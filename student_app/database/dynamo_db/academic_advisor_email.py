from typing import Any
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
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
#AWS_REGION_DEV = os.getenv('AWS_REGION_DEV')

# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    #region_name="eu-west-3",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#table = dynamodb.Table("prod_dev_academic_advisor_email") 
#table = dynamodb.Table("prod_preprod_academic_advisor_email")
table = dynamodb.Table("prod_prod_academic_advisor_email")

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
async def store_academic_advisor_email_async(uid: str, email: str):
    print(f"Attempting to store academic advisor email for uid: {uid}, email: {email}")

    try:
        # Préparer l'élément à insérer dans DynamoDB
        args = {
            'uid': uid,
            'email': email,
            'timestamp': datetime.now().isoformat(),
        }

        # Log prepared args for debugging
        print(f"Prepared item for DynamoDB: {json.dumps(args, indent=2)}")

        # Insérer l'élément dans DynamoDB
        response = table.put_item(Item=args)
        print(f"Response from DynamoDB: {response}")
        print("Academic advisor email stored successfully")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting item into academic advisor email table: {error_code} - {error_message}")
        # Log full error response for detailed debugging
        print(f"Full error response: {json.dumps(e.response, indent=2)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        # Log detailed exception information
        print(f"Traceback: {traceback.format_exc()}")
