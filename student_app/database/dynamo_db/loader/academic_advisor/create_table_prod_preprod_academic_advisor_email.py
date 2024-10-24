import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION_PREPROD = os.getenv('AWS_REGION_PREPROD')

def create_academic_advisor_email_table():
    # Create a DynamoDB client
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION_PREPROD,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    try:
        # Create the prod_dev_academic_advisor_email table
        table = dynamodb.create_table(
            TableName='prod_preprod_academic_advisor_email',
            KeySchema=[
                {
                    'AttributeName': 'uid',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'email',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'uid',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait until the table exists
        table.wait_until_exists()
        print("Table created successfully.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error creating table: {error_code} - {error_message}")

# Call the function to create the table
create_academic_advisor_email_table()