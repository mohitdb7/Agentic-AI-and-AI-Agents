from tavily import TavilyClient
from dotenv import load_dotenv
from crewai.tools import tool

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import os

from .clean_html_links import clean_web_content, clean_html_and_entities
from news_agent_flow.models import TavilyResponse, TavilyCrawlListModel, TavilyResultItem, TavilyCrawlItemModel

load_dotenv()

@tool
def search_news_on_web(query_text: str) -> TavilyResponse:
    """
        Search on the web to get the latest news
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    tavily_response = client.search(query_text, 
                                    max_results=10, 
                                    search_depth="advanced", 
                                    time_range="day")
    tavily_web_response: TavilyResponse = TavilyResponse(**tavily_response)

    return tavily_web_response

def crawl_url(crawl_item):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    crawl_result = client.crawl(crawl_item.url, instructions=f"find the information on {crawl_item.title}", 
                                max_breadth=2, max_depth=2)
    return crawl_result

@tool
def crawl_url_list(crawl_urls: list[TavilyResultItem] = []) -> TavilyCrawlListModel:
    """
    Crawl the urls from the web and get the complete detail from the web page crawling
    """
    results = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(crawl_url, url) for url in crawl_urls]

        for future in as_completed(futures):
            future_result = future.result()
            if future_result["results"]:
                merged_raw_content = ". ".join(item["raw_content"] if item["raw_content"] else "" for item in future_result["results"])
                merged_raw_content = clean_web_content(clean_html_and_entities(merged_raw_content))
                
                last_url = future_result["base_url"] if future_result["base_url"] else future_result["results"][-1]["url"]
                try:
                    last_url = last_url if isinstance(last_url, str) else last_url["url"] if last_url.get("url") else ""
                except:
                    last_url = ""
                
                # Replace results with one merged item
                future_result["results"] = [{
                    "url": last_url,
                    "raw_content": merged_raw_content
                }]

            results.append(future_result)
        
    # return [TavilyCrawlItemModel(**result) for result in results]
    with open("mock_run/json_files/crawl_result_from_api.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    return results