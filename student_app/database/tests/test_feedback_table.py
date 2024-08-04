import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import traceback

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION_DEV = os.getenv('AWS_REGION_DEV')
#DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'prod_dev_feedback')

def create_dynamodb_resource():
    return boto3.resource(
        'dynamodb',
        region_name=AWS_REGION_DEV,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

def store_feedback(
        dynamodb, 
        uid: str, 
        feedback: str, 
        page: str, 
        chat_id: Optional[str] = None, 
        ai_message: Optional[str] = None, 
        human_message: Optional[str] = None):
    print(f"Attempting to store feedback for uid: {uid}, page: {page}, feedback: {feedback}")

    table = dynamodb.Table('prod_dev_feedback')

    try:
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
        print(f"Prepared item for DynamoDB: {json.dumps(args, indent=2)}")

        # Insérer l'élément dans DynamoDB
        response = table.put_item(Item=args)
        print(f"Response from DynamoDB: {response}")
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

if __name__ == "__main__":
    # Create the DynamoDB resource
    dynamodb = create_dynamodb_resource()

    # Test data
    uid = "test_user"
    feedback = "This is a test feedback"
    page = "test_page"
    chat_id = "test_chat_id"
    ai_message = "This is a test AI message"
    human_message = "This is a test human message"

    # Store the test feedback
    store_feedback(
        dynamodb, 
        uid, 
        feedback, 
        page, 
        chat_id=chat_id, 
        ai_message=ai_message, 
        human_message=human_message
    )
