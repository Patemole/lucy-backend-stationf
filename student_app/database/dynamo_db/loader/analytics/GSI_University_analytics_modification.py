import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION_DEV = os.getenv('AWS_REGION_DEV')

def add_gsi_university_timestamp():
    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION_DEV,
                            aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    try:
        response = dynamodb.update_table(
            TableName='prod_dev_analytics',
            AttributeDefinitions=[
                {
                    'AttributeName': 'university',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': 'university-timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'university',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 10,
                            'WriteCapacityUnits': 10
                        }
                    }
                }
            ]
        )
        print("GSI ajouté avec succès.")
    except ClientError as e:
        print(f"Erreur lors de l'ajout du GSI : {e.response['Error']['Message']}")

# Appel de la fonction pour ajouter le GSI
add_gsi_university_timestamp()
