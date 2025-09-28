from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

class LangChainPrompts:
    @staticmethod
    def get_genre_prompt():
        system_temp = SystemMessagePromptTemplate.from_template(
            """You are an experienced news editor.
            Your task is to classify a news summary into the most appropriate genre from the list below:
            Genres: {genres}
            
            Instructions:
            - Read the summary carefully.
            - Choose **only one** genre label from the list that best describes the content.
            - Respond **only** with the selected genre label. Do **not** include any explanation or additional text.
            """, input_variables=['genres'])

        human_temp = HumanMessagePromptTemplate.from_template(
            """News Summary:
            {content}""", input_variables=['content'])

        chat_prompt = ChatPromptTemplate.from_messages([system_temp, human_temp])

        return chat_prompt
    
    @staticmethod
    def get_individual_news_summariser_prompt():
        system_temp = SystemMessagePromptTemplate.from_template(
            """You are a professional news editor.
            
            Your task is to summarise a single news article or snippet into a brief, accurate, and readable summary.
            
            Guidelines:
            - Preserve all essential facts.
            - Eliminate unnecessary adjectives, opinions, or speculation.
            - Use a neutral, journalistic tone.
            - Limit the summary to 1-3 sentences."""
        )

        human_temp = HumanMessagePromptTemplate.from_template(
            """News Item:
            {news_item}""",
            input_variables=['news_item']
        )

        chat_prompt = ChatPromptTemplate.from_messages([system_temp, human_temp])

        return chat_prompt


