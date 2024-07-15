# Importations et initialisations
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec

from dotenv import load_dotenv

from datetime import datetime

# Import AWS memory 
from database.dynamo_db.chat import AWSDynamoDBChatMessageHistory, get_table



# Load environment variables from .env file
load_dotenv()


# Class to create llm with memory from DynamoDB
class CreateLLMWithDynamoDBMemory(RunnableWithMessageHistory):

    # Constants
    MODEL_NAME = "llama3-70b-8192"
    GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)
    TABLE_NAME, TABLE_AWS = get_table("dev") # TODO: Change to "prod" when ready

    # Set the prompt for the assistant
    def set_prompting(self, prompt: str):
        self.prompt = prompt
        self.llm_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.prompt,
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    (
                        "user","{input}"
                    ),
                ]
            )
        return self.llm_prompt
    

    def get_dynamoDB_history(self, chat_id: str, username: str, course_id: str) -> AWSDynamoDBChatMessageHistory:
        return AWSDynamoDBChatMessageHistory(
            table=self.TABLE_AWS,
            chat_id=chat_id,
            # timestamp=datetime.now().isoformat(),
            course_id=course_id,
            username=username,
            table_name=self.TABLE_NAME,
            session_id=chat_id,
                    primary_key_name="chat_id",
                    key={
                        "chat_id": chat_id,
                        "timestamp": datetime.now().isoformat()
                        },
        )

    # Create the llm chain with history
    def create_llm_with_dynamoDB_memory(self):
        chain = self.llm_prompt | self.GROQ_LLM

        # Adding memory
        chain_with_memory = RunnableWithMessageHistory(
            chain,
            self.get_dynamoDB_history,
            input_messages_key="input",
            history_messages_key="chat_history",
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





    
