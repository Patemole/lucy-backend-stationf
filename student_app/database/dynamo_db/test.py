from typing import Any, Dict, List
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



def get_chat_history_as_text(chat_id: str):
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

messages = get_chat_history_as_text('8d35f7b1-41e5-4dfe-a33d-4592f768d5d5')
print(messages)