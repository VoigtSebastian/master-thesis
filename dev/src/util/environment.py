from getpass import getpass
from os import environ
import structlog
from dotenv import load_dotenv
from util.log_format import setup_global_logging
from shared.configuration import initialize_configuration
from shared.state import GraphState


def setup_config_state(query: str | None = None) -> tuple[dict, dict]:
    setup_global_logging()
    log = structlog.get_logger(emitter="setup")
    load_dotenv(override=True)

    confluence_token = environ.get("CONFLUENCE_API_KEY")
    if not confluence_token:
        confluence_token = getpass("Confluence token: ")

    rocket_token = environ.get("ROCKET_CHAT_TOKEN")
    if not rocket_token:
        rocket_token = getpass("Rocket token: ")

    rocket_id = environ.get("ROCKET_CHAT_ID")
    if not rocket_id:
        rocket_id = getpass("Rocket Chat ID: ")

    query: str = environ.get("QUERY") if not query else query
    if not query:
        query = input("Query: ")
    log.info("set user query", query=query)

    # https://python.langchain.com/docs/how_to/runnable_runtime_secrets/
    config = {
        "configurable": initialize_configuration(
            confluence_token=confluence_token,
            user_question=query,
            rocket_token=rocket_token,
            rocket_id=rocket_id,
        )
    }

    state = GraphState.initialize()

    return (config, state)
