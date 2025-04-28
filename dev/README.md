# Code

After creating the necessary environment (`../README.md`) you can start running and editing code.
This file will explain the basics on how to do this.

## TLDR
### Dependencies
Open a new terminal and run the following commands to set up the environment:

```sh
pip install --upgrade pip
pip install uv
```

Navigate to the `dev` directory and set up the virtual environment:

```sh
cd dev
uv lock && uv sync
source .venv/bin/activate
```

Now, open the command palette (`CTRL/CMD+SHIFT+P`) and enter the command `Python: Select Interpreter`, use `Enter interpreter path ...`, `Find ...` and enter the path `~/thesis/dev/.venv/bin/python`.
This will setup code to use the correct Python interpreter in the editor and terminal
To verify that it worked, open a terminal ``CTRL/CMD+SHIFT+` ``, there should be a `(agent-workspace)` before your username.

At this point you can start the agent with the UI by opening the command palette (`CTRL/CMD+SHIFT+P`), executing `Tasks: Run Task` and choosing `Start UI`.

### Environment

Set the following environment variables by putting them in `dev/.env`.
You will need to generate the API tokens:

```env
OPENAI_API_KEY= # OpenAI compatible API key
MODEL_NAME= # Name of the OpenAI compatible model
ROOT_URL= # Base URL for the OpenAI compatible API

EMBEDDING_NAME= # Name of the OpenAI compatible embedding model
MAX_EMBEDDING_CHARACTERS= # The maximum number of characters you want to pass to your embedding model

CONFLUENCE_URL= # Base URL for Confluence - skip the final /
CONFLUENCE_API_KEY= # API key for Confluence

ROCKET_CHAT_URL= # Base URL for Rocket.Chat - skip the final /
ROCKET_CHAT_TOKEN= # Token for Rocket.Chat
ROCKET_CHAT_ID= # ID for Rocket.Chat
```

### Running the agent

To run the agent, you have two options: one for quick development with extensive observability, and the other for a polished, finished app experience.

For development and a quick setup test, execute any of the following commands:

- Run the entire agent with:
  ```bash
  python src/main_graph.py
  ```
- Run a specific sub-graph with:
  ```bash
  python src/rocket_graph.py
  ```
  or
  ```bash
  python src/cql_graph.py
  ```

For the polished app-experience, open the command palette (`CTRL/CMD+SHIFT+P`), execute `Tasks: Run Task` and choose `Start UI`.

## Structure
This directory consists of three main sub-directories:
- `agent-frontend/` contains the `vue.js` code that interacts with the agent.
- `questionnaire/` contains the `vue.js` code used to evaluate the master's thesis.
- `evaluation/` contains the jupyter notebook that is used to evaluate the questionnaire.
- `src/` contains the Python code that describes and runs the agent.

After running the agent, a `log/` directory will be created, containing logs for every run.

```
.
├── agent-frontend
├── evaluation
├── questionnaire
├── log
└── src
    ├── confluence
    ├── main
    ├── prompts
    │   ├── confluence
    │   ├── general
    │   ├── main
    │   └── rocket
    ├── rocket
    ├── shared
    └── util

```

The `src` directory contains all relevant Python code, subdivided into multiple directories:
- `confluence/`, `rocket/`, and `main/` contain `LangGraph`/agent-specific code.
- `prompts/` contains relevant prompts in the `jinja` templating language, following the structure of the `src/` directory.
- `shared/` contains information shared by the agents, such as configuration, state, and the final output.
- `util/` contains utility functions, including API clients, logging, and general operations.

Run each agent using the commands described [here](#running-the-agent).
The [main agent](/dev/src/main) serves as the primary decision maker or orchestrator for the [Confluence](/dev/src/confluence) and [Rocket](dev/src/rocket) agents.

## Workflow

As described earlier, the [main agent](/dev/src/main) is the primary decision maker or orchestrator and the [Confluence](/dev/src/confluence) and [Rocket](dev/src/rocket) agents are only secondary.
The general workflow of the [main agent](/dev/src/main) is therefore to look at the available data and decide what sources (Confluence or Rocket.Chat) would be smart to access.
The [Confluence](/dev/src/confluence) and [Rocket](dev/src/rocket) agents are currently implemented as rather naive agents that mostly focus on querying their respective API and summarizing the outcome, taking the query history into account.

### Confluence Agent

The Confluence agent constructs a set of keywords in the `build_query` node, which can be used in a [CQL query](https://developer.atlassian.com/server/confluence/advanced-searching-using-cql/).
It then constructs and executes the query in the `execute_cql` node.
The [tool](dev/src/confluence/tool.py) performs the following steps:

+ Execute the query and download the top `n` (~100) pages that match it.
+ Rank the pages using an embedding model and the embedded distance to the user's question.
+ Filter the top `m` (~10) pages.
+ Construct a summary of those pages, tailored to the user's question.
+ Return the results with a link to the original page.

### Rocket.Chat Agent

The Rocket.Chat agent, unlike the Confluence agent, not only constructs and executes queries to search for information but also filters channels to enhance the relevance of the search results. This allows users to ask specific questions, such as "Did I ever chat with foo about bar," and ensures that the search is confined to channels where `foo` is a participant.

The `build_search_pattern` node generates keywords to filter the list of available channels and keywords to search within those channels.
The `search` node then executes the queries in the corresponding channels by running the [tool](dev/src/rocket/tool.py).
The Rocket.Chat tool follows these steps:

+ Execute the query in the list of filtered chats.
+ Rank the chats using an embedding model and the embedded distance to the user's question.
+ Filter the top `n` (~3) chats.
+ Construct a summary of those chats, tailored to the user's question.
+ Return the results with a link to the original chat.

## Questionnaire

The questionnaire for evaluating the prototype is located in `dev/questionnaire`.
This directory contains a VueJS application.
To run the application, follow these steps:

```sh
cd dev/questionnaire
npm install
npm run dev
```
