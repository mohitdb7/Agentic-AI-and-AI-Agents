from crewai import LLM
from news_agent_flow.configs import AppConfigModel
from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv

_gemini_llm = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json").get_llm_by_name("gemini")

load_dotenv()

class GeminiCrewLLM:
    """
    Gemini LLM 
    """
    llm: LLM

    def __init__(self):
        self.llm = LLM(
            model=f"{_gemini_llm.model.crew_ai}",
            temperature=_gemini_llm.temprature,
            api_key=os.getenv("GOOGLE_API_KEY")  # or correct param name
        )

    def get_llm(self) -> LLM:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        f"{_gemini_llm.name}"


class GeminiLangchainLLM:
    """
    Gemini LLM 
    """
    llm: ChatGoogleGenerativeAI

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=f"{_gemini_llm.model.langchain}",
            temperature=_gemini_llm.temprature,
            api_key=os.getenv("GOOGLE_API_KEY")
            )

    def get_llm(self) -> ChatGoogleGenerativeAI:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        f"{_gemini_llm.name}"