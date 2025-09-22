from crewai.tools import tool
from transformers import pipeline

from bs4 import BeautifulSoup
import re

from news_agent_flow.models import SummarisedNewsArticle

from concurrent.futures import ThreadPoolExecutor, as_completed

import os
from dotenv import load_dotenv

load_dotenv()

def summarise_news_article(news_content):
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

@tool
def summarise_news_list(news_list) -> list["SummarisedNewsArticle"]:
    """
    Can summarise the list of news articles

    Args: News Article List

    Return: list[SummarisedNewsArticle]
    """
    news_summary_dict = [ summarise_news_article({
                        "url": news_article["url"],
                        "title": news_article["title"],
                        "content": news_article["content"][:10000]
                    }) for news_article in news_list]
    news_summary_list = [SummarisedNewsArticle(**item) for item in news_summary_dict]
    return news_summary_list

    


