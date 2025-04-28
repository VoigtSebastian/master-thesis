import asyncio

from confluence import confluence_graph
from util.environment import setup_config_state

#
# Debugging and development executable, runs ONLY THE CONFLUENCE graph
#


async def main():
    config, state = setup_config_state()

    print("-" * 80)
    print(confluence_graph.get_graph().draw_mermaid())
    print("-" * 80)
    print()

    source = None

    async for msg, metadata in confluence_graph.astream(
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
    print("-" * 80)
    print(state)
    print("-" * 80)


asyncio.run(main())
