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
    #region_name="eu-west-3",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#ADD AN ENVIRONMENT VARIABLE FOR TABLE
#table = dynamodb.Table("prod_dev_analytics")
#table = dynamodb.Table("prod_preprod_analytics")
table = dynamodb.Table("prod_prod_analytics")


#table = DynamoDBClient().client.Table("PROD_chat")
#table = DynamoDBClient().client.Table("prod_dev_analytics") #Mettre dans une variable d'environnement en fonction si c'est dev, prep-prod ou prod 


def convert_to_decimal_list(float_list):
    return [Decimal(str(f)) for f in float_list]

def convert_decimal_to_str(decimal_list):
    return [str(d) for d in decimal_list]


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
async def store_analytics_async(
        chat_id: str, 
        course_id: str, 
        uid: str,
        input_embedding: List[float],
        output_embedding: List[float],
        feedback: str,
        ask_for_advisor: str,
        interaction_position: int,
        word_count: int,
        ai_message_id: str,
        input_message: str,
        output_message: str):
    print(f"Attempting to store message for ai_message_id: {ai_message_id}, course_id: {course_id}, uid: {uid}")


    try:

        # Convertir les listes d'embeddings en liste de Decimal pour le stockage
        input_embedding = convert_to_decimal_list(input_embedding)
        output_embedding = convert_to_decimal_list(output_embedding)


        # Convertir les listes de Decimal en chaînes pour la sérialisation JSON
        input_embedding_str = convert_decimal_to_str(input_embedding)
        output_embedding_str = convert_decimal_to_str(output_embedding)


         # Convertir les listes en JSON string
        input_embedding_json = json.dumps(input_embedding_str)
        output_embedding_json = json.dumps(output_embedding_str)
        
        # Préparer l'élément à insérer dans DynamoDB
        args = {
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'uid': uid,
            'course_id': course_id,
            'input_embedding': input_embedding_json,
            'output_embedding': output_embedding_json,
            'feedback': feedback,
            'ask_for_advisor': ask_for_advisor,
            'interaction_position': Decimal(interaction_position),
            'word_count': Decimal(word_count),
            'ai_message_id': ai_message_id,
            'input_text': input_message,
            'output_text': output_message,
        }
        
        # Insérer l'élément dans DynamoDB
        table.put_item(Item=args)
        print("Analytics stored successfully with message")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into analytics database: {error_code} - {error_message}")