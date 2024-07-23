import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatPerplexity
from langchain_community.chat_message_histories import ChatMessageHistory
from functools import wraps

load_dotenv()

PPLX_API_KEY = os.getenv("PPLX_API_KEY")


class PplxChatCompletion:

    def __init__(self):
        self.store = {}  # Local memory
        self.model = "llama-3-sonar-small-32k-online"  # Default model

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

    def get_local_memory(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def reset_local_memory(self):
        self.store = {}

    def set_prompt(self, system_prompt: str, user_prompt: str):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("messages", n_messages=2),
            ("user", user_prompt),
        ])

    def create_chain_with_memory(self):
        if not hasattr(self, 'prompt') or self.prompt is None:
            raise SyntaxError("You need to set the prompt with set_prompt function.")
        
        chain = self.prompt | self.pplx_llm()
        chain_with_memory = RunnableWithMessageHistory(
            chain,
            get_session_history=self.get_local_memory,
            input_messages_key='input',
            history_messages_key='messages'
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
    pplx = PplxChatCompletion()

    human = content
    pplx.set_prompt(prompt_answering, human)
    
    content_dict = {"input": content, "university": university, "student_profile": student_profile}
    config = {"configurable": {"session_id": chat_id}}

    for chunk in pplx.stream_llm(content=content_dict, config=config):
        print(chunk, end='')
        yield chunk
