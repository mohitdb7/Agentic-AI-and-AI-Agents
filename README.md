# Agentic AI and AI Agents
This repository contains the **AI News Summariser**, an agentic system designed to autonomously fetch, process, and present news from the web. The system leverages a multi-agent framework built with LangGraph and CrewAI to create a sophisticated pipeline that searches for news, crawls content, summarizes articles, assigns them to relevant genres, and generates a final, coherent summary for each category.

The project includes a FastAPI backend for serving the agentic workflow, a Streamlit frontend for interactive visualization, and MongoDB for caching results.

## Key Features

- **Agentic Workflow**: Utilizes a stateful graph (LangGraph) to manage a sequence of tasks: web search, content crawling, summarization, and genre classification.
- **Multi-Agent System**: Employs agents built with CrewAI to perform specialized tasks like summarizing content and assigning genres.
- **Dynamic News Fetching**: Searches for real-time news articles based on user-selected topics using the Tavily API.
- **Hierarchical Summarization**: First, it summarizes individual articles, then it creates a final, aggregated summary for each news category.
- **Streaming API**: A FastAPI backend streams the results of each step in the agentic flow to the frontend in real-time.
- **Interactive UI**: A Streamlit-based user interface allows users to select news genres, initiate the process, and view results as they are generated and organized.
- **Result Caching**: Uses MongoDB to store the results of the agent flow, enabling near-instantaneous responses for previously queried topics.
- **Configurable Components**: Easily switch between LLMs (Gemini, OpenAI), summarization models, and other components via a central configuration file.

## Architecture

The AI News Summariser operates on a stateful graph built with **LangGraph**. The workflow is composed of several nodes, each representing a distinct task performed by an AI agent or tool:

1.  **Search the Web (`search_the_web`)**: Takes a user query (e.g., "AI, Technology") and uses the Tavily API to find relevant, recent news articles.
2.  **Crawl News Content (`crawl_the_news`)**: Fetches the full content from the URLs provided by the search node.
3.  **Summarize News (`summarise_the_news`)**: Processes the crawled content of each article to generate a concise summary.
4.  **Assign Genre (`assign_genre`)**: Categorizes each summarized article into predefined genres like "Technology," "AI," "Business," etc., using an LLM.
5.  **Final Genre Summary (`final_genre_summary`)**: For each genre, it takes all the individual summaries and creates a single, aggregated, and coherent meta-summary.

The system is served via a **FastAPI** backend, which provides a streaming API endpoint. Results from each stage are cached in **MongoDB** to provide instant responses for subsequent identical queries. A **Streamlit** application provides a rich, interactive user interface to consume and visualize the streamed results.

## Getting Started

### Prerequisites

- Python 3.13+
- MongoDB
- `uv` (or another Python package manager like `pip`)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/mohitdb7/Agentic-AI-and-AI-Agents.git
    cd Agentic-AI-and-AI-Agents/ai_news_summariser
    ```

2.  **Set Up Environment Variables**
    Create a `.env` file in the `ai_news_summariser` directory and add your API keys:
    ```.env
    TAVILY_API_KEY="your_tavily_api_key"
    GOOGLE_API_KEY="your_google_api_key"
    # OPENAI_API_KEY="your_openai_api_key" # Required if using OpenAI models
    ```

3.  **Install Dependencies**
    The project's dependencies are listed in `pyproject.toml`. You can install them using `uv`:
    ```bash
    uv pip install -r requirements.txt 
    # Or install directly from the pyproject.toml dependencies
    uv pip install beautifulsoup4 crewai "dataclasses>=0.8" "dotenv>=0.9.9" fastapi langchain langchain-google-genai langchain-openai langgraph motor pathlib pydantic sseclient-py tavily-python torch transformers uvicorn
    ```

4.  **Set Up and Run MongoDB**
    If you are using macOS, you can install MongoDB via Homebrew:
    ```bash
    brew tap mongodb/brew
    brew update
    brew install mongodb-community@7.0
    ```
    Start the MongoDB service:
    ```bash
    brew services start mongodb/brew/mongodb-community@7.0
    ```
    To verify it's running, check the services list:
    ```bash
    brew services list
    ```

## Usage

The application consists of a backend API and a frontend UI. They should be run in separate terminal sessions from the `ai_news_summariser` directory.

1.  **Run the Backend API**
    This command starts the FastAPI server on `http://localhost:8080`.
    ```bash
    uv run run.py
    ```

2.  **Run the Frontend UI**
    This command starts the Streamlit application.
    ```bash
    streamlit run front_end_ui/streamlit_app.py
    ```
    The Streamlit app will be accessible in your web browser, typically at `http://localhost:8501`. You can enter the API URL (`http://localhost:8080/news_summariser`), select genres, and click "Search & Stream" to start the process.

## Configuration

The behavior of the agentic flow can be customized through configuration files.

-   **Agent & Tool Configuration (`news_agent_flow/configs/agent_config.json`)**:
    This file allows you to switch between different implementations for various components of the agentic flow:
    -   `llm`: Switch between `gemini` and `open_ai` models for the agents.
    -   `web_crawl`: Configure the Tavily tool to be used.
    -   `summarizer`: Choose the summarization model (e.g., `facebook/bart-large-cnn` or an LLM).
    -   `assign_genre`: Select the method for genre assignment.

-   **Backend Configuration (`rest_api/configs/be_config.json`)**:
    This file controls settings for the FastAPI server and database:
    -   `storage`: Configure the MongoDB connection URL, port, and data expiration time.
    -   `stream_sequence` & `stream_events`: Define the order and naming of events sent to the frontend.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
