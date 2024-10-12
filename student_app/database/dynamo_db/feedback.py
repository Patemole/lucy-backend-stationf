from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
from datetime import datetime
import time
from functools import wraps
import boto3
import os
from dotenv import load_dotenv
import json
import traceback

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    #region_name="eu-west-3",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#table = dynamodb.Table("prod_dev_feedback") 
table = dynamodb.Table("prod_preprod_feedback")
#table = dynamodb.Table("prod_prod_feedback")

# Définir le décorateur
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

@timing_decorator
async def store_feedback_async(
        uid: str, 
        feedback: str, 
        page: Optional[str] = None, 
        chat_id: Optional[str] = None, 
        ai_message: Optional[str] = None, 
        human_message: Optional[str] = None):
    #print(f"Attempting to store feedback for uid: {uid}, page: {page}, feedback: {feedback}")

    print("Beginning to store feedback")

    try:
        # Assigner une valeur par défaut à `page` si elle est None
        if page is None:
            page = 'chat_page'

        # Préparer l'élément à insérer dans DynamoDB
        args = {
            'uid': uid,
            'feedback': feedback,
            'page': page,
            'timestamp': datetime.now().isoformat(),
        }
        
        if chat_id:
            args['chat_id'] = chat_id
        if ai_message:
            args['ai_message'] = ai_message
        if human_message:
            args['human_message'] = human_message

        # Log prepared args for debugging
        #print(f"Prepared item for DynamoDB: {json.dumps(args, indent=2)}")

        # Insérer l'élément dans DynamoDB
        table.put_item(Item=args)
        #print(f"Response from DynamoDB: {response}")
        print("Feedback stored successfully")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into feedback database: {error_code} - {error_message}")
        # Log full error response for detailed debugging
        print(f"Full error response: {json.dumps(e.response, indent=2)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        # Log detailed exception information
        print(f"Traceback: {traceback.format_exc()}")


# Example of calling the function (should be called within an async environment)
# await store_feedback_async(uid="1234", feedback="Great service!", page="/home")







'''
from typing import Any, Dict, List
from third_party_api_clients.dynamo_db.dynamo_db_client import DynamoDBClient
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import time
from functools import wraps
from decimal import Decimal
import boto3
import os
from dotenv import load_dotenv
import json


load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')


# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name="eu-west-3",  # Assurez-vous que la région est correcte
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#ADD AN ENVIRONMENT VARIABLE FOR TABLE
table = dynamodb.Table("prod_dev_feedback")


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
async def store_feedback_async(
        chat_id: str, 
        page: str, 
        uid: str,
        feedback: str,
        ai_message: str,
        human_message: str):
    print(f"Attempting to store feedback for uid: {uid}, page: {page}, feedback: {feedback}")


    try:
        
        # Préparer l'élément à insérer dans DynamoDB
        args = {
            'uid': uid,
            'chat_id': chat_id,
            'feedback': feedback,
            'page': page,
            'ai_message': ai_message,
            'human_message' : human_message,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Insérer l'élément dans DynamoDB
        table.put_item(Item=args)
        print("Feedback stored successfully")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into feedback database: {error_code} - {error_message}")
        '''