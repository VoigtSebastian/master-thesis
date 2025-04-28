import json

import structlog
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from shared.state import GraphState
from main import graph
from util.environment import setup_config_state
from fastapi.middleware.cors import CORSMiddleware

# Provides a server that runs the graph and returns custom events + the last message that was generated
# fastapi dev src/server.py

log = structlog.get_logger(emitter="server")

print("-" * 80)
print(graph.get_graph().draw_mermaid())
print("-" * 80)

origins = ["http://localhost", "http://127.0.0.1:5174/", "http://127.0.0.1:8000/", "*"]


async def stream_graph(query: str):
    config, state = setup_config_state(query)
    final_response = None

    try:
        async for event in graph.astream_events(
            state,
            version="v2",
            config=config,
        ):
            if event["event"] == "on_custom_event":
                name = event["name"]
                data = event["data"]

                m = json.dumps({"event": name, "data": data})
                yield m + "\n"

        final_state: GraphState = graph.get_state(config=config).values
        final_response = final_state["final_response"]
        log.info("final state reached", final_response=final_response)
    except:
        error_message = json.dumps(
            {
                "event": "final_message",
                "data": {"message": "A fatal error occurred running the agent"},
            }
        )
        yield error_message + "\n"

    if final_response:
        m = json.dumps({"event": "final_message", "data": final_response.model_dump()})
        yield m + "\n"
    else:
        error_message = json.dumps(
            {
                "event": "final_message",
                "data": {
                    "message": "A fatal error occurred extracting the final message"
                },
            }
        )
        yield error_message + "\n"


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/streaming/{query}")
async def main(query: str):
    return StreamingResponse(stream_graph(query), media_type="text/event-stream")
