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
from student_app.prompts.academic_advisor_reformulations_prompts import prompt_reformulation_for_web_search
#from langchain_core.output_parsers import StrOutputParser

prompt_answering = prompt_reformulation_for_web_search
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
def LLM_profile_generation(prompt_answering: str, username: str, chat_id: str, university: str, school: str, major: str, minor: str, pro_exp: str):

    print("\n")
    print("\n")
    print(f"Profiling of the user")
    print(f"username: {username}, chat_id: {chat_id}, university: {university}, School: {school}, major: {major}, minor: {minor}, pro_exp: {pro_exp}")

    try:
        GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


        standalone_system_prompt = prompt_answering
        standalone_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", standalone_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                ("human", "{input}"),
            ]
        )

        profiling_generation = standalone_question_prompt | GROQ_LLM # | StrOutputParser()# fix incompatible type

        config = {"configurable": {"username":username}}
        response = profiling_generation.invoke({"prompt_answering": prompt_answering, "username": username, "chat_id": chat_id, "university": university, "school": school, "major": major, "minor": minor, "pro_exp": pro_exp}, config=config)

        return response.content
    except Exception as e:
        print(e)