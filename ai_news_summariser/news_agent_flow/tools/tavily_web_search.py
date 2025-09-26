from tavily import TavilyClient
from dotenv import load_dotenv
from crewai.tools import tool
from typing import List, Optional

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import os

from .clean_html_links import clean_web_content, clean_html_and_entities
from news_agent_flow.models import TavilyResponse, TavilyCrawlListModel, TavilyResultItem, TavilyCrawlItemModel
from news_agent_flow.configs import AppConfigModel

web_crawl_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

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

def _crawl_url(crawl_item, client):
    crawl_result = client.crawl(crawl_item.url, instructions=f"find the information on {crawl_item.title}", 
                                max_breadth=2, max_depth=2)
    return crawl_result

def _crawl_url_list(crawl_urls: list[TavilyResultItem] = []) -> TavilyCrawlListModel:
    """
    Crawl the urls from the web and get the complete detail from the web page crawling
    """
    results = []
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    with ThreadPoolExecutor(max_workers=web_crawl_config.web_crawl_parallel) as executor:
        futures = [executor.submit(_crawl_url, url, client) for url in crawl_urls]

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

def _find_by_url(items: List[TavilyResultItem], url: str) -> Optional[TavilyResultItem]:
    return next((item for item in items if item.url == url), None)


def _extract_from_url(news_item, client):
    result= client.extract(urls=[news_item.url], include_images=False)
    return result

def _extract_from_urls(crawl_urls: list[TavilyResultItem] = []):
    """Extract the web content"""

    results = []
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    with ThreadPoolExecutor(max_workers=web_crawl_config.web_crawl_parallel) as executor:
        futures = [executor.submit(_extract_from_url, url, client) for url in crawl_urls]

        for future in futures:
            try:
                future_result = future.result()
                item = future_result["results"] if future_result["results"] else None
                if item:
                    parent_item = _find_by_url(crawl_urls, item[0]["url"])

                    dict_item = {
                        "base_url": future_result["results"][0]["url"],
                        "response_time": future_result["response_time"],
                        "request_id": future_result["request_id"],
                        "results" : [
                            {
                                "url": future_result["results"][0]["url"],
                                "raw_content": clean_web_content(clean_html_and_entities(future_result["results"][0]["raw_content"]))
                            }
                        ]
                    }

                    results.append(dict_item)
                else:
                    print(f"Failed for url {future_result}")
            except Exception as e:
                print(f"Exception in url {str(e)}")
                raise e
    
    with open("mock_run/json_files/extract_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    return results

@tool
def get_news_content(crawl_urls: list[TavilyResultItem] = []):
    """
    Web search to get the content from the url. Select the tool based on config for web crawlling. 
    """
    active_crawl = web_crawl_config.active_web_crawl
    match active_crawl.name:
        case "tavily_crawl":
            return _crawl_url_list(crawl_urls=crawl_urls)
        case "tavily_extract":
            return _extract_from_urls(crawl_urls=crawl_urls)
        case _:
            return _extract_from_urls(crawl_urls=crawl_urls)
