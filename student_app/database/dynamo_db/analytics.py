from typing import Any, Dict, List
#from third_party_api_clients.dynamo_db.dynamo_db_client import DynamoDBClient
from datetime import datetime, timedelta
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
import logging
import asyncio
from boto3.dynamodb.conditions import Key
import sys


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
        output_message: str,
        university: str):
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
            'university' : university,
        }
        
        # Insérer l'élément dans DynamoDB
        table.put_item(Item=args)
        print("Analytics stored successfully with message")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into analytics database: {error_code} - {error_message}")




'''
async def fetch_request_data_from_dynamo(time_filter: str) -> Dict[str, Any]:
    try:
        now = datetime.utcnow()

        # Calculate the start date based on the time filter
        if time_filter == 'Today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'Last Week':
            start_date = now - timedelta(days=7)
        elif time_filter == 'Last Month':
            start_date = now - timedelta(days=30)
        elif time_filter == 'Last Year':
            start_date = now - timedelta(days=365)
        else:
            raise ValueError("Invalid time filter provided")

        # Build the filter expression for DynamoDB query (only filtering by time for now)
        filter_expression = "#timestamp BETWEEN :start AND :end"
        expression_attribute_names = {"#timestamp": "timestamp"}
        expression_attribute_values = {
            ":start": start_date.isoformat(),
            ":end": now.isoformat()
        }

        # Query DynamoDB
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )

        items = response.get('Items', [])
        count = len(items)
        dates = [item['timestamp'] for item in items]

        return {"count": count, "dates": dates}

    except ClientError as e:
        logging.error(f"Error querying DynamoDB: {str(e)}")
        raise e

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise e
'''



'''
#NOUVELLE FOCNTION AVEC UNIVERSITY AS SEARCH 
async def fetch_request_data_from_dynamo(time_filter: str, university: str) -> Dict[str, Any]:
    try:
        now = datetime.utcnow()

        # Calculate the start date based on the time filter
        if time_filter == 'Today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == 'Last Week':
            start_date = now - timedelta(days=7)
        elif time_filter == 'Last Month':
            start_date = now - timedelta(days=30)
        elif time_filter == 'Last Year':
            start_date = now - timedelta(days=365)
        else:
            raise ValueError("Invalid time filter provided")

        # Initialize variables for pagination
        items = []
        last_evaluated_key = None

        # Paginate through the results
        while True:
            if university.lower() == "all":
                # If university is "all", query the entire table for timestamp
                if last_evaluated_key:
                    response = table.scan(
                        FilterExpression='#ts BETWEEN :start_date AND :end_date',
                        ExpressionAttributeNames={
                            '#ts': 'timestamp'
                        },
                        ExpressionAttributeValues={
                            ':start_date': start_date.isoformat(),
                            ':end_date': now.isoformat()
                        },
                        ProjectionExpression='#ts',
                        ExclusiveStartKey=last_evaluated_key
                    )
                else:
                    response = table.scan(
                        FilterExpression='#ts BETWEEN :start_date AND :end_date',
                        ExpressionAttributeNames={
                            '#ts': 'timestamp'
                        },
                        ExpressionAttributeValues={
                            ':start_date': start_date.isoformat(),
                            ':end_date': now.isoformat()
                        },
                        ProjectionExpression='#ts'
                    )
            else:
                # Query the GSI with university-timestamp-index for a specific university
                if last_evaluated_key:
                    response = table.query(
                        IndexName='university-timestamp-index',
                        KeyConditionExpression='university = :university AND #ts BETWEEN :start_date AND :end_date',
                        ExpressionAttributeNames={
                            '#ts': 'timestamp'
                        },
                        ExpressionAttributeValues={
                            ':university': university,
                            ':start_date': start_date.isoformat(),
                            ':end_date': now.isoformat()
                        },
                        ProjectionExpression='#ts',
                        ExclusiveStartKey=last_evaluated_key
                    )
                else:
                    response = table.query(
                        IndexName='university-timestamp-index',
                        KeyConditionExpression='university = :university AND #ts BETWEEN :start_date AND :end_date',
                        ExpressionAttributeNames={
                            '#ts': 'timestamp'
                        },
                        ExpressionAttributeValues={
                            ':university': university,
                            ':start_date': start_date.isoformat(),
                            ':end_date': now.isoformat()
                        },
                        ProjectionExpression='#ts'
                    )

            # Collect items and handle pagination
            items.extend(response.get('Items', []))
            last_evaluated_key = response.get('LastEvaluatedKey', None)

            if not last_evaluated_key:
                break

        # Count the number of timestamps and create a list of timestamps
        count = len(items)
        dates = [item['timestamp'] for item in items]

        return {"count": count, "dates": dates}

    except ClientError as e:
        logging.error(f"Error querying DynamoDB: {str(e)}")
        raise e

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise e
'''



def fetch_request_data_from_dynamo(university, filter_time):
    
    end_date = datetime.now()

    if filter_time == "Today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_time == "Last Week":
        start_date = end_date - timedelta(days=7)
    elif filter_time == "Last Month":
        start_date = end_date - timedelta(days=30)
    elif filter_time == "Last Year":
        start_date = end_date - timedelta(days=365)
    else:
        raise ValueError("Invalid filter_time value provided.")

    # Format dates to ISO string for DynamoDB comparison
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    # Initialize list to collect all timestamps
    timestamps = []

    # Set initial parameters
    total_items_retrieved = 0
    total_data_size = 0  # For tracking total size in bytes
    exclusive_start_key = None  # For pagination

    # Keep querying until no more pages are available
    while True:
        if university == "all":
            filter_expression = Key('timestamp').between(start_date_str, end_date_str)
            params = {
                'IndexName': 'university-timestamp-index',
                'FilterExpression': filter_expression,
                'ProjectionExpression': '#ts',
                'ExpressionAttributeNames': {'#ts': 'timestamp'}
            }
            if exclusive_start_key:
                params['ExclusiveStartKey'] = exclusive_start_key

            response = table.scan(**params)
        else:
            filter_expression = Key('university').eq(university) & Key('timestamp').between(start_date_str, end_date_str)
            params = {
                'IndexName': 'university-timestamp-index',
                'KeyConditionExpression': filter_expression,
                'ProjectionExpression': '#ts',
                'ExpressionAttributeNames': {'#ts': 'timestamp'}
            }
            if exclusive_start_key:
                params['ExclusiveStartKey'] = exclusive_start_key

            response = table.query(**params)

        # Collect timestamps from this page
        page_items = response['Items']
        timestamps += [item['timestamp'] for item in page_items]

        # Update total items and data size
        page_size_in_bytes = sys.getsizeof(page_items)
        total_items_retrieved += len(page_items)
        total_data_size += page_size_in_bytes

        # Print the data for debugging purposes
        print(f"Page size: {page_size_in_bytes / 1024:.2f} KB, Total data size: {total_data_size / (1024 * 1024):.2f} MB")
        print(f"Total items retrieved so far: {total_items_retrieved}")

        # Check if there are more pages to fetch
        exclusive_start_key = response.get('LastEvaluatedKey')

        # If no more pages, break the loop
        if exclusive_start_key is None:
            break

    # Count the number of timestamps
    timestamp_count = len(timestamps)
    
    # Return the count and the list of timestamps
    return timestamp_count, timestamps

# Example usage
#university = 'all'  # Or specific university name
#filter_time = 'Last Week'  # Options: 'Today', 'Last Week', 'Last Month', 'Last Year'

#count, timestamps = fetch_request_data_from_dynamo(university, filter_time)
#print(count)
#print(timestamps)



'''

async def main():
    
    # Choisir un filtre de temps (Today, Last Week, Last Month, Last Year)
    time_filter = 'Last Month'  # Exemple : utiliser 'Today', 'Last Week', 'Last Month'
    university = 'all'

    try:
        # Appel de la fonction pour récupérer les données
        result = await fetch_request_data_from_dynamo(time_filter, university)

        # Afficher le résultat
        print("Nombre de timestamps récupérés:", result["count"])
        print("Liste des timestamps:")
        print(result["dates"])

    except Exception as e:
        logging.error(f"Erreur lors de l'exécution : {str(e)}")
        raise e

# Exécuter la fonction principale en mode asynchrone
if __name__ == "__main__":
    asyncio.run(main())
    '''