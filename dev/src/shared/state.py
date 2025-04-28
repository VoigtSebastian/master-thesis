from typing import Annotated, Optional, TypedDict

from prompts.main import Tools
from shared.main_output import ErrorOutput, SuccessOutput
from util.ConfluenceClient import Page
from util.rocket_client import ChatRoom


def confluence_reducer(a, b):
    pass


def list_reducer(a, b):
    # Return an empty list if neither list is defined
    if not a and not b:
        return a
    # If one list is empty/None and the other is not, return the other
    if not a and b:
        return b
    if a and not b:
        return a
    # Return the larger list
    if len(a) > len(b):
        return a
    return b


def none_reducer(a, b):
    # Optional fields may contain None and the standard reducer cannot handle that
    return b if b is not None else a


def larger_reducer(a, b):
    # When merging states, blindly adding numbers (e.g. counters) is not a good idea, we pick the larger one
    return a if a > b else b


class RocketChatState(TypedDict):
    """
    :param chat_rooms: A list of chat rooms that are searched
    :param search_patterns: A list of keywords
    :param results: A list of summaries and the URLs that created them
    """

    chat_rooms: Annotated[list[ChatRoom], list_reducer]
    search_patterns: Annotated[list[list[str]], list_reducer]
    results: Annotated[list[(ChatRoom, str)], list_reducer]

    @classmethod
    def initialize(cls):
        return RocketChatState(chat_rooms=[], search_patterns=[], results=[])


def rocket_reducer(a: RocketChatState, b: RocketChatState):
    if a and not b:
        return a
    if b and not a:
        return b
    return RocketChatState(
        chat_rooms=list_reducer(a["chat_rooms"], b["chat_rooms"]),
        search_patterns=list_reducer(a["search_patterns"], b["search_patterns"]),
        results=list_reducer(a["results"], b["results"]),
    )


class ConfluenceState(TypedDict):
    """
    :param cql_queries: A list of keywords, that were generated for each query
    :param confluence_pages: A list of pages that were retrieved for each query
    """

    cql_queries: Annotated[list[list[str]], list_reducer]
    confluence_pages: Annotated[list[list[Page]], list_reducer]

    @classmethod
    def initialize(cls):
        return ConfluenceState(cql_queries=[], confluence_pages=[])


def confluence_reducer(a: ConfluenceState, b: ConfluenceState):
    if a and not b:
        return a
    if b and not a:
        return b
    return ConfluenceState(
        cql_queries=list_reducer(a["cql_queries"], b["cql_queries"]),
        confluence_pages=list_reducer(a["confluence_pages"], b["confluence_pages"]),
    )


class GraphState(TypedDict):
    iterations: Annotated[int, larger_reducer]
    initial_check_failed: Annotated[str, none_reducer]
    final_response: Annotated[Optional[ErrorOutput | SuccessOutput], none_reducer]
    operations: Annotated[list[list[Tools]], larger_reducer]
    rocket_chat_state: Annotated[RocketChatState, rocket_reducer]
    confluence_state: Annotated[ConfluenceState, confluence_reducer]

    @classmethod
    def initialize(cls):
        return GraphState(
            cql_queries=[],
            confluence_pages=[],
            iterations=0,
            initial_check_failed=None,
            final_response=None,
            operations=[],
            rocket_chat_state=RocketChatState.initialize(),
            confluence_state=ConfluenceState.initialize(),
        )
