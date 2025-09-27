from news_agent_flow.models import TavilyCrawlListModel, GenreSumarisedModel, SummarisedNewsArticle, NewsAgentState
from news_agent_flow.models import TavilyResponse, OutputGenreSummarisedResponseModel
from news_agent_flow.tools import GenreManager, search_news_on_web, summarise_news_list, get_news_content
from news_agent_flow.configs import AppConfigModel
from news_agent_flow.utils import log_node

import time
import json
from datetime import datetime


app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

@log_node("summarise_news")
def summarise_news(state: NewsAgentState) -> NewsAgentState:
    started_at = datetime.now()
    try:
        if app_config.is_mock:
            result = SummarisedNewsArticle.from_file("mock_run/json_files/tavily_AI_Summary.json")
            time.sleep(5)
        else:
            news_articles = []

            for wbs, wcl in zip(state["results_search"].results, state["result_crawl"]):
                combined = {
                    "url": wbs.url, 
                    "title": wbs.title,
                    "content": wcl.results[0].raw_content if isinstance(wcl, TavilyCrawlListModel) else wcl["results"][0]["raw_content"]
                }
                news_articles.append(combined)

            result = summarise_news_list.run(news_articles)
        ended_at = datetime.now()

        duration_seconds = (ended_at - started_at).total_seconds()
        print(f"summarise_news Time taken: {duration_seconds} seconds")

        with open("mock_run/json_files/tavily_AI_Summary.json", "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in result], f, indent=4)

        print("Returning from summarise_news")
        return {
            "query": state["query"],
            "results_search": state["results_search"],
            "result_crawl": state["result_crawl"],
            "news_summary": result
        }
    except Exception as e:
        print(f"Exception in summarise_news {str(e)}")
        return {
            **state,
            "has_error": True,
            "error_message": str(e)
        }