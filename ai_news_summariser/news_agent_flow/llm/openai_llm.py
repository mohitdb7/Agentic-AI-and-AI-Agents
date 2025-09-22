from crewai import LLM
from langchain_openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv

load_dotenv()

class OpenAICrewLLM:
    """
    OpenAI LLM 
    """
    llm: LLM

    def __init__(self):
        self.llm = LLM(
            model=OpenAICrewLLM.llm_model(),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")  # or correct param name
        )

    def get_llm(self) -> LLM:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        "openai/gpt-4"


class OpenAILangchainLLM:
    """
    OpenAI Langchain AI
    """

    llm: OpenAI
    def __init__(self):
        self.llm = OpenAI(
            model=OpenAILangchainLLM.llm_model(),
            api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_llm(self):
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        "gpt-4"