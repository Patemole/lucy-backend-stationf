from typing import Any, Dict, List
from third_party_api_clients.dynamo_db.dynamo_db_client import DynamoDBClient
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import time
from functools import wraps
from dotenv import load_dotenv
import boto3
import os
import json
from typing import Optional
from student_app.prompts.perplexity_pydantic_prompt_checker import Message, Chat



load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')


# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name="eu-west-3",
    #region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#ADD AN ENVIRONMENT VARIABLE FOR TABLE
table = dynamodb.Table("dev_chat_academic_advisor")
#table = dynamodb.Table("prod_preprod_chat_academic_advisor")
#table = dynamodb.Table("prod_prod_chat_academic_advisor")



'''
load_dotenv()

#NEED TO CHANGE THE NAME OF THE TABLE 
table = DynamoDBClient().client.Table("MVP_chat_academic_advisor")
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

        # Generate a unique message_id
        message_id = str(uuid.uuid4())

        # Insert the item into DynamoDB
        args = {
            'message_id': message_id,
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

        # Return the message_id
        return message_id
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into chat history: {error_code} - {error_message}")
        return None

    

@timing_decorator
async def get_messages_from_history(chat_id: str, n: Optional[int] = None) -> Chat:

    filtered_items = await get_chat_history(chat_id)

    # Ensure of getting even number of messages (user + lucy)
    if n is None :
        items = filtered_items  # Get all messages
    elif n % 2 != 0:  # If n is odd
        n += 1  # Make it even
        items = filtered_items[-n:]
    else:  # If n is even
        items = filtered_items[-n:]

    # messages = [
    #     {"role": "assistant" if item['username'] == "Lucy" else "user", "content": item['body']}
    #     for item in items
    # ]

    # Pydantic
    chat = Chat(chat=[Message(role="assistant" if item['username'] == "Lucy" else "user", content=item['body']) for item in items])
    chat_json = chat.model_dump()
    formated_chat = chat_json["chat"]

    print(f"Retrieved {len(formated_chat)} messages from chat history.")
    return formated_chat


@timing_decorator
async def get_chat_history_as_text(chat_id: str):
    try:
        response = table.query(
            KeyConditionExpression='chat_id = :chat_id',
            ExpressionAttributeValues={':chat_id': chat_id},
            ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
        )
        items = response.get('Items', [])
        # print(f"Retrieved {len(items)} items from chat history.")
        
        # Format the messages
        messages = []
        for item in items:
            messages.append(f"{item['username'].upper()}: {item['body']}")

        return "\n".join(messages)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []
    

get_chat_history_as_text("1eaf3b4f-44a9-4fb5-9d66-b442d0086b51")
