from news_agent_flow.models import NewsAgentState
from news_agent_flow.models import OutputGenreSummarisedResponseModel
from news_agent_flow.agents import NewsSummariser
from news_agent_flow.configs import AppConfigModel
from news_agent_flow.utils import log_node

import time
import json
from datetime import datetime

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

@log_node("final_genre_summary")
def final_genre_summary(state: NewsAgentState) -> NewsAgentState:
    started_at = datetime.now()
    try:
        if app_config.is_mock:
            out_obj: OutputGenreSummarisedResponseModel = OutputGenreSummarisedResponseModel.from_file("mock_run/json_files/tavily_AI_Final_Summarised_Genre.json")
            time.sleep(5)
        else:
            out_obj: OutputGenreSummarisedResponseModel = NewsSummariser().summarise_genre_news(state["genre_summary"])

        ended_at = datetime.now()

        duration_seconds = (ended_at - started_at).total_seconds()
        print(f"final_genre_summary Time taken: {duration_seconds} seconds")

        with open("mock_run/json_files/tavily_AI_Final_Summarised_Genre.json", "w", encoding="utf-8") as f:
            json.dump(out_obj.model_dump(), f, indent=4)

        print("Returning from final_genre_summary")
        return {
            "query": None,
            "results_search": None,
            "result_crawl": None,
            "news_summary": None,
            "genre_summary": None,
            "final_summary" : out_obj
        }
    except Exception as e:
        print(f"Exception in final_genre_summary {str(e)}")
        return {
            **state,
            "has_error": True,
            "error_message": str(e)
        }