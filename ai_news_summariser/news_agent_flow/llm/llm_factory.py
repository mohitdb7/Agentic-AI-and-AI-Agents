from news_agent_flow.llm import GeminiCrewLLM, OpenAICrewLLM, OpenAILangchainLLM, GeminiLangchainLLM

class LLMFactory:
    
    @staticmethod
    def build_crew_llm(llm_param):
        if llm_param == OpenAICrewLLM.llm_model():
            return OpenAICrewLLM().get_llm()
        elif llm_param == GeminiCrewLLM.llm_model():
            return GeminiCrewLLM().get_llm()
        else:
            return GeminiCrewLLM().get_llm()
        
    @staticmethod
    def build_langchain_llm(llm_param):
        if llm_param == OpenAICrewLLM.llm_model():
            return OpenAILangchainLLM().get_llm()
        elif llm_param == GeminiCrewLLM.llm_model():
            return GeminiLangchainLLM().get_llm()
        else:
            return GeminiLangchainLLM().get_llm()