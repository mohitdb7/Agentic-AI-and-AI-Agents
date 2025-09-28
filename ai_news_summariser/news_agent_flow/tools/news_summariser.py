from crewai.tools import tool
from transformers import pipeline

from bs4 import BeautifulSoup
import re

from news_agent_flow.models import SummarisedNewsArticle

from concurrent.futures import ThreadPoolExecutor, as_completed
from news_agent_flow.prompts import LangChainPrompts
from news_agent_flow.llm import LLMFactory
from news_agent_flow.configs import AppConfigModel

import os
from dotenv import load_dotenv

load_dotenv()

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

def summarise_news_article_with_cnn(news_content):
    """
    Summaries the content using the summarization transformers. Best to summarising the text
    """
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summary = summarizer(news_content["content"],
                            max_length=1000,  # increase this to get a longer summary
                            min_length=150,  # ensure it's not too short
                            do_sample=False)[0]['summary_text']
    return {
        "url": news_content["url"],
        "title": news_content["title"],
        "summary": summary
    }


class NewsSummaryChain:
    def _get_chain_summarise_news_article(self):
        prompt = LangChainPrompts.get_individual_news_summariser_prompt()
        llm = LLMFactory.build_langchain_llm()

        chain_exec = ({
            "news_item": lambda x: x["content"]
            }
            |prompt
            |llm
            |{"summary": lambda x: x.content}
            )
        
        return chain_exec
    
    def summarise_news_article(self, news_content):
        content = news_content["content"]
        chain = self._get_chain_summarise_news_article()

        result = chain.invoke({
            "content": content
            })
        
        return {
            "url": news_content["url"],
            "title": news_content["title"],
            "summary": result["summary"]
            }

def summarise_news_content(news_content):
    match app_config.active_summarizer.name:
        case "llm":
            return NewsSummaryChain().summarise_news_article(news_content=news_content)
        case "facebook_cnn":
            summarise_news_article_with_cnn(news_content=news_content)
        case _:
            summarise_news_article_with_cnn(news_content=news_content)

@tool
def summarise_news_list(news_list) -> list["SummarisedNewsArticle"]:
    """
    Can summarise the list of news articles

    Args: News Article List

    Return: list[SummarisedNewsArticle]
    """

    news_summary_dict = [ summarise_news_content({
                        "url": news_article["url"],
                        "title": news_article["title"],
                        "content": news_article["content"][:10000]
                    }) for news_article in news_list]
    news_summary_list = [SummarisedNewsArticle(**item) for item in news_summary_dict]
    return news_summary_list

    


