from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

class GenrePrompts:
    @staticmethod
    def get_genre_prompt():
        system_temp = SystemMessagePromptTemplate.from_template(
        """You are an expert news editor. Based on the following news summary, assign the most appropriate genre from the list below:

        Genres: {genres}

        Task: Read the news summary carefully and return only the genre that best fits its content. 
        Do not explain your reasoning. Only respond with one of the genre labels from the list.""",
        input_variables=['genres'])

        human_temp = HumanMessagePromptTemplate.from_template(
            """
            Summarise the content:
            {content}
            """, input_variables=['content']
        )

        chat_prompt = ChatPromptTemplate.from_messages([system_temp, human_temp])

        return chat_prompt



