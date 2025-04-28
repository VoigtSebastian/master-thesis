import asyncio

from main import graph
from rich.console import Console
from rich.markdown import Markdown
from shared.state import GraphState
from util.environment import setup_config_state

#
# Debugging and development executable, runs ONLY THE CONFLUENCE graph
#


async def main():
    config, state = setup_config_state()

    print("-" * 80)
    print(graph.get_graph().draw_mermaid())
    print("-" * 80)
    print()

    source = None

    async for msg, metadata in graph.astream(
        state,
        stream_mode="messages",
        config=config,
    ):
        if not source or metadata["langgraph_node"] != source:
            print("\n")
            source = metadata["langgraph_node"]
            print(f"{source}: ", end="", flush=True)
        print(msg.content, end="", flush=True)

    print()
    print("-" * 80, end="\n\n")

    final_state: GraphState = graph.get_state(config=config).values
    response = final_state["final_response"].message
    Console().print(Markdown(response))


asyncio.run(main())
