import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Récupération des clés AWS depuis les variables d'environnement
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION_DEV')

# Initialisation du service DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Nom de la table
table_name = 'dev_fake_data_yc'
table = dynamodb.Table(table_name)

# Fonction pour ajouter les éléments du fichier JSON à la table
def load_data_to_dynamodb(json_file):
    try:
        # Lire les données du fichier JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Boucle pour insérer chaque élément dans DynamoDB
        for item in data:
            # Reformater les données pour correspondre à DynamoDB
            dynamodb_item = {
                'chat_id': item['chat_id']['S'],
                'timestamp': item['timestamp']['S'],
                'body': item['body']['S'],
                'course_id': item['course_id']['S'],
                'message_id': item['message_id']['S'],
                'username': item['username']['S']
            }

            # Insérer l'élément dans la table
            table.put_item(Item=dynamodb_item)
            print(f"Item inséré: {dynamodb_item['message_id']}")

    except ClientError as e:
        print(f"Erreur lors de l'insertion: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Une erreur est survenue: {str(e)}")

# Spécifier le chemin vers votre fichier JSON
json_file_path = 'student_app/database/dynamo_db/loader/fake_data_demo/fake_data_yc_improvment.json'

# Appel de la fonction pour charger les données JSON dans DynamoDB
load_data_to_dynamodb(json_file_path)
