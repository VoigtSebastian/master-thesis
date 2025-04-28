import asyncio
from dataclasses import dataclass
from os import environ
from typing import Callable, List, TypeVar

import structlog
from httpx import AsyncClient

T = TypeVar("T")

log = structlog.get_logger(emitter="rocket_client")


@dataclass
class ChatRoom:
    """
    Represents a chat room with the following attributes:

    :param room_id: A unique identifier for the chat room.
    :param room_type: The type of the chat room (c for channels and d for dms).
    :param usernames: List of the usernames that are part of a dm chat room
    :param name: An optional name of the chat room (dms typically have no name or description).
    :param description: An optional description of the chat room.
    """

    room_id: str
    room_type: str
    usernames: list[str] | None
    name: str | None
    description: str | None
    url: str

    @staticmethod
    def from_api_result(base_url: str, chat_identifier: str):
        def builder(result: list[dict]):
            return [
                ChatRoom(
                    room_id=c["_id"],
                    room_type=c["t"],
                    usernames=c.get("uids"),
                    name=c.get("name"),
                    description=c.get("description"),
                    url=ChatRoom.room_url(base_url, c),
                )
                for c in result[chat_identifier]
            ]

        return builder

    @staticmethod
    def room_url(base_url: str, c: dict):
        t = "channel" if c["t"] == "c" else "direct"
        return f"{base_url}/{t}/{c["_id"]}"


@dataclass
class RocketChatMessage:
    """
    Represents a message in a RocketChat room with the following attributes:

    :param message: The content of the message.
    :param message_id: A unique identifier for the message.
    :param thread_id: An optional identifier for the thread to which the message belongs.
    :param score: An optional score associated with the message (if it was searched for using the API).
    :param username: The username of the user who sent the message.
    :param user_id: A unique identifier for the user who sent the message.
    :param timestamp: The ISO timestamp of the message.
    """

    message: str
    message_id: str
    thread_id: str | None
    score: float | None
    username: str
    user_id: str
    timestamp: str

    @staticmethod
    def from_chat_search(result: dict):
        return [
            RocketChatMessage(
                message=r["msg"],
                message_id=r["_id"],
                thread_id=r.get("tmid"),
                score=r.get("score"),
                username=r["u"]["name"],
                user_id=r["u"]["_id"],
                timestamp=r["ts"],
            )
            for r in result["messages"]
        ]

    @staticmethod
    def from_threaded_result(result: dict):
        return [
            RocketChatMessage(
                message=r["msg"],
                message_id=r["_id"],
                thread_id=r["tmid"],
                score=None,
                username=r["u"]["name"],
                user_id=r["u"]["_id"],
                timestamp=r["ts"],
            )
            for r in result["messages"]
        ]


class RocketChatClient:
    def __init__(
        self,
        token: str,
        user_id: str,
        max_items_limit: int = 100,
        step_size: int = 50,
    ):
        headers = {
            "Accept": "application/json",
            "X-Auth-Token": token,
            "X-User-Id": user_id,
        }
        self.client = AsyncClient(headers=headers, timeout=30)

        self.base_url = environ["ROCKET_CHAT_URL"]
        self.max_items_limit = max_items_limit
        self.step_size = step_size

    async def search_text(
        self,
        pattern: str,
        chats: list[ChatRoom],
    ) -> list[tuple[ChatRoom, list[RocketChatMessage | list[RocketChatMessage]]]]:
        results = [self.search_room(pattern, c) for c in chats]
        results = await asyncio.gather(*results)
        return [r for r in results if r[1]]

    async def search_room(
        self,
        pattern: str,
        chat: ChatRoom,
    ) -> tuple[ChatRoom, list[RocketChatMessage | list[RocketChatMessage]]]:
        result = await self.api_chat_search(chat.room_id, pattern)
        expanded_messages: list[RocketChatMessage | list[RocketChatMessage]] = []
        seen_thread_ids = set()

        for message in result:
            if message.thread_id and message.thread_id not in seen_thread_ids:
                # Retrieve the full thread
                thread_messages = await self.api_get_threaded_messages(
                    message.thread_id
                )
                expanded_messages.append(thread_messages)
                seen_thread_ids.add(message.thread_id)
            elif message.thread_id and message.thread_id in seen_thread_ids:
                # Skip this message as it's part of a thread that has already been expanded
                continue
            else:
                # This message is not part of a thread, add it as is
                expanded_messages.append(message)

        return chat, expanded_messages

    async def retrieve_all_rooms(self) -> list[ChatRoom]:
        try:
            channels = await self.api_channels_list_joined()
            dms = await self.api_list_dms()

            user_names = [
                [self.api_get_user_names(u_id) for u_id in dm.usernames] for dm in dms
            ]
            user_names = await asyncio.gather(*[asyncio.gather(*u) for u in user_names])
            for dm, user_names in zip(dms, user_names):
                dm.usernames = user_names

            return channels + dms
        except:
            log.exception("could not retrieve channels")
            return []

    async def api_get_user_names(self, user_id: str) -> str:
        url = f"{self.base_url}/api/v1/users.info"
        params = {"userId": user_id}

        response = await self.client.get(url=url, params=params)
        response.raise_for_status()

        response = response.json()
        assert response["success"]

        return response["user"]["name"]

    async def api_list_dms(self) -> list[ChatRoom]:
        """https://developer.rocket.chat/apidocs/list-dms"""
        url = f"{self.base_url}/api/v1/im.list"
        params = {}

        return await self.retrieve_all_items(
            url, params, ChatRoom.from_api_result(self.base_url, "ims")
        )

    async def api_channels_list_joined(self) -> list[ChatRoom]:
        """https://developer.rocket.chat/apidocs/get-list-of-joined-channels"""
        url = f"{self.base_url}/api/v1/channels.list.joined"
        params = {}

        return await self.retrieve_all_items(
            url, params, ChatRoom.from_api_result(self.base_url, "channels")
        )

    async def api_chat_search(
        self,
        chat_id: str,
        pattern: str,
        count: int = 50,
    ) -> list[RocketChatMessage]:
        """https://developer.rocket.chat/apidocs/search-message"""
        url = f"{self.base_url}/api/v1/chat.search"
        params = {"roomId": chat_id, "searchText": pattern, "count": count}

        response = await self.client.get(url=url, params=params)
        response.raise_for_status()
        response = response.json()
        assert response["success"]

        return RocketChatMessage.from_chat_search(response)

    async def api_get_threaded_messages(
        self, thread_id: str
    ) -> list[RocketChatMessage]:
        """https://developer.rocket.chat/apidocs/get-thread-messages"""
        url = f"{self.base_url}/api/v1/chat.getThreadMessages"
        params = {"tmid": thread_id}

        return await self.retrieve_all_items(
            url,
            params,
            RocketChatMessage.from_threaded_result,
        )

    async def retrieve_all_items(
        self,
        url: str,
        params: dict,
        constructor: Callable[[dict], T],
        max_messages: int = 50,
    ) -> List[T]:
        """Helper method that runs API with offset"""
        params.setdefault("offset", 0)
        params["count"] = self.step_size
        all_items: List[T] = []

        i = 0

        while i < max_messages:
            response = await self.client.get(url=url, params=params)
            response.raise_for_status()
            response = response.json()
            assert response["success"]

            all_items.extend(constructor(response))
            params["offset"] += self.step_size

            if response.get("count", 0) < self.step_size:
                break

            i += self.step_size

        return all_items
