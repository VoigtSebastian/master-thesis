import structlog
from langchain_core.runnables.config import RunnableConfig
from shared.configuration import ConfigSchema
from shared.state import RocketChatState
from util.rocket_client import ChatRoom, RocketChatMessage

log = structlog.get_logger(emitter="rocket_tool")


async def rocket_chat_search(
    state: RocketChatState, config: RunnableConfig
) -> None | list[tuple[ChatRoom, list[RocketChatMessage | list[RocketChatMessage]]]]:
    """Returns list of chat messages (or list of list for threaded messages) for a given set of channels and a search pattern."""
    configurable: ConfigSchema = config["configurable"]
    user_request = configurable["user_question"]

    rc = configurable["__rocket_client"]
    rs: RocketChatState = state["rocket_chat_state"]

    terms = rs["search_patterns"][-1]
    executed = [x for xs in rs["search_patterns"][:-1] for x in xs]
    new_terms = [t for t in terms if t not in executed]

    if len(terms) > len(new_terms):
        log.info(
            "reduced keyword length",
            terms=terms,
            new_terms=new_terms,
            executed=executed,
        )

    if not new_terms:
        log.warn("no keywords generated", search_pattern=rs["search_patterns"])
        return None

    search_pattern = "/(" + "|".join(new_terms) + ")/i"
    log.info("generated search pattern", search_pattern=search_pattern)

    try:
        chat_results = await rc.search_text(
            pattern=search_pattern, chats=rs["chat_rooms"]
        )
        log.info("search done", results=chat_results)

        return chat_results
    except:
        log.exception(
            "exception occurred executing search",
            regular_expression=search_pattern,
            user_request=user_request,
        )

    return None
