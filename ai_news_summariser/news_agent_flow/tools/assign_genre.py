from news_agent_flow.prompts import LangChainPrompts
from news_agent_flow.llm import LLMFactory
from news_agent_flow.models import SummarisedNewsArticle, GenreSumarisedModel
from news_agent_flow.configs import AppConfigModel

app_config = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json")

class GenreManager:
    def parse_genre(self, genres):
        if isinstance(genres, list):
            return ", ".join(genres)
        elif isinstance(genres, str):
            return genres
        else:
            return ", ".join(app_config.genre_list)
    def assign_genre(self):
        prompt = LangChainPrompts.get_genre_prompt()
        
        llm = LLMFactory.build_langchain_llm()

        chain_exec = (
                        {
                            "genres": lambda x: x["genres"].upper(),
                            "content": lambda x: x["content"]
                        }
                        | prompt
                        | llm   
                        | {"genre": lambda x: x.content}  # Extract content from AI response
                        )

        return chain_exec
    
    def get_genre(self, genre: list[str], content):
        genre_str = self.parse_genre(genres=genre)
        chain = self.assign_genre()

        result = chain.invoke({
            "genres" : genre_str,
            "content" : content
        })

        return result

    def assign_genre_to_summaries(self, news_summaries: list[SummarisedNewsArticle]) -> GenreSumarisedModel:
        genres = app_config.genre_list

        genre_str = self.parse_genre(genres)

        genre_summary = {}


        for news_summary in news_summaries:
            result = self.get_genre(genre=genre_str, content=news_summary.summary)
            if genre_summary.get(result["genre"]):
                genre_summary[result["genre"]].append({
                    "url": news_summary.url,
                    "title": news_summary.title,
                    "summary": news_summary.summary
                })
            else:
                genre_summary[result["genre"]] = [{
                    "url": news_summary.url,
                    "title": news_summary.title,
                    "summary": news_summary.summary
                }]
        
        result = GenreSumarisedModel(categories=genre_summary)
        return result