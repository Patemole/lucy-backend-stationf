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
async def store_feedback_without_popup_async(
        message_id: int, 
        chat_id: str, 
        is_positive: bool, 
        user_id: str,
        ai_message: str,
        human_message: str,
        ):
    
    print("Beginning to store feedback without popup")

    try:
        # Préparer l'élément à insérer dans DynamoDB
        feedback_item = {
            'message_id': message_id,
            'chat_id': chat_id,
            'is_positive': is_positive,
            'human_message': human_message,
            'ai_message': ai_message,
            'uid': user_id,
            'timestamp': datetime.now().isoformat(),
        }

        # Insérer l'élément dans DynamoDB
        print("Item to insert into DynamoDB:", feedback_item)
        table.put_item(Item=feedback_item)
        print("Feedback without popup stored successfully")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into feedback database: {error_code} - {error_message}")
        print(f"Full error response: {json.dumps(e.response, indent=2)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")




@timing_decorator
async def store_feedback_async(
        uid: str, 
        feedback: str, 
        page: Optional[str] = None, 
        chat_id: Optional[str] = None, 
        ai_message: Optional[str] = None, 
        human_message: Optional[str] = None,
        relevance: Optional[int] = None,
        accuracy: Optional[int] = None,
        format: Optional[int] = None,
        sources: Optional[int] = None,
        overall_satisfaction: Optional[int] = None):
    
    print("Beginning to store feedback")

    try:
        # Assigner une valeur par défaut à page si elle est None
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

        # Ajouter les scores de feedback si fournis
        if relevance is not None:
            args['relevance'] = relevance
        if accuracy is not None:
            args['accuracy'] = accuracy
        if format is not None:
            args['format'] = format
        if sources is not None:
            args['sources'] = sources
        if overall_satisfaction is not None:
            args['overall_satisfaction'] = overall_satisfaction

        # Insérer l'élément dans DynamoDB
        table.put_item(Item=args)
        print("Feedback stored successfully")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into feedback database: {error_code} - {error_message}")
        print(f"Full error response: {json.dumps(e.response, indent=2)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")


