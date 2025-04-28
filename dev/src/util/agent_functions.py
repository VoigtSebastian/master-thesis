import functools

from openai import LengthFinishReasonError
import structlog
from jinja2 import Environment, Template
from langchain_openai import ChatOpenAI
from shared.configuration import ConfigSchema
from langchain_core.callbacks.manager import adispatch_custom_event
import inspect
from langchain_core.messages import HumanMessage, SystemMessage

log = structlog.get_logger(emitter="agent_functions")


def unpack_node(log_message: str, template_paths: dict[str, str]):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state, config, *args, **kwargs):
            # Log the message
            log.info(log_message)

            # Extract important configuration variables
            configurable: ConfigSchema = config["configurable"]
            template_environment: Environment = configurable["template_environment"]

            # Load used prompts
            templates = {}
            for key, path in template_paths.items():
                templates[key] = template_environment.get_template(path)

            extracted = {
                "configurable": configurable,
                "llm": configurable["models"]["default/llm"],
                "embedding_model": configurable["models"]["default/embed"],
                "question": configurable["user_question"],
                "template_environment": template_environment,
                "templates": templates,
                "rc": configurable["__rocket_client"],
                "rs": state["rocket_chat_state"],
                "cs": state["confluence_state"],
            }

            sig = inspect.signature(func)
            params = sig.parameters.keys()
            filtered = {k: v for k, v in extracted.items() if k in params}

            return await func(state, config, *args, **filtered, **kwargs)

        return wrapper

    return decorator


async def run_llm(
    llm: ChatOpenAI,
    template: Template,
    template_variables: dict,
    structure,
):
    """Render a template, construct an LLM with structured output and invoke the LLM"""
    prompt = template.render(template_variables)

    fail_counter = 0
    while True:
        try:
            structured_llm = llm.with_structured_output(structure)
            if fail_counter > 0:
                return await structured_llm.ainvoke(
                    [
                        SystemMessage(
                            content="It is important to conserve resources, keep your reply as short as possible."
                        ),
                        HumanMessage(content=prompt),
                    ]
                )
            else:
                return await structured_llm.ainvoke([prompt])
        except LengthFinishReasonError as e:
            log.exception(
                "LLM generated too many tokens",
                fail_counter=fail_counter,
                prompt=prompt,
            )
            fail_counter += 1
            if fail_counter >= 3:
                raise e


async def dispatch_log(l, message: str, arguments: dict):
    """Logs a message and dispatches the corresponding event"""
    l.info(message, **arguments)
    await adispatch_custom_event(message, arguments)
