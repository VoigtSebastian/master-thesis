import asyncio
import re

import structlog
from jinja2 import Template
from langchain.evaluation.embedding_distance import EmbeddingDistanceEvalChain
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from prompts.rocket import ChannelSelection, RegexSearch, SummarizeChat
from rocket.tool import rocket_chat_search
from shared.configuration import ConfigSchema
from shared.state import GraphState, RocketChatState
from util.agent_functions import dispatch_log, run_llm, unpack_node
from util.rocket_client import ChatRoom, RocketChatClient, RocketChatMessage
from util.embedding import embedding_distance

# General agent information:
# There are two main nodes (thinking and action) that the state oscillates between.
# - thinking: Plans a new query to be executed by generating thinking-traces
# - action: Executes the generated query and handles observation (information that should be stored)
#
# The END state is reached if the conditional edge is_done decides that enough information was retrieved

log = structlog.get_logger(emitter="rocket_graph")


async def update_channels(rs: RocketChatState, pattern: str):
    """Limit the number of channels that are searched by the agent using a generated pattern."""
    channel_pattern = re.compile(pattern, re.IGNORECASE)

    channels = [r for r in rs["chat_rooms"] if r.room_type == "c"]
    dm = [r for r in rs["chat_rooms"] if r.room_type == "d"]

    channels = [c for c in channels if channel_pattern.match(c.name)]
    dm = [d for d in dm if any([channel_pattern.match(u) for u in d.usernames])]

    if len(channels) + len(dm) > 0:
        rs["chat_rooms"] = channels + dm
        log.info(
            "reduces searched channels",
            n=len(rs["chat_rooms"]),
            rooms=rs["chat_rooms"],
        )
    else:
        log.info("pattern did not result in matches")


@unpack_node(
    "constructing search pattern",
    {
        "channel_selection": "rocket/channel_selection.j2",
        "regex_search": "rocket/regex_search.j2",
    },
)
async def build_search_pattern(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    templates: dict[str, Template],
    rc: RocketChatClient,
    rs: RocketChatState,
    question: str,
):
    """Thinking state, initializes state if not already done and then continues to create search patterns."""

    # If not initialized - initialize the group/dm list
    if not rs["chat_rooms"]:
        rs["chat_rooms"] = await rc.retrieve_all_rooms()
        log.info("initialized chat rooms", n=len(rs["chat_rooms"]))

        channel_selection: ChannelSelection = await run_llm(
            llm,
            templates["channel_selection"],
            {"user_request": question},
            ChannelSelection,
        )

        if not channel_selection.regular_expression:
            log.info("no pattern created, skipping")
        else:
            log.info(
                "created channel selection pattern",
                pattern=channel_selection.regular_expression,
                identifiers=channel_selection.extracted_identifiers,
            )
            await update_channels(rs, channel_selection.regular_expression)

    # Create new regex search pattern
    regex_search: RegexSearch = await run_llm(
        llm,
        templates["regex_search"],
        {"queries": rs["search_patterns"], "user_request": question},
        RegexSearch,
    )
    rs["search_patterns"].append(regex_search.keywords)

    await dispatch_log(
        log,
        "Searching Rocket.Chat",
        {
            "pattern": regex_search.keywords,
            "identifiers": regex_search.observations,
        },
    )

    return state


async def summarize_chat(llm, template, template_variables, room):
    summary = await run_llm(
        llm,
        template,
        template_variables,
        SummarizeChat,
    )
    return room, summary


async def rank_chat(
    chat_room: ChatRoom,
    messages: list[RocketChatMessage | list[RocketChatMessage]],
    question_embedding: list[float],
    embedding_chain: EmbeddingDistanceEvalChain,
    embedding_model,
) -> tuple[
    float,
    ChatRoom,
    list[RocketChatMessage | list[RocketChatMessage]],
]:
    single_messages = [m.message for m in messages if type(m) is not list]
    threads = [t for t in messages if type(t) is list]
    threads = [m.message for t in threads for m in t]
    text = ";".join(single_messages + threads)

    d = embedding_distance(
        text,
        embedding_model,
        embedding_chain,
        question_embedding,
    )
    return (d, chat_room, messages)


@unpack_node(
    "searching rocket chat",
    {"summarize_chat": "rocket/summarize_chat.j2"},
)
async def search(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    embedding_model,
    templates: dict[str, Template],
    configurable: ConfigSchema,
    rc: RocketChatClient,
    question: str,
):
    """Action state, executed the latest CQL query and stores the results in the graph's state."""
    question_embedding: list[float] = configurable["question_embedding"]
    embedding_chain: EmbeddingDistanceEvalChain = configurable["embedding_chain"]

    try:
        if search_results := await rocket_chat_search(state, config):
            # Rank chats using an embedding model
            ranked_results = [
                rank_chat(
                    r[0],
                    r[1],
                    question_embedding,
                    embedding_chain,
                    embedding_model,
                )
                for r in search_results
            ]
            ranked_results = await asyncio.gather(*ranked_results)
            ranked_results = sorted(ranked_results, key=lambda x: x[0])
            # Select the top 5 chats
            ranked_results = ranked_results[:3]
            ranked_results = [(s[1], s[2]) for s in ranked_results]

            log.info(
                "ranked results",
                chats_before=len(search_results),
                chats_after=len(ranked_results),
            )

            # Summarize the top 3 chats
            summaries = [
                summarize_chat(
                    llm,
                    templates["summarize_chat"],
                    {
                        "chat_base_url": rc.base_url,
                        "room": room,
                        "messages": messages,
                        "user_request": question,
                    },
                    room,
                )
                for room, messages in ranked_results
            ]
            summaries: list[tuple[ChatRoom, SummarizeChat]] = await asyncio.gather(
                *summaries
            )
            summaries = [(s[0], s[1].summary) for s in summaries if s[1].summary]
            state["rocket_chat_state"]["results"].extend(summaries)
        else:
            log.warn("could not retrieve data", user_request=question)
    except:
        log.exception("error querying rocket chat", user_request=question)
    return state


rocket_graph_builder = StateGraph(GraphState)
rocket_graph_builder.add_node(build_search_pattern)
rocket_graph_builder.add_node(search)

rocket_graph_builder.add_edge(START, "build_search_pattern")
rocket_graph_builder.add_edge("build_search_pattern", "search")
rocket_graph_builder.add_edge("search", END)

rocket_graph = rocket_graph_builder.compile(checkpointer=MemorySaver())
