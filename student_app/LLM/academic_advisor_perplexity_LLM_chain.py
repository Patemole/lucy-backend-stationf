import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatPerplexity
from langchain_community.chat_message_histories import ChatMessageHistory
from functools import wraps
from student_app.database.dynamo_db.chat import AWSDynamoDBChatMessageHistory, TABLE_NAME, table
from datetime import datetime
from langchain_core.runnables import ConfigurableFieldSpec


load_dotenv()

PPLX_API_KEY = os.getenv("PPLX_API_KEY")


class PplxChatCompletion:

    def __init__(self):
        self.store = {}  # Local memory
        self.model = "llama-3-sonar-small-32k-online"  # Default model
        self.table_name = TABLE_NAME
        self.table_AWS = table

    def change_model(self, model: str):
        available_models = [
            "llama-3-sonar-small-32k-chat",
            "llama-3-sonar-small-32k-online",
            "llama-3-sonar-large-32k-chat",
            "llama-3-sonar-large-32k-online",
            "llama-3-8b-instruct",
            "llama-3-70b-instruct",
            "mixtral-8x7b-instruct"
        ]
        if model not in available_models:
            raise ValueError(f"Model must be one of: {available_models}")
        self.model = model
        print(f"You are using the model: {self.model}")

    def pplx_llm(self):
        llm = ChatPerplexity(
            model=self.model,
            temperature=0,
            max_tokens=512
        )
        return llm

    def get_AWS_history(self, chat_id, course_id, username) -> AWSDynamoDBChatMessageHistory:
        return AWSDynamoDBChatMessageHistory(
            table=self.table_AWS,
            chat_id=chat_id,
            course_id=course_id,
            username=username,
            table_name=self.table_name,
            session_id=chat_id,
                primary_key_name="chat_id",
                key={
                    "chat_id": chat_id,
                    "timestamp": datetime.now().isoformat()
                    },
        )

    def set_prompt(self, system_prompt: str, user_prompt: str):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Hello Lucy, can you help me with the different enquiries I have at {university}?"),
            ("assistant", "Hello, I will be glad to help you with any questions you have about your student life at {university}."),
            ("user", "How do I register to classes ?"),
            ("assistant", """To register for classes at UPenn, follow these steps:
             1. **Log In**: Go to Path@Penn and log in with your PennKey and password.
             2. **Discover & Research Courses**: Use the search functions to find courses. You can read course descriptions and view prerequisites.
             3. **Add Courses to Cart**: Select the desired courses and add them to your cart.
             4. **Request Courses**: During the Advance Registration period, submit your course requests. All requests are batch processed after the period ends, so timing within the period does not affect priority.
             5. **Confirm Registration**: After course requests are processed, confirm your schedule in Path@Penn. Make any necessary adjustments during the Course Selection period, also known as Add/Drop/Swap.
             For detailed steps and tips, refer to [Penn Student Registration & Financial Services](https://srfs.upenn.edu/registration) and the [College of Arts & Sciences](https://www.college.upenn.edu/registration) pages.
             **Sources:**
             - [Penn Student Registration & Financial Services](https://srfs.upenn.edu/registration)
             - [College of Arts & Sciences](https://www.college.upenn.edu/registration)
             **Related Questions:**
             - What is the deadline to drop a course for the fall 2024?
             - How do I get a copy of my transcript?
             - Is there any compulsory courses?"""),
            MessagesPlaceholder("messages", n_messages=2),
            # MessagesPlaceholder("messages"),
            ("user", user_prompt),
        ])

    def create_chain_with_memory(self):
        if not hasattr(self, 'prompt') or self.prompt is None:
            raise SyntaxError("You need to set the prompt with set_prompt function.")
        
        chain = self.prompt | self.pplx_llm()
        chain_with_memory = RunnableWithMessageHistory(
            chain,
            get_session_history=self.get_AWS_history,
            input_messages_key='input',
            history_messages_key='messages',
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="chat_id",
                    annotation=str,
                    name="Chat ID",
                ),
                ConfigurableFieldSpec(
                    id="username",
                    annotation=str,
                    name="Username",
                ),
                ConfigurableFieldSpec(
                    id="course_id",
                    annotation=str,
                    name="Course ID",
                ),
            ],
        )
        return chain_with_memory

    def stream_llm(self, content: dict, config):
        llm_chain = self.create_chain_with_memory()
        for chunk in llm_chain.stream(content, config=config):
            yield chunk.content + "|"

    def invoke_llm(self, content: dict, config):
        llm_chain = self.create_chain_with_memory()
        response = llm_chain.invoke(content, config)
        print(response.content)
        return response

def LLM_chain_perplexity(content, prompt_answering, student_profile, chat_id, university, course_id, username):
    """
    Generate a perplexity chain for the given content using the provided prompt, student profile, chat ID, university, course ID, and username.

    Args:
        content (str): The content to generate the perplexity chain for.
        prompt_answering (str): The prompt to use for answering the content.
        student_profile (str): The student profile to use in the perplexity chain.
        chat_id (str): The chat ID to use in the perplexity chain configuration.
        university (str): The university to use in the perplexity chain content.
        course_id (str): The course ID to use in the perplexity chain configuration.
        username (str): The username to use in the perplexity chain configuration.

    Yields:
        str: The generated perplexity chain chunk.
    """
    pplx = PplxChatCompletion()

    human = "{input}. Please only search information on this domain: site:upenn.edu. Please also provide the useful links to find the information and some related questions that could be useful to me."
    
    pplx.set_prompt(prompt_answering, human)

    chain = pplx.create_chain_with_memory()
    
    content_dict = {"input": content, "university": university, "student_profile": student_profile}
    config = {"configurable": {"chat_id": chat_id, "username": username, "course_id": course_id}}

    for r in chain.stream(input=content_dict, config=config):
        # print(chunk, end='')
        yield r.content + "|"

    # yield from pplx.stream_llm(content=content_dict, config=config)

    # for chunk in pplx.stream_llm(content=content_dict, config=config):
    #     print(chunk, end='')
    #     yield chunk
