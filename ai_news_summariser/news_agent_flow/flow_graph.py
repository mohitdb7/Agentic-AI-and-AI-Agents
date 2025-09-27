from langgraph.graph import StateGraph, START, END
from news_agent_flow.models import NewsAgentState
from news_agent_flow.nodes import search_web_for_news, crawl_news_content, assign_genre, final_genre_summary, summarise_news
from news_agent_flow.utils import cleanup_old_logs
from news_agent_flow.configs import AppConfigModel

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

# Graph creation
def create_news_agent_with_final_summary_flow():
    # Run cleanup before executing
    cleanup_old_logs(days=app_config.log_expiry.days, hours=app_config.log_expiry.hours, minutes=app_config.log_expiry.minutes)

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

    return graph.compile()

def create_news_agent_with_news_summary_flow():
    # Run cleanup before executing
    cleanup_old_logs(days=app_config.log_expiry.days, hours=app_config.log_expiry.hours, minutes=app_config.log_expiry.minutes)

    graph = StateGraph(state_schema=NewsAgentState)

    graph.add_node("search_the_web", search_web_for_news)
    graph.add_node("crawl_the_news", crawl_news_content)
    graph.add_node("summarise_the_news", summarise_news)
    # graph.add_node("assign_genre", assign_genre)
    # graph.add_node("final_genre_summary", final_genre_summary)

    graph.add_edge(START, "search_the_web")
    # Router nodes
    graph.add_conditional_edges("search_the_web",  lambda s: END if s.get("has_error") else "crawl_the_news")
    graph.add_conditional_edges("crawl_the_news", lambda s: END if s.get("has_error") else "summarise_the_news")
    graph.add_edge("summarise_the_news", END)
    # graph.add_conditional_edges("assign_genre", lambda s: END if s.get("has_error") else "final_genre_summary")
    # graph.add_edge("final_genre_summary", END)

    return graph.compile()

# Invoke the graph
# graph = create_news_agent_flow()
# output = graph.invoke({"query": "latest news on AI advancements in the last week"})
# print("Graph completed")
# print(output)