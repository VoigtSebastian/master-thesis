import os

import structlog
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from openai import OpenAI

#
# Provides model_setup that handles the LLM and embedding-model setup
#

log = structlog.get_logger(emitter="models")


def model_setup() -> dict[str, BaseChatModel]:
    """Provide handlers to available models"""

    models: dict[str, BaseChatModel] = {}

    # Setting up open-AI model
    model_name = os.environ.get("MODEL_NAME")
    root_url = os.environ.get("ROOT_URL")
    model_path = f"openai/{model_name}"

    if not model_name:
        raise BaseException("Missing MODEL_NAME")
    if not root_url:
        raise BaseException("Missing ROOT_URL")
    log.info(
        "initializing model",
        model_name=model_name,
        root_url=root_url,
        key=model_path,
    )
    models[model_path] = ChatOpenAI(
        model=model_name,
        temperature=0.1,
        max_tokens=1500,  # per request
        timeout=60.0,  # seconds
        max_retries=2,
        base_url=root_url,
        streaming=True,
    )
    models["default/llm"] = models[model_path]
    log.info("setting default model", key=model_path)

    # Setup the embedding model

    default_embedding = os.environ.get("EMBEDDING_NAME")
    if not default_embedding:
        raise BaseException("Missing EMBEDDING_NAME")

    log.info(
        "initializing embedding model",
        model_name=default_embedding,
        root_url=root_url,
        key=model_path,
    )
    open_ai = OpenAI(base_url=root_url)

    def embed(text: str) -> list[float]:
        return (
            open_ai.embeddings.create(
                input=text,
                model=default_embedding,
            )
            .data[0]
            .embedding
        )

    # This not nice, but langchain_openai.OpenAIEmbedding is broken ...
    models["default/embed"] = embed

    return models
