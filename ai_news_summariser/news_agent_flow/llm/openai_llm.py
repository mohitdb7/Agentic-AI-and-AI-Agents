from crewai import LLM
from langchain_openai import OpenAI
from news_agent_flow.configs import AppConfigModel

import os
from dotenv import load_dotenv

load_dotenv()

_openai_llm = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json").get_llm_by_name("open_ai")

class OpenAICrewLLM:
    """
    OpenAI LLM 
    """
    llm: LLM

    def __init__(self):
        self.llm = LLM(
            model=f"{_openai_llm.model.crew_ai}",
            temperature=_openai_llm.temprature,
            api_key=os.getenv("OPENAI_API_KEY")  # or correct param name
        )

    def get_llm(self) -> LLM:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        f"{_openai_llm.name}"


class OpenAILangchainLLM:
    """
    OpenAI Langchain AI
    """

    llm: OpenAI
    def __init__(self):
        self.llm = OpenAI(
            model=f"{_openai_llm.model.langchain}",
            api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_llm(self):
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        f"{_openai_llm.name}"