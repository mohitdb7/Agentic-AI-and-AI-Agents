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

# Node to search the web
def search_web_for_news(state: NewsAgentState) -> NewsAgentState:    
    if is_mock:
        result = TavilyResponse.from_json_file("mock_run/json_files/tavily_AI_response.json")
    else:
        result = search_news_on_web.run(state["query"])
    
    with open("mock_run/json_files/tavily_AI_response.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4)

    time.sleep(5)

    return {
        "query": state["query"],
        "results_search": result
    }

def crawl_news_content(state: NewsAgentState) -> TavilyCrawlListModel:

    def is_list_of_Crawl(obj):
        return isinstance(obj, list) and all(isinstance(item, TavilyCrawlListModel) for item in obj)

    response: TavilyResponse = state["results_search"]
    if is_mock:
        result = TavilyCrawlListModel.from_json_file("mock_run/json_files/tavily_AI_crawl.json")
    else:
        started_at = datetime.now()
        crawl_results = crawl_url_list.run(response.results)
        ended_at = datetime.now()
        result = crawl_results

    with open("mock_run/json_files/tavily_AI_crawl.json", "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in result] if is_list_of_Crawl(result) else result, f, indent=4)

    time.sleep(5)
    return {
        "query": state["query"],
        "results_search": state["results_search"],
        "result_crawl": result
    }

def summarise_news(state: NewsAgentState) -> NewsAgentState:

    if is_mock:
        result = SummarisedNewsArticle.from_file("mock_run/json_files/tavily_AI_Summary.json")
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

    time.sleep(5)

    return {
        "query": state["query"],
        "results_search": state["results_search"],
        "result_crawl": state["result_crawl"],
        "news_summary": result
    }

def assign_genre(state: NewsAgentState) -> NewsAgentState:
    if not is_mock:
        result = GenreSumarisedModel.from_json_file("mock_run/json_files/tavily_AI_Genre_Summary.json")
    else:
        result = GenreManager().assign_genre_to_summaries(state["news_summary"])

    with open("mock_run/json_files/tavily_AI_Genre_Summary.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4)

    time.sleep(5)

    return {
        "query": state["query"],
        "results_search": state["results_search"],
        "result_crawl": state["result_crawl"],
        "news_summary": state["news_summary"],
        "genre_summary": result
    }

def final_genre_summary(state: NewsAgentState) -> NewsAgentState:
    if not is_mock:
        out_obj: OutputGenreSummarisedResponseModel = OutputGenreSummarisedResponseModel.from_file("mock_run/json_files/tavily_AI_Final_Summarised_Genre.json")
    else:
        out_obj: OutputGenreSummarisedResponseModel = NewsSummariser().summarise_genre_news(state["genre_summary"])

    with open("mock_run/json_files/tavily_AI_Final_Summarised_Genre.json", "w", encoding="utf-8") as f:
        json.dump(out_obj.model_dump(), f, indent=4)

    time.sleep(5)

    return {
        "query": None,
        "results_search": None,
        "result_crawl": None,
        "news_summary": None,
        "genre_summary": None,
        "final_summary" : out_obj
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
    graph.add_edge("search_the_web", "crawl_the_news")
    graph.add_edge("crawl_the_news", "summarise_the_news")
    graph.add_edge("summarise_the_news", "assign_genre")
    graph.add_edge("assign_genre", "final_genre_summary")

    graph.add_edge("final_genre_summary", END)

    return graph.compile()

# Invoke the graph
graph = create_news_agent_flow()
output = graph.invoke({"query": "latest news on AI advancements in the last week"})
print(output)