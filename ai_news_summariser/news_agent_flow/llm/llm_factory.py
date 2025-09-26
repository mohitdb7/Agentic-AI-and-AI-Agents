from news_agent_flow.llm import GeminiCrewLLM, OpenAICrewLLM, OpenAILangchainLLM, GeminiLangchainLLM
from news_agent_flow.configs import AppConfigModel

_active_llm = AppConfigModel.from_json_file("news_agent_flow/configs/agent_config.json").active_llm

class LLMFactory:
    
    @staticmethod
    def build_crew_llm():
        
        if _active_llm.name == OpenAICrewLLM.llm_model():
            return OpenAICrewLLM().get_llm()
        elif _active_llm.name == GeminiCrewLLM.llm_model():
            return GeminiCrewLLM().get_llm()
        else:
            return GeminiCrewLLM().get_llm()
        
    @staticmethod
    def build_langchain_llm():
        if _active_llm.name == OpenAICrewLLM.llm_model():
            return OpenAILangchainLLM().get_llm()
        elif _active_llm.name == GeminiCrewLLM.llm_model():
            return GeminiLangchainLLM().get_llm()
        else:
            return GeminiLangchainLLM().get_llm()