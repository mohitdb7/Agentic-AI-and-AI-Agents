from langgraph.graph import StateGraph, START, END
from news_agent_flow.models import TavilyResponse, OutputGenreSummarisedResponseModel
from news_agent_flow.models import TavilyCrawlListModel, GenreSumarisedModel, SummarisedNewsArticle
from news_agent_flow.tools import GenreManager, search_news_on_web, crawl_url_list, summarise_news_list
from news_agent_flow.agents import NewsSummariser
from news_agent_flow.configs import AppConfigModel

from typing import TypedDict

import time
import json
from datetime import datetime

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

is_mock = True

# Define the state schema
class NewsAgentState(TypedDict):
    query: str
    results_search: TavilyResponse | None
    result_crawl: list[TavilyCrawlListModel] | None
    news_summary: list[SummarisedNewsArticle] | None
    genre_summary: GenreSumarisedModel | None
    final_summary: OutputGenreSummarisedResponseModel | None
    has_error: bool
    error_message: str


# Node to search the web
def search_web_for_news(state: NewsAgentState) -> NewsAgentState: 
    try:
        if is_mock:
            result = TavilyResponse.from_json_file("mock_run/json_files/tavily_AI_response.json")
            time.sleep(5)
        else:
            result = search_news_on_web.run(state["query"])
        
        with open("mock_run/json_files/tavily_AI_response.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=4)

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

def crawl_news_content(state: NewsAgentState) -> TavilyCrawlListModel:

    def is_list_of_Crawl(obj):
        return isinstance(obj, list) and all(isinstance(item, TavilyCrawlListModel) for item in obj)

    try:
        response: TavilyResponse = state["results_search"]
        if is_mock:
            result = TavilyCrawlListModel.from_json_file("mock_run/json_files/tavily_AI_crawl.json")
            time.sleep(5)
        else:
            started_at = datetime.now()
            crawl_results = crawl_url_list.run(response.results)
            ended_at = datetime.now()
            result = crawl_results

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

def summarise_news(state: NewsAgentState) -> NewsAgentState:
    try:
        if is_mock:
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

def assign_genre(state: NewsAgentState) -> NewsAgentState:
    try:
        if is_mock:
            result = GenreSumarisedModel.from_json_file("mock_run/json_files/tavily_AI_Genre_Summary.json")
            time.sleep(5)
        else:
            result = GenreManager().assign_genre_to_summaries(state["news_summary"])

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

def final_genre_summary(state: NewsAgentState) -> NewsAgentState:
    try:
        if is_mock:
            out_obj: OutputGenreSummarisedResponseModel = OutputGenreSummarisedResponseModel.from_file("mock_run/json_files/tavily_AI_Final_Summarised_Genre.json")
            time.sleep(5)
        else:
            out_obj: OutputGenreSummarisedResponseModel = NewsSummariser().summarise_genre_news(state["genre_summary"])

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

# Graph creation
def create_news_agent_flow():
    graph = StateGraph(state_schema=NewsAgentState)

    graph.add_node("search_the_web", search_web_for_news)
    graph.add_node("crawl_the_news", crawl_news_content)
    graph.add_node("summarise_the_news", summarise_news)
    graph.add_node("assign_genre", assign_genre)
    graph.add_node("final_genre_summary", final_genre_summary)

    graph.add_edge(START, "search_the_web")
    # Router nodes
    graph.add_conditional_edges("search_the_web",  lambda s: END if s.get("has_error") else "crawl_the_news")
    graph.add_conditional_edges("crawl_the_news", lambda s: END if s.get("has_error") else "summarise_the_news")
    graph.add_conditional_edges("summarise_the_news", lambda s: END if s.get("has_error") else "assign_genre")
    graph.add_conditional_edges("assign_genre", lambda s: END if s.get("has_error") else "final_genre_summary")
    graph.add_edge("final_genre_summary", END)

    graph.add_edge("final_genre_summary", END)

    return graph.compile()

# Invoke the graph
# graph = create_news_agent_flow()
# output = graph.invoke({"query": "latest news on AI advancements in the last week"})
# print("Graph completed")
# print(output)