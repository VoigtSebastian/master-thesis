# Master's Thesis

Welcome to the repository for my master's thesis!
If you want to make sure you're looking at the code at the time of submission, go to the [submission branch](https://github.com/VoigtSebastian/master-thesis/tree/submission).

This README provides an overview of the project structure and instructions for executing and editing the code.

First, let's clarify the project's focus.
My master's thesis leverages Large Language Models (LLMs) and embedding models to create complex workflows in the form of LLM-based autonomous agents.
These workflows can autonomously search through various systems, improving the efficiency and accuracy of traditional search methods for research tasks.
The agent, provided in the form of this code, specializes in retrieval and aggregation of proprietary information.

The repository includes the following key components:
- The complete code that was developed for this thesis.
- Documentation of this code in the form of multiple READMEs.
- Instructions for setting up the environment and running the code.

Fore more details on the agent's workflow, you can go to [the development README](dev/README.md#workflow).

After I published my findings in the end of April 2025 I will also publish the written thesis in addition to this code.
The repository may therefore contain references to the `thesis` sub-directory which is currently not yet included.

## Abstract
In recent years, Large Language Models (LLMs) have gained significant popularity, seamlessly integrating into our daily lives by assisting with a multitude of tasks — from composing emails to providing insightful recommendations.
However, their effectiveness tends to decline in professional environments, where the need for precision and access to internal information is paramount.

Trained primarily on publicly available data, using an LLM to retrieve proprietary information can lead to falsehoods, inaccuracies, or fictitious details, thereby creating a trust deficit in business applications.
Although solutions such as hosting private LLM, fine-tuning, and Retrieval Augmented Generation (RAG) approaches show promise, they often face limitations in adaptability and robustness.

In response to these challenges, we propose a novel architecture focused on LLM-based autonomous agents, that specializes in retrieval and aggregation of proprietary information.
Capable of navigating complex problem-solving scenarios and leveraging diverse tools for data retrieval makes them the ideal choice for business-critical applications.

## TLDR

Development occurs within a `devcontainer`, ensuring a consistent environment with all necessary dependencies for everyone.

To use this easily, install [Docker](https://docs.docker.com/engine/install/) and [Visual Studio Code](https://code.visualstudio.com/download). Then, follow these steps:

1. Open Visual Studio Code in the root of this project.
2. Open the command palette (`CTRL/CMD+SHIFT+P`) and run `Dev Container: Open Folder in Container`. This will open the container and include the necessary user dependencies.
3. Proceed to the [development](dev/README.md#TLDR) or [thesis/writing](thesis/README.md#TLDR) README based on your needs.

## Structure

This repository's main directory is `dev/`, which contains all of the code that was developed as part of my master's thesis.
The main code can be found in `dev/src/`, where the agent's and infrastructure code is located.
Additionally, the [agent's frontend](dev/agent-frontend/) and the [questionnaire](dev/questionnaire/) used in the final evaluation are included.
For more details, have a look at [development README](dev/README.md)

```
.
└── dev
    ├── agent-frontend
    ├── questionnaire
    └── src
        ├── confluence
        ├── main
        ├── prompts
        ├── rocket
        ├── shared
        └── util
```

## Acknowledgements

I am grateful to my supervisors Prof. Dr. Ing. Oliver Haase, Dr. Benjamin Hartmann, and Thomas Vamos for their invaluable insights and unwavering patience throughout this journey.

This research is conducted in collaboration with the SEITENBAU GmbH.
I would like to express my gratitude to SEITENBAU for providing this opportunity and their invaluable support throughout the research process.

## License

This project is licensed under the [MIT License](LICENSE.txt).
I always welcome comments, suggestions, or questions - please feel free to reach out if you have ideas for improvements or would like to discuss the project further!
