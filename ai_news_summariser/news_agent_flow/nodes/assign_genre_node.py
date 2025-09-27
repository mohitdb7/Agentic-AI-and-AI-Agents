from news_agent_flow.models import GenreSumarisedModel, NewsAgentState
from news_agent_flow.tools import GenreManager
from news_agent_flow.configs import AppConfigModel
from news_agent_flow.utils import log_node

import time
import json
from datetime import datetime

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

@log_node("assign_genre")
def assign_genre(state: NewsAgentState) -> NewsAgentState:
    started_at = datetime.now()
    try:
        if app_config.is_mock:
            result = GenreSumarisedModel.from_json_file("mock_run/json_files/tavily_AI_Genre_Summary.json")
            time.sleep(5)
        else:
            result = GenreManager().assign_genre_to_summaries(state["news_summary"])
        
        ended_at = datetime.now()
        
        duration_seconds = (ended_at - started_at).total_seconds()
        print(f"assign_genre Time taken: {duration_seconds} seconds")

        with open("mock_run/json_files/tavily_AI_Genre_Summary.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=4)

        print("Returning from assign_genre")
        return {
            "query": state["query"],
            "results_search": state["results_search"],
            "result_crawl": state["result_crawl"],
            "news_summary": state["news_summary"],
            "genre_summary": result
        }
    except Exception as e:
        print(f"Exception in assign_genre {str(e)}")
        return {
            **state,
            "has_error": True,
            "error_message": str(e)
        }