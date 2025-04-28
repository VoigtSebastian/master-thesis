from langchain.evaluation.embedding_distance import EmbeddingDistanceEvalChain
from os import environ
import numpy as np
import structlog

log = structlog.get_logger(emitter="embedding")


def embedding_distance(
    text: str,
    embedding_model,
    embedding_chain: EmbeddingDistanceEvalChain,
    question_embedding: list[float],
) -> float:
    """Chunk a text, embed each chunk and the return the closest distance to question_embedding"""

    # Split page into chunks
    # We assume that a token is generated for about every 2 characters (very conservative)
    chunk_size = int(environ["MAX_EMBEDDING_CHARACTERS"])
    chunk_overlap = int(chunk_size / 8)

    texts = [
        text[s : s + chunk_size]
        for s in range(0, len(text), chunk_size - chunk_overlap)
    ]
    log.info("text lengths", t=[len(t) for t in texts])

    # Embed each page and calculate embedding distances
    embeddings: list[list[float]] = [
        embedding_model(f"""passage: {t}""") for t in texts
    ]
    distances: list[float] = [
        embedding_chain._compute_score(np.array([question_embedding, e]))
        for e in embeddings
    ]
    # We use the min distance
    min_distance = min(distances)

    return min_distance
