import asyncio

import structlog
from langchain.evaluation.embedding_distance import EmbeddingDistanceEvalChain
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from prompts.confluence.page_summary import PageSummary
from shared.configuration import ConfigSchema
from util.agent_functions import run_llm
from util.ConfluenceClient import ConfluenceClient, Page, QueryResult
from util.embedding import embedding_distance
from util.llm_operations import is_hallucination

#
# Contains confluence_query, a tool to execute CQL queries
#

log = structlog.get_logger(emitter="confluence_tool")


async def download_embed_page(
    client: ConfluenceClient,
    query_result: QueryResult,
    embedding_model,
    embedding_chain: EmbeddingDistanceEvalChain,
    question_embedding: list[float],
) -> tuple[float, Page] | None:
    """Download a page and calculate the distance of its embedding to the questions embedding"""

    # Download page
    page = await client.get_page(query_result=query_result)
    if not page or not page.body:
        log.warn("could not download page", title=query_result.title)
        return None
    log.info("retrieved page", title=page.title, web_url=page.web_ui)

    min_distance = embedding_distance(
        page.body,
        embedding_model,
        embedding_chain,
        question_embedding,
    )

    return (min_distance, page)


async def summarize_page(
    page: Page, question: str, llm: BaseChatModel, config: RunnableConfig
) -> Page | None:
    """Use the page_summary prompt template to summarize a page"""
    configurable: ConfigSchema = config["configurable"]
    prompt = configurable["template_environment"].get_template(
        "confluence/page_summary.j2"
    )
    response: PageSummary = await run_llm(
        llm,
        prompt,
        {
            "confluence_page": str(page.body),
            "user_question": question,
        },
        PageSummary,
    )

    if not response.summary:
        return None

    body = response.summary

    hallucination = await is_hallucination(page.body.replace("\n", " "), body, config)
    if hallucination.hallucination:
        log.warn(
            "hallucination detected",
            page=page.title,
            claim=body,
            observations=hallucination.observations,
        )
        return None

    log.info(
        "shortened page",
        title=page.title,
        web_url=page.web_ui,
        original_length=len(page.body),
        shortened_length=len(body),
    )

    page.body = body
    return page


# @tool(parse_docstring=True)
async def confluence_query(query: str, config: RunnableConfig) -> list[Page]:
    """Execute a Confluence Query Language (CQL) query, retrieving the relevant Confluence pages to this query.

    Args:
        query: str containing valid query in Confluence Query Language (CQL)

    Returns:
        page_info (list): [Page(title, body, web_ui)]
    """
    log.info("running query", query=query)

    # Setup
    configurable: ConfigSchema = config["configurable"]
    client: ConfluenceClient = configurable["__confluence_client"]
    question = configurable["user_question"]

    log.info("embedding question", query=query)
    embedding_model = configurable["models"]["default/embed"]
    question_embedding: list[float] = configurable["question_embedding"]
    embedding_chain: EmbeddingDistanceEvalChain = configurable["embedding_chain"]

    log.info("downloading pages", query=query)
    query_results = await client.cql_all(query)
    log.info("ranking pages", query=query, nr_documents=len(query_results))
    ranked_pages = [
        download_embed_page(
            client=client,
            query_result=result,
            embedding_model=embedding_model,
            embedding_chain=embedding_chain,
            question_embedding=question_embedding,
        )
        for result in query_results
    ]
    ranked_pages = await asyncio.gather(*ranked_pages)
    ranked_pages = [p for p in ranked_pages if p]
    ranked_pages = sorted(ranked_pages, key=lambda x: x[0])

    log.info("ranked pages", pages=[r[1].title for r in ranked_pages])
    ranked_pages = ranked_pages[:8]

    log.info("summarizing pages", query=query, nr_documents=len(ranked_pages))
    pages = await asyncio.gather(
        *[
            summarize_page(
                page=page,
                question=question,
                llm=configurable["models"]["default/llm"],
                config=config,
            )
            for _, page in ranked_pages
        ]
    )
    return [p for p in pages if p]


tool_node = ToolNode([confluence_query])


def wrap_model_with_query_tool(model: BaseChatModel):
    return model.bind_tools([confluence_query])
