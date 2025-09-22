from tavily import TavilyClient
from dotenv import load_dotenv
import os

from models import TavilyResponse
import json
from pathlib import Path

import torch
from transformers import pipeline

from langchain.chat_models import init_chat_model


load_dotenv()


client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
# tavily_response = client.search("Get me the latest news Tech, Sports and Politics", 
#                                 max_results=10, 
#                                 search_depth="advanced", 
#                                 # optional filters:
#                                 time_range="week")

# #     # Step 1: Write to file
filepath = "tavily_AI_response.json"
# with open(filepath, "w", encoding="utf-8") as f:
#     json.dump(tavily_response, f, indent=4)

# print(f"Response written to {tavily_response}")

# Step 2: Read back & parse into class
# response = TavilyResponse(**tavily_response)



# response = TavilyResponse.from_json_file(filepath)  # Parse the response JSON into TavilyResponse object

# print(len(response.results))  # Print the response to verify the output

# crawl_path = "tavily_AI_crawl.json"
# crawl_result_list = []
# news_summary = []
# for i, news in enumerate(response.results):
#     crawl_result = client.crawl(news.url, instructions=f"find the information on {news.title}", max_breadth=1, max_depth=1)

#     # crawl_result = {}
#     # file_path = Path(crawl_path)
#     # with file_path.open("r", encoding="utf-8") as f:
#     #     crawl_result = json.load(f)[i]
#     print("----"*50)
#     print(crawl_result["base_url"])
#     print("----"*50)

#     summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
#     summary = summarizer(crawl_result["results"][0]["raw_content"][:10000],
#                             max_length=1000,  # increase this to get a longer summary
#                             min_length=150,  # ensure it's not too short
#                             do_sample=False)[0]['summary_text']

#     print("****"*50)
#     print(summary)
#     print("****"*50)

#     crawl_result_list.append(crawl_result)

#     news_summary.append({
#         "url": news.url,
#         "title": news.title,
#         "summary": summary
#     })
# with open("tavily_AI_crawl.json", "w", encoding="utf-8") as f:
#     json.dump(crawl_result_list, f, indent=4)

# with open("tavily_AI_Summary.json", "w", encoding="utf-8") as f:
#     json.dump(news_summary, f, indent=4)


### Analyse the Genere of this model
with open("tavily_AI_Summary.json", "r", encoding="utf-8") as f:
    news_summary_from_file = json.load(f)

# for i, news_summary in enumerate(news_summary_from_file):
#     # ----- 1. Sentiment Analysis -----
#     sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
#     sentiment = sentiment_pipeline(news_summary["summary"])
#     print("****"*50)
#     print(news_summary["summary"])
#     print("Sentiment:", sentiment)
#     print("****"*50)

# print("####"*50)
# print("####"*50)
### Analyse the Genre 
# genre_summary = {}
# for i, news_summary in enumerate(news_summary_from_file):
#     # ----- 2. Text Classification -----
#     candidate_labels = ["Politics", "Sports", "Business", "Technology", "Science", "Health", "Entertainment", "Crime", "World"]

#     genre_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    
#     assert isinstance(news_summary["summary"], str), "Input must be a string"
#     assert isinstance(candidate_labels, list), "Candidate labels must be a list of strings"

#     genre = genre_classifier(news_summary["summary"], candidate_labels=candidate_labels)

#     if genre_summary.get(genre["labels"][0]):
#         genre_summary[genre["labels"][0]].append(news_summary["summary"])
#     else:
#         genre_summary[genre["labels"][0]] = [news_summary["summary"]]

#     print("****"*50)
#     print(news_summary["summary"])
#     print("****")
#     print("Genre Distribution:", genre["labels"][:2], genre["scores"][:2])
#     print("****"*50)

# genre_summary_path = "tavily_AI_Genre_Summary.json"
# with open(genre_summary_path, "w", encoding="utf-8") as f:
#     json.dump(genre_summary, f, indent=4)
# print(f"Genre summary written to {genre_summary_path}")


### Summary with LLM
# genre_summary = {}
# for i, news_summary in enumerate(news_summary_from_file):
#     genres = [
#         "Politics", "Sports", "Business", "Technology", "Science", "Health",
#         "Entertainment", "Crime", "World", "Environment", "Economy",
#         "Culture", "Education", "Law", "Military", "Religion",
#         "Opinion", "Travel", "AI & Emerging Tech", "Local News"
#     ]
#     llm = init_chat_model("google_genai:gemini-2.0-flash")
#     prompt_for_summary = """You are an expert news editor. Based on the following news summary, assign the most appropriate genre from the list below:

#     Genres: {genres}

#     Task: Read the news summary carefully and return only the genre that best fits its content. 
#     Do not explain your reasoning. Only respond with one of the genre labels from the list.

#     News Summary:
#     {news_summary}"""
#     news_genre = llm.invoke(prompt_for_summary.format(genres=",".join(genres), news_summary=news_summary["summary"]))
#     print("**\n**", news_summary["summary"], "**\n**", news_genre.content, "**\n**")

#     if genre_summary.get(news_genre.content):
#         genre_summary[news_genre.content].append({"url": news_summary["url"], "summary":news_summary["summary"]})
#     else:
#         genre_summary[news_genre.content] = [{"url": news_summary["url"], "summary":news_summary["summary"]}]
    
# with open("tavily_AI_Genre_Summary.json", "w", encoding="utf-8") as f:
#     json.dump(genre_summary, f, indent=4)
# print(f"Genre summary written to tavily_AI_Genre_Summary.json")


with open("tavily_AI_Genre_Summary.json", "r", encoding="utf-8") as f:
    genre_summary_from_file = json.load(f)
llm = init_chat_model("google_genai:gemini-2.0-flash")
final_summarised_genre = {}
for genre, summaries in genre_summary_from_file.items():
    print("####"*20)
    print(f"Genre: {genre}, Number of articles: {len(summaries)}")

    numbered_news = [f"News {i+1}: {article["summary"]}" for i, article in enumerate(summaries)]
    
    # Join them with double newlines
    joined_news = "\n\n".join(numbered_news)

    # Create the final prompt
    prompt = f"""
    You are an expert news editor. Your task is to read a list of brief news summaries and merge them into one clear, concise, and well-written summary. 
    Eliminate any numbering or references to individual items (e.g., "News 1", "News 2") and remove any repeated or irrelevant information. 
    Ensure the final summary flows naturally as a single, coherent paragraph that accurately reflects the key points from all the items.

    Input (list of news summaries):
    {joined_news}

    Output:
    A concise, unified summary that combines all key information into a single paragraph, written in a neutral, journalistic tone."""

    print("****"*20)
    # print("Prompt for summarization:")
    # print(prompt)
    # print("****"*20)

    result = llm.invoke(prompt)
    print(f"Summary: {result.content}")
    final_summarised_genre[genre] = result.content

with open("tavily_AI_Final_Summarised_Genre.json", "w", encoding="utf-8") as f:
    json.dump(final_summarised_genre, f, indent=4)
print(f"Final summarised genre written to tavily_AI_Final_Summarised_Genre.json")



    