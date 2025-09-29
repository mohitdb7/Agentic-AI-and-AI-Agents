# 🤖 Agentic News Summariser: A LangGraph & CrewAI Orchestration

**A high-performance, containerized multi-agent system designed for autonomous real-time news aggregation, processing, and categorized summarization.**

| Status | Coverage | License |
| :---: | :---: | :---: |
| [![Build Status](https://img.shields.io/badge/Status-Stable-brightgreen)](TBD) | [![Test Coverage](https://img.shields.io/badge/Coverage-95%25-green)](TBD) | [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) |

## 🚀 Quick Start (One-Command Setup)

The fastest way to get the entire stack—FastAPI backend, Streamlit frontend, and MongoDB cache—running locally is using the **uv**.

Here is the the tech doc for this project: **[AI News Summariser](https://www.linkedin.com/in/mohit-kumar-dubey/)**

```bash
# 1. Clone the repository
git clone [https://github.com/mohitdb7/Agentic-AI-and-AI-Agents.git](https://mohitdubey60-1759037840631.atlassian.net/wiki/spaces/~71202056e8fb05e8a04bb4af2b6261c96eb4e2/pages/98308/AI+News+Summariser)
cd Agentic-AI-and-AI-Agents/ai_news_summariser

# 2. Configure API Keys
# Ensure your .env file is set up (see Configuration section)

# 3. Build and run the entire stack (FastAPI, Streamlit, MongoDB)
docker-compose up --build
````

The application will be accessible at:

  * **Frontend UI:** `http://localhost:8501`
  * **Backend API:** `http://localhost:8080` (for direct API access/testing)

-----

## 💡 Project Overview: The Architecture

The **AI News Summariser** is a sophisticated, agentic system that transforms raw web data into organized, meta-summarized intelligence. It decouples the core agent logic (LangGraph/CrewAI) from the service layer (FastAPI), ensuring scalability and clear separation of concerns.

### Core Stack

| Component | Role | Technology |
| :---: | :---: | :---: |
| **Agent Orchestration** | Manages the stateful, multi-step workflow. | **LangGraph** (Stateful Graph) |
| **Agent Execution** | Executes specialized, individual tasks (e.g., genre assignment). | **CrewAI and LangChain** (Multi-Agent Framework) |
| **Backend Service** | Provides a high-performance, streaming API endpoint. | **FastAPI** |
| **Frontend UI** | Interactive user interface and real-time visualization. | **Streamlit** |
| **Data/State** | Persistent caching for previously processed queries. | **MongoDB / In Memory** (via `motor`) |
| **LLMs/Tools** | Generative intelligence and real-time data access. | **Gemini/OpenAI, facebook-bart** & **Tavily API** |

### Key Features

- **Agentic Workflow**: Utilizes a stateful graph (LangGraph) to manage a sequence of tasks: web search, content crawling, summarization, and genre classification.
- **Multi-Agent System**: Employs agents built with CrewAI to perform specialized tasks like summarizing content and assigning genres.
- **Dynamic News Fetching**: Searches for real-time news articles based on user-selected topics using the Tavily API.
- **Hierarchical Summarization**: First, it summarizes individual articles, then it creates a final, aggregated summary for each news category.
- **Streaming API**: A FastAPI backend streams the results of each step in the agentic flow to the frontend in real-time.
- **Interactive UI**: A Streamlit-based user interface allows users to select news genres, initiate the process, and view results as they are generated and organized.
- **Result Caching**: Uses MongoDB to store the results of the agent flow, enabling near-instantaneous responses for previously queried topics.

### Agentic Workflow (The LangGraph Pipeline)

The system utilizes a stateful graph built with **LangGraph** to manage the sequence of complex, inter-dependent tasks. Each node in the graph represents a specialized action, ensuring reliability and observability of the flow:

1.  **Search the Web (`search_the_web`):** Takes a user query and uses the Tavily API to find relevant, recent news articles.
2.  **Crawl News Content (`crawl_the_news`):** Fetches the full content from the URLs provided by the search node.
3.  **Summarize News (`summarise_the_news`):** Processes the crawled content of each article to generate a concise summary.
4.  **Assign Genre (`assign_genre`):** Categorizes each summarized article into predefined genres like "Technology," "AI," "Business," etc., using an LLM.
5.  **Final Genre Summary (`final_genre_summary`):** For each genre, it takes all the individual summaries and creates a single, aggregated, and coherent meta-summary.

-----

The system is served via a **FastAPI** backend, which provides a streaming API endpoint. Results from each stage are cached in **MongoDB** to provide instant responses for subsequent identical queries. A **Streamlit** application provides a rich, interactive user interface to consume and visualize the streamed results.

## ⚙️ Development Setup (Native)

For development and debugging, follow these steps to run the components natively.

### 1\. Prerequisites

  * **Python 3.11+** (The project requires Python 3.13+)
  * **MongoDB:** A running instance is required for the caching layer.
  * **`uv`:** Recommended modern package manager for rapid dependency installation (or `pip`).

### 2\. Installation and Environment

1.  **Clone the Repository:**

    ```bash
    git clone [https://github.com/mohitdb7/Agentic-AI-and-AI-Agents.git](https://github.com/mohitdb7/Agentic-AI-and-AI-Agents.git)
    cd Agentic-AI-and-AI-Agents/ai_news_summariser
    ```

2.  **Environment Variables (`.env`)**
    Create a `.env` file in the `ai_news_summariser` directory to securely store your API keys:

    ```.env
    # Example .env file content
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
    TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
    LANGCHAIN_API_KEY=""
    LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
    LANGCHAIN_PROJECT=“your_project_name”
    LANGCHAIN_TRACING_V2=true
    CREWAI_TRACING_ENABLED=true
    # Add any other required sensitive keys here

    # --- Database (Adjust if using a remote MongoDB) ---
    MONGO_DB_URL="mongodb://localhost:27017" 
    ```

3.  **Install Dependencies**
    Use `uv` for a fast installation based on the `pyproject.toml`:

    ```bash
    uv venv .venv
    source .venv/bin/activate
    uv sync --active 
    ```

4.  **MongoDB Setup (If running locally)**

      * **macOS (Homebrew):**
        ```bash
        brew tap mongodb/brew
        brew install mongodb-community@7.0
        brew services start mongodb/brew/mongodb-community@7.0
        ```
      * Verify the service is running: `brew services list`

### 3\. Execution

Run the Backend API and the Frontend UI in separate terminal sessions from the `ai_news_summariser` directory.

#### **A. Start the Backend API (Terminal 1)**

The FastAPI server will start on `http://localhost:8080`.

```bash
uv run run.py
```

#### **B. Start the Frontend UI (Terminal 2)**

The Streamlit app will launch in your browser, typically at `http://localhost:8501`.

```bash
streamlit run front_end_ui/streamlit_app.py
```

**Usage Flow:** In the Streamlit UI, enter the API URL (`http://localhost:8080/news_summariser`), select genres, and click **"Search & Stream"** to initiate the agentic workflow. The results of each step will stream back to the UI in real-time.

-----

## 🛠️ Configuration and Extensibility (DevOps Focus)

The project is designed for high configurability, allowing for quick model and service swaps without modifying core logic.

### 1\. Agent & Tool Configuration (`news_agent_flow/configs/agent_config.json`)

This file is crucial for customizing the AI components and tools:

| Configuration Key | Purpose | Options/Examples |
| :---: | :---: | :---: |
| `llm` | Defines the LLM provider for core agent tasks. | Switch between `gemini` and `open_ai` models. |
| `web_crawl` | Configures the web search/crawling tool. | Configures the Tavily tool. |
| `summarizer` | Selects the model for individual article summarization. | Choose the summarization model (e.g., `facebook/bart-large-cnn` or an LLM). |
| `assign_genre` | Selects the method used by the agent for categorization. | Select the method for genre assignment. |
| `final_summary` | Selects the method used by the agent for genre summarisation. | Select the method for Summary. |

### 2\. Backend and Caching Configuration (`rest_api/configs/be_config.json`)

This controls the API and persistence layer:

| Configuration Key | Purpose | Details |
| :---: | :---: | :---: |
| `storage` | MongoDB connection settings and data policies. | Configure the MongoDB connection URL, port, and data expiration time. |
| `stream_sequence` | Event order for the streaming API. | Define the order of events sent to the frontend. |
| `stream_events` | Naming convention for streamed events. | Define the naming of events sent to the frontend. |

-----

## Configuration

The behavior of the agentic flow can be customized through configuration files.

-   **Agent & Tool Configuration (`news_agent_flow/configs/agent_config.json`)**:
    This file allows you to switch between different implementations for various components of the agentic flow:
    -   `llm`: Switch between `gemini` and `open_ai` models for the agents.
    -   `web_crawl`: Configure the Tavily tool to be used.
    -   `summarizer`: Choose the summarization model (e.g., `facebook/bart-large-cnn` or an LLM).
    -   `assign_genre`: Using **Langchain** for assigning the genres with llm of choice (Gemini or OpenAI)
    -   `final_summary`: Using **CrewAI** for assigning the genres with llm of choice (Gemini or OpenAI)

-   **Backend Configuration (`rest_api/configs/be_config.json`)**:
    This file controls settings for the FastAPI server and database:
    -   `storage`: Configure the MongoDB connection URL, port, and data expiration time.
    -   `stream_sequence` & `stream_events`: Define the order and naming of events sent to the frontend.

## 🔒 License

This project is licensed under the **MIT License**. See the accompanying [`LICENSE`](https://www.google.com/search?q=LICENSE) file for full details.

------

Made with ❤️ By **[Mohit Kumar Dubey](https://www.linkedin.com/in/mohit-kumar-dubey/)**