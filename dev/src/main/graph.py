import structlog
from confluence import confluence_graph
from jinja2 import Template
from langchain_core.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from prompts.main import ToolChoice, Tools, Validation
from rocket import rocket_graph
from shared.main_output import ErrorOutput, SuccessOutput
from shared.state import ConfluenceState, GraphState, RocketChatState
from util.agent_functions import dispatch_log, run_llm, unpack_node
from util.llm_operations import is_hallucination

# General agent information:
# There are two main nodes (thinking and action) that the state oscillates between.
# - thinking: Plans a new query to be executed by generating thinking-traces
# - action: Executes the generated query and handles observation (information that should be stored)

MAX_ITERATIONS = 2

log = structlog.get_logger(emitter="main_graph")


@unpack_node("starting verification process", {"validation": "main/validation.j2"})
async def verification(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    question: str,
    templates: dict[str, Template],
):
    """Initial state, verifies the user input and determines if we continue to the rest of the graph or return."""
    output: Validation = await run_llm(
        llm,
        templates["validation"],
        {"user_question": question},
        Validation,
    )
    await dispatch_log(
        log,
        "Verifying Input",
        {"passed": output.passed, "thoughts": output.observations},
    )

    if not output.passed:
        state.update(initial_check_failed=output.observations)
    return state


@unpack_node("starting aggregation process", {"aggregate": "main/aggregate.j2"})
async def aggregator(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    cs: ConfluenceState,
    question: str,
    templates: dict[str, Template],
):
    """Generate reply to the user, given the retrieved information or failure to do so."""
    await dispatch_log(
        log,
        "Summarizing Information",
        {"answering": question},
    )

    pages = [page for pages in cs["confluence_pages"] for page in pages]
    prompt = templates["aggregate"].render(
        user_question=question,
        documents=pages,
        replies=[],
        chat_messages=state["rocket_chat_state"]["results"],
    )
    output = await llm.ainvoke([SystemMessage(prompt)])

    state.update(final_response=SuccessOutput(message=output.content))
    return state


@unpack_node(
    "generating final response", {"validation_failed": "main/validation_failed.j2"}
)
async def final_validation(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    cs: ConfluenceState,
    question: str,
    templates: dict[str, Template],
):
    """Final state, generate a reply to the user, given the retrieved information or failure to do so."""
    # initial_check_failed is set to the list of thoughts that the verification
    # process returns if it fails. We use this list to reply to the user.
    if thoughts := state["initial_check_failed"]:
        output: ErrorOutput = await run_llm(
            llm,
            templates["validation_failed"],
            {"thoughts": thoughts, "user_question": question},
            ErrorOutput,
        )
        state.update(final_response=output)

    match state["final_response"]:
        case None:
            log.warn("fatal error occurred - no final response set", query=question)
            state.update(final_response=ErrorOutput(message="A fatal error occurred"))
        case SuccessOutput(message=message):
            # Check for hallucinations
            documents = [d.body for pages in cs["confluence_pages"] for d in pages]
            documents.extend(state["rocket_chat_state"]["results"])

            hallucination = await is_hallucination(
                documents, message, config, leniency=True
            )
            if hallucination.hallucination:
                log.warn(
                    "hallucination occurred",
                    observations=hallucination.observations,
                )
                message = f"{message}\n\n\n### Check\n\n{hallucination.observations}\n"
                state.update(final_response=ErrorOutput(message=message))
            else:
                log.info(f"hallucination check passed")

        case ErrorOutput(message=message):
            log.info("graph unsuccessful - returning to user", message=message)

    return state


@unpack_node("starting decision process", {"tool_choice": "main/tool_choice.j2"})
async def main_loop(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    cs: ConfluenceState,
    question: str,
    templates: dict[str, Template],
    rs: RocketChatState,
):
    """Main Loop - executes"""
    # determine and set operations
    state["iterations"] += 1

    pages = [page for pages in cs["confluence_pages"] for page in pages]
    output: ToolChoice = await run_llm(
        llm,
        templates["tool_choice"],
        {
            "user_question": question,
            "confluence_pages": pages,
            "chat_summaries": rs["results"],
            "confluence_iterations": len(cs["confluence_pages"]),
            "rocket_iterations": len(rs["search_patterns"]),
            "rocket_patterns": rs["search_patterns"],
            "cql_queries": cs["cql_queries"],
        },
        ToolChoice,
    )
    log.info("tool choice generated", tool=output.tool)
    state["operations"].append(output.tool)

    return state


async def main_loop_edge(state: GraphState):
    if state["iterations"] > MAX_ITERATIONS:
        log.info("max iterations reached", iterations=state["iterations"])
        return "aggregator"

    operations = state["operations"]
    next_operations = operations[-1]

    # If no tool was selected - we are done and compose a summary
    if not next_operations:
        log.info("done")
        return ["aggregator"]

    # If there was a tool choice, we map them to the appropriate node
    next_nodes = []
    for tool in next_operations:
        match tool:
            case Tools.CONFLUENCE:
                log.info("add next operation", next_operation="confluence_graph")
                next_nodes.append("confluence_graph")
            case Tools.ROCKET_CHAT:
                log.info("add next operation", next_operation="rocket_graph")
                next_nodes.append("rocket_graph")

    return next_nodes


async def verification_failed(state: GraphState):
    if state["initial_check_failed"]:
        return "final_validation"
    return "main_loop"


main_graph_builder = StateGraph(GraphState)
main_graph_builder.add_node(verification)  # Verify input
main_graph_builder.add_node("confluence_graph", confluence_graph)  # TOOLS
main_graph_builder.add_node("rocket_graph", rocket_graph)  # TOOLS
main_graph_builder.add_node("aggregator", aggregator)  # Build final reply
main_graph_builder.add_node("final_validation", final_validation)  # Validate output
main_graph_builder.add_node("main_loop", main_loop)  # Main loop

# Agent entry point
main_graph_builder.add_edge(START, "verification")

# Conditional edges
# Decide whether we continue to the main_loop or stop
main_graph_builder.add_conditional_edges("verification", verification_failed)
# Decide what tool should be executed
node_options = ["aggregator", "confluence_graph", "rocket_graph"]
main_graph_builder.add_conditional_edges("main_loop", main_loop_edge, node_options)
# Execute main_loop after executing tool
main_graph_builder.add_edge("confluence_graph", "main_loop")
main_graph_builder.add_edge("rocket_graph", "main_loop")

# Final steps
main_graph_builder.add_edge("aggregator", "final_validation")
main_graph_builder.add_edge("final_validation", END)

main_graph = main_graph_builder.compile(checkpointer=MemorySaver())
