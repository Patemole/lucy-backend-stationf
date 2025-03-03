import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION_PROD = os.getenv('AWS_REGION_PROD')

def create_chat_table():
    # Création d'un client DynamoDB
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION_PROD,  # Assurez-vous que la région est correcte
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    try:
        # Création de la table prod_dev_analytics
        table = dynamodb.create_table(
            TableName='prod_prod_analytics',
            KeySchema=[
                {
                    'AttributeName': 'chat_id',  # Nom de l'attribut pour la clé de partition
                    'KeyType': 'HASH'  # Type de la clé de partition, HASH signifie clé principale
                },
                {
                    'AttributeName': 'timestamp',  # Nom de l'attribut pour la clé de tri
                    'KeyType': 'RANGE'  # Type de la clé de tri
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'chat_id',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'uid',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'course_id',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'feedback',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'ask_for_advisor',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'interaction_position',
                    'AttributeType': 'N'  # Type 'N' pour Number
                },
                {
                    'AttributeName': 'word_count',
                    'AttributeType': 'N'  # Type 'N' pour Number
                },
                {
                    'AttributeName': 'ai_message_id',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'input_text',
                    'AttributeType': 'S'  # Type 'S' pour String
                },
                {
                    'AttributeName': 'output_text',
                    'AttributeType': 'S'  # Type 'S' pour String
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            },
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'uid-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'uid',
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
                },
                {
                    'IndexName': 'interaction_position-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'interaction_position',
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
                },
                {
                    'IndexName': 'ai_message_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'ai_message_id',
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
                },
                {
                    'IndexName': 'course_id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'course_id',
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
                },
                {
                    'IndexName': 'feedback-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'feedback',
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
                },
                {
                    'IndexName': 'ask_for_advisor-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'ask_for_advisor',
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
                },
                {
                    'IndexName': 'word_count-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'word_count',
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
                },
                {
                    'IndexName': 'input_text-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'input_text',
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
                },
                {
                    'IndexName': 'output_text-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'output_text',
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
            ]
        )

        # Attendre que la table soit complètement créée
        table.wait_until_exists()
        print("Table created successfully.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error creating table: {error_code} - {error_message}")

# Appel de la fonction pour créer la table
create_chat_table()