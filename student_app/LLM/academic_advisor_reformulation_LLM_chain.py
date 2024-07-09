# Importations et initialisations
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
import os
import time
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.chat_message_histories import ChatMessageHistory

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

MODEL_NAME = "llama3-70b-8192"

# Fonction pour mesurer le temps d'exécution
def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        return result
    return wrapper





# Fonction principale renommée
def LLM_chain_reformulation(content: str, chat_history):

    GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


    #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
    prompt_search_engine = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Given the following conversation and a follow up question (the HumanMessage), rephrase the follow up question to be a standalone question, in its original language.

                    Chat History:
                    {chat_history}
                    Standalone question:
                """
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt_search_engine | GROQ_LLM

    response = chain.invoke({"messages": [HumanMessage(content=content)], "chat_history": chat_history})

    return response.content
        