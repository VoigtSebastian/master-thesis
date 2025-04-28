from datetime import datetime, timezone
from os import environ
from typing import TypedDict
from uuid import uuid1

import structlog
from jinja2 import Environment, FileSystemLoader
from langchain.evaluation import EmbeddingDistance
from langchain.evaluation.embedding_distance import EmbeddingDistanceEvalChain
from langchain_core.language_models.chat_models import BaseChatModel
from shared.models import model_setup
from util.ConfluenceClient import ConfluenceClient
from util.rocket_client import RocketChatClient

#
# Contains global runtime configuration
#

log = structlog.get_logger(emitter="configuration")


class ConfigSchema(TypedDict):
    """Runtime configuration for graphs.
    Contains LLMs/embedding-models, API clients, the user's query and a thread_id.
    """

    models: dict[str, BaseChatModel]
    __confluence_client: ConfluenceClient
    user_question: str
    thread_id: str
    template_environment: Environment
    question_embedding: list[float]
    embedding_chain: EmbeddingDistanceEvalChain
    __rocket_client: RocketChatClient


def initialize_configuration(
    confluence_token: str,
    user_question: str,
    rocket_token: str,
    rocket_id: str,
) -> ConfigSchema:
    environment = Environment(
        loader=FileSystemLoader("src/prompts/"),
        keep_trailing_newline=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    now = datetime.now(timezone.utc)
    environment.globals["now"] = now.strftime(r"%Y-%m-%d, %H:%M")
    if personality := environ.get("AGENT_PERSONALITY"):
        environment.globals["agent_personality"] = personality
        log.info(
            "set personality from environment",
            personality=environment.globals["agent_personality"],
        )
    else:
        environment.globals["agent_personality"] = "a helpful researcher"
        log.info(
            "set default personality",
            personality=environment.globals["agent_personality"],
        )

    models = model_setup()

    embedding_model = models["default/embed"]
    question_embedding: list[float] = embedding_model(f"query: {user_question}")
    embedding_chain = EmbeddingDistanceEvalChain(
        distance_metric=EmbeddingDistance.COSINE
    )

    return {
        "models": models,
        "__confluence_client": ConfluenceClient(confluence_token),
        "user_question": user_question,
        "thread_id": uuid1(),
        "question_embedding": question_embedding,
        "embedding_chain": embedding_chain,
        "template_environment": environment,
        "__rocket_client": RocketChatClient(rocket_token, rocket_id),
    }
