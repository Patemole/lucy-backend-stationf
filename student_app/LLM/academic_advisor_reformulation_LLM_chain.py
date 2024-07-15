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
from langchain_community.chat_message_histories.dynamodb import DynamoDBChatMessageHistory
import boto3
from database.dynamo_db.chat import AWSDynamoDBChatMessageHistory, get_table
from datetime import datetime
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec




# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

MODEL_NAME = "llama3-70b-8192"

### To modify depending on the table name where you want to store the memory 
TABLE_NAME = "DEV_Memory_academic_advisor"  

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



# Create the history for the memory
table_name, table_AWS = get_table("dev")
def get_dynamoDB_history(chat_id: str, username: str, course_id: str) -> AWSDynamoDBChatMessageHistory:
    return AWSDynamoDBChatMessageHistory(
        table=table_AWS,
        chat_id=chat_id,
        # timestamp=datetime.now().isoformat(),
        course_id=course_id,
        username=username,
        table_name=table_name,
        session_id=chat_id,
                primary_key_name="chat_id",
                key={
                    "chat_id": chat_id,
                    "timestamp": datetime.now().isoformat()
                    },
    )


# Fonction principale renommée
def LLM_chain_reformulation(content: str, chat_id: str, username: str, course_id):

    GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


    standalone_system_prompt = """
    Given a chat history: {history} and a follow-up question, rephrase the follow-up question to be a standalone question. \
    Do NOT answer the question, just reformulate it if needed, otherwise return it as is. \
    Only return the final standalone question with no preamble, postamble or explanation. \
    """
    standalone_question_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", standalone_system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    reformulation_chain = standalone_question_prompt | GROQ_LLM # | StrOutputParser()# fix incompatible type

    reformulation_chain_with_message_history = RunnableWithMessageHistory(
        reformulation_chain,
        get_dynamoDB_history,
        input_messages_key="input",
        history_messages_key="history",
        history_factory_config=[
            ConfigurableFieldSpec(
                id="chat_id",
                annotation=str,
                name="Chat ID",
                description="Unique identifier for the chat.",
                default="",
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="username",
                annotation=str,
                name="User Name",
                description="Unique name for the user.",
                default="",
                is_shared=True,
            ),
            ConfigurableFieldSpec(
                id="course_id",
                annotation=str,
                name="Course ID",
                description="Unique identifier for the course.",
                default="",
                is_shared=True,
            ),
        ],
    )

    config = {"configurable": {"chat_id": chat_id, "username":username, "course_id": course_id}}
    response = reformulation_chain_with_message_history.invoke({"input": content}, config=config)

    return response.content

    # #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
    # prompt_search_engine = ChatPromptTemplate.from_messages(
    #     [
    #         (
    #             "system",
    #             """Given the following conversation and a follow up question (the HumanMessage), rephrase the follow up question to be a standalone question, in its original language.

    #                 Chat History:
    #                 {chat_history}
    #                 Standalone question:
    #             """
    #         ),
    #         MessagesPlaceholder(variable_name="messages"),
    #     ]
    # )

    # chain = prompt_search_engine | GROQ_LLM

    # response = chain.invoke({"messages": [HumanMessage(content=content)], "chat_history": chat_history})

    # return response.content
        