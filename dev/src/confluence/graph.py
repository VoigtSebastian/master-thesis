import structlog
from confluence.tool import confluence_query
from jinja2 import Template
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from prompts.confluence import QueryBuilderOutput
from shared.state import ConfluenceState, GraphState
from util.agent_functions import dispatch_log, run_llm, unpack_node

# General agent information:
# There are two main nodes (thinking and action) that the state oscillates between.
# - thinking: Plans a new query to be executed by generating thinking-traces
# - action: Executes the generated query and handles observation (information that should be stored)
#
# The END state is reached if the conditional edge is_done decides that enough information was retrieved

log = structlog.get_logger(emitter="confluence_graph")


@unpack_node("constructing query", {"cql_prompt": "confluence/cql_prompt.j2"})
async def build_query(
    state: GraphState,
    config: RunnableConfig,
    llm: ChatOpenAI,
    cs: ConfluenceState,
    question: str,
    templates: dict[str, Template],
):
    """Thinking state, created a new CQL query from previously retrieved information."""
    log.info("starting thinking process")

    output: QueryBuilderOutput = await run_llm(
        llm,
        templates["cql_prompt"],
        {"queries": cs["cql_queries"], "user_question": question},
        QueryBuilderOutput,
    )

    # add new cql query to state and dispatch event (displayed in the frontend)
    cs["cql_queries"].append(output.keywords)
    await dispatch_log(
        log,
        "Searching Confluence",
        {"query": output.keywords, "observations": output.observations},
    )

    return state


@unpack_node("executing cql", {})
async def execute_cql(state: GraphState, config: RunnableConfig, cs: ConfluenceState):
    """Action state, executed the latest CQL query and stores the results in the graph's state."""
    terms = cs["cql_queries"][-1]
    queries = [x for xs in cs["cql_queries"][:-1] for x in xs]
    new_terms = [t for t in terms if t not in queries]

    if len(terms) > len(new_terms):
        log.info("reduces keyword length", terms=terms, new_terms=new_terms)
    if not new_terms:
        log.info("no new keywords generated", cql=terms)
        return state

    # construct CQL query
    cql: str = "OR ".join([f"""text ~ "{t}" OR title ~ "{t}" """ for t in new_terms])
    log.info("constructed new cql query", cql=cql)

    # Execute CQL query, log and store outcome
    try:
        pages = await confluence_query(cql, config)
        cs["confluence_pages"].append(pages)

        log.info("successfully executed cql", cql=terms)
    except:
        log.exception("exception occurred calling CQL tool")
        return state

    return state


confluence_graph_builder = StateGraph(GraphState)
confluence_graph_builder.add_node(build_query)
confluence_graph_builder.add_node(execute_cql)

confluence_graph_builder.add_edge(START, "build_query")
confluence_graph_builder.add_edge("build_query", "execute_cql")
confluence_graph_builder.add_edge("execute_cql", END)

confluence_graph = confluence_graph_builder.compile(checkpointer=MemorySaver())
