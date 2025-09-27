from typing import TypedDict
from news_agent_flow.models import TavilyResponse, OutputGenreSummarisedResponseModel
from news_agent_flow.models import TavilyCrawlListModel, GenreSumarisedModel, SummarisedNewsArticle

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