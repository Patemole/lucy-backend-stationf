from typing import Any, Coroutine, Dict, List
from third_party_api_clients.dynamo_db.dynamo_db_client import DynamoDBClient
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import time
from functools import wraps
from datetime import datetime
from langchain_community.chat_message_histories.dynamodb import DynamoDBChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage 
import logging

logger = logging.getLogger(__name__)


#table = DynamoDBClient().client.Table("PROD_chat")
def get_table(table = "dev" or "prod"):
    if table == "prod":
        print("No access to prod table in DynamoDB")
        return None
    elif table == "dev":
        table_AWS = DynamoDBClient().client.Table("DEV_Memory_academic_advisor")
    return table_AWS


'''
async def get_chat_history(chat_id: str):
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print(f"Attempting to retrieve chat history for chat_id: {chat_id}")
    try:
        response = table.query(
            KeyConditionExpression='chat_id = :value',
            ExpressionAttributeValues={':value': chat_id}
        )
        items = response.get('Items', [])
        print(f"Retrieved {len(items)} items from chat history.")
        return items
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []
'''

# Définir le décorateur
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

'''
@timing_decorator
async def get_chat_history(chat_id: str):
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print(f"Attempting to retrieve chat history for chat_id: {chat_id}")
    try:
        response = table.query(
            KeyConditionExpression='chat_id = :chat_id',
            ExpressionAttributeValues={':chat_id': chat_id},
            ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
        )
        items = response.get('Items', [])
        print(f"Retrieved {len(items)} items from chat history.")
        return items
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []
'''

@timing_decorator
async def get_chat_history(chat_id: str):
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print(f"Attempting to retrieve chat history for chat_id: {chat_id}")
    try:
        response = table.query(
            KeyConditionExpression='chat_id = :chat_id',
            ExpressionAttributeValues={':chat_id': chat_id},
            ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
        )
        items = response.get('Items', [])
        print(f"Retrieved {len(items)} items from chat history.")
        
        # Ne retourner que le username et le body
        filtered_items = [{'username': item['username'], 'body': item['body']} for item in items]
        
        return filtered_items
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []
    
@timing_decorator
async def store_message_async(
        chat_id: str, 
        course_id: str, 
        message_body: str, 
        #username: str = "TAI",
        username: str,
        documents: List[Dict[str, Any]] = []):
    print(f"Attempting to store message for chat_id: {chat_id}, course_id: {course_id}, username: {username}")
    try:
        # Insert the item into DynamoDB
        args = {
            'message_id': str(uuid.uuid4()),
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'course_id': course_id,
            'body': message_body,
            'username': username
        }
        if username == "TAI" and documents:
            args['documents'] = documents
        table.put_item(Item=args)
        print(f"Message stored successfully with message_id: {args['message_id']}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into chat history: {error_code} - {error_message}")
    






class AWSDynamoDBChatMessageHistory(DynamoDBChatMessageHistory, BaseChatMessageHistory):

    def __init__(self, 
                 # New class
                 table,
                 chat_id: str, 
                 course_id: str, 
                 username: str, 
                 # Super class (DynamoDBChatMessageHistory)
                 table_name: str, 
                 session_id: str, 
                 primary_key_name: str, 
                 attributes: dict = None,
                 key: dict = None, 
                 ttl: int = None):

        # Variables taken from the class DynamoDBChatMessageHistory
        super().__init__(table_name=table_name, session_id=session_id, primary_key_name=primary_key_name, key=key, ttl=ttl)

        # Additional variables to the class DynamoDBChatMessageHistory
        self.attributes = attributes
        self.table = table
        self.chat_id = chat_id
        self.course_id = course_id
        self.username = username

    
    def get_chat_history(self):
        print("\n")
        print("\n")
        print(f"Attempting to retrieve chat history for chat_id: {self.chat_id}")
        try:
            response = self.table.query(
                KeyConditionExpression='chat_id = :chat_id',
                ExpressionAttributeValues={':chat_id': self.chat_id},
                ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
            )
            items = response.get('Items', [])
            print(f"Retrieved {len(items)} items from chat history.")

            return items
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Error querying chat history: {error_code} - {error_message}")
            return []
        
    
    def store_message(self,
                      message: BaseMessage,
                      documents: List[Dict[str, Any]] = []):
        print("\n")
        print("\n")
        print(f"Attempting to store message for chat_id: {self.chat_id}, course_id: {self.course_id}, username: {self.username}")
        try:
            # Insert the item into DynamoDB
            args = {
                'message_id': str(uuid.uuid4()),
                'chat_id': self.chat_id,
                'timestamp': datetime.now().isoformat(),
                'course_id': self.course_id,
                'body': message.content,
                'username': self.username
            }

            if self.username == "TAI" and documents:
                args['documents'] = documents

            print("\n\nThis is a message from: ", message.type)

            if message.type != "human":
                args['username'] = "Lucy"

            self.table.put_item(Item=args)
            print(f"Message stored successfully with message_id: {args['message_id']}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Error inserting message into chat history: {error_code} - {error_message}")
        



    @property
    def messages(self):
        items = self.get_chat_history()
        messages = [items[i]['body'] for i in range(len(items))]
        return messages
    

    def add_message(self, message: BaseMessage) -> None:
        """Add a Message object to the store.

        Args:
            message: A BaseMessage object to store.
        """
        self.store_message(message)

        



