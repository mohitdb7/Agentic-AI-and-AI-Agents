from crewai import LLM

from langchain_google_genai import ChatGoogleGenerativeAI

import os
from dotenv import load_dotenv

load_dotenv()

class GeminiCrewLLM:
    """
    Gemini LLM 
    """
    llm: LLM

    def __init__(self):
        self.llm = LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")  # or correct param name
        )

    def get_llm(self) -> LLM:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        "gemini/gemini-2.0-flash"


class GeminiLangchainLLM:
    """
    Gemini LLM 
    """
    llm: ChatGoogleGenerativeAI

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            api_key=os.getenv("GOOGLE_API_KEY")
            )

    def get_llm(self) -> ChatGoogleGenerativeAI:
        return self.llm
    
    @staticmethod
    def llm_model() -> str:
        "gemini-2.0-flash"