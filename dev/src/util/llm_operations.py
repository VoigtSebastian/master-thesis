import structlog
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from shared.configuration import ConfigSchema
from prompts.general import Hallucination

log = structlog.get_logger(emitter="llm_operations")


async def is_hallucination(
    document: str, claim: str, config: RunnableConfig, leniency: bool = False
) -> Hallucination:
    configurable: ConfigSchema = config["configurable"]
    llm = configurable["models"]["default/llm"]
    template_environment = configurable["template_environment"]

    prompt = template_environment.get_template("general/is_hallucination.j2")
    prompt = prompt.render(
        {
            "document": document,
            "claim": claim,
            "leniency": leniency,
        }
    )

    response: Hallucination = await llm.with_structured_output(Hallucination).ainvoke(
        [SystemMessage(content=prompt)]
    )
    log.info("hallucination check", content=response.hallucination)

    return response
