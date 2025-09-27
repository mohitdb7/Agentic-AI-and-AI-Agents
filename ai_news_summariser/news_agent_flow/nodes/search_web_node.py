from news_agent_flow.models import TavilyCrawlListModel, GenreSumarisedModel, SummarisedNewsArticle, NewsAgentState
from news_agent_flow.models import TavilyResponse, OutputGenreSummarisedResponseModel
from news_agent_flow.tools import GenreManager, search_news_on_web, summarise_news_list, get_news_content
from news_agent_flow.configs import AppConfigModel
from news_agent_flow.utils import log_node

import time
import json
from datetime import datetime

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

@log_node("search_web_for_news")
def search_web_for_news(state: NewsAgentState) -> NewsAgentState: 
    started_at = datetime.now()
    try:
        if app_config.is_mock:
            result = TavilyResponse.from_json_file("mock_run/json_files/tavily_AI_response.json")
            time.sleep(5)
        else:
            result = search_news_on_web.run(state["query"])
        
        with open("mock_run/json_files/tavily_AI_response.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=4)
        ended_at = datetime.now()
        
        duration_seconds = (ended_at - started_at).total_seconds()
        print(f"search_web_for_news Time taken: {duration_seconds} seconds")

        print("Returning from search_web_for_news")
        return {
            "query": state["query"],
            "results_search": result
        }
    except Exception as e:
        print(f"Exception in search_web_for_news {str(e)}")
        return {
            **state,
            "has_error": True,
            "error_message": str(e)
        }
    
    return
    
@log_node("crawl_news_content")
def crawl_news_content(state: NewsAgentState) -> TavilyCrawlListModel:

    def is_list_of_Crawl(obj):
        return isinstance(obj, list) and all(isinstance(item, TavilyCrawlListModel) for item in obj)

    started_at = datetime.now()
    try:
        response: TavilyResponse = state["results_search"]
        if app_config.is_mock:
            result = TavilyCrawlListModel.from_json_file("mock_run/json_files/tavily_AI_crawl.json")
            time.sleep(5)
        else:
            # crawl_results = crawl_url_list.run(response.results)
            crawl_results = [TavilyCrawlListModel(**item) for item in get_news_content.run(response.results)]
            result = crawl_results
        ended_at = datetime.now()
        
        duration_seconds = (ended_at - started_at).total_seconds()
        print(f"crawl_news_content Time taken: {duration_seconds} seconds")

        with open("mock_run/json_files/tavily_AI_crawl.json", "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in result] if is_list_of_Crawl(result) else result, f, indent=4)

        print("Returning from crawl_news_content")
        return {
            "query": state["query"],
            "results_search": state["results_search"],
            "result_crawl": result
        }
    except Exception as e:
        print(f"Exception in crawl_news_content {str(e)}")
        return {
            **state,
            "has_error": True,
            "error_message": str(e)
        }