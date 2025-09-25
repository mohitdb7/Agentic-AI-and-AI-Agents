from crewai import Agent, Task, Crew
from crewai import LLM
import os
from dotenv import load_dotenv
import json

from news_agent_flow.llm import LLMFactory

from news_agent_flow.models import GenreSumarisedModel, OutputGenreSummarisedResponseModel

from news_agent_flow.prompts import summariser_task_prompts, summariser_agent_prompts

load_dotenv()

class NewsSummariser:
    llm: LLM

    def __init__(self):
        self.llm = LLMFactory.build_crew_llm()

    def news_summariser(self, news_content, genre):

        summariser_agent = Agent(
            role="News Summariser",
            llm=self.llm,
            goal=summariser_agent_prompts["goal"],
            backstory=summariser_agent_prompts["backstory"],
            # tools=[summarise_news],
            verbose=False
        )


        news_summary_task = Task(
            description=summariser_task_prompts["description"],
            agent=summariser_agent,
            expected_output=summariser_task_prompts["expected_output"]
        )

        crew = Crew(
            tasks=[news_summary_task],
            agents=[summariser_agent],
            verbose=False
        )

        result = crew.kickoff(inputs={
            "genre": genre,
            "joined_news": news_content
            })
        
        return result
    
    def combine_summary(self, summaries) -> str:
        if isinstance(summaries, str):
            return summaries
        elif isinstance(summaries, list):
            return ". ".join([summary.summary for summary in summaries])
        else:
            return ""
        
    def summarise_genre_news(self, news_genre_summary: GenreSumarisedModel) -> OutputGenreSummarisedResponseModel:
        serializeable = {}
        for genre, summaries in news_genre_summary.categories.items():
            full_summary = self.combine_summary(summaries=summaries)
            summary_result = self.news_summariser(full_summary, genre)

            serializeable[genre] = {"final_summary" : str(summary_result), 
                                    "all_summary" : [summary.model_dump() for summary in summaries]}
        
        result = OutputGenreSummarisedResponseModel(**serializeable)
        return result


        


