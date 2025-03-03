from third_party_api_clients.dynamo_db.dynamo_db_client import DynamoDBClient
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
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Union



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
async def get_chat_history(chat_id: str):
    print("\n")
    print("\n")
    print("\n")
    print("\n")
    print(f"Attempting to retrieve chat history for chat_id: {chat_id}")
    try:
        response = table.query(
            KeyConditionExpression='chat_id = :chat_id',
            ExpressionAttributeValues={':chat_id': chat_id},
            ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
        )
        items = response.get('Items', [])
        print(f"Retrieved {len(items)} items from chat history.")
        
        # Ne retourner que le username et le body
        filtered_items = [{'username': item['username'], 'body': item['body']} for item in items]

        return filtered_items
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []


@timing_decorator
async def get_most_recent_conversations(limit: int = 100):
    """
    Retrieve the most recent conversations from the DynamoDB table.

    :param limit: Number of conversations to fetch (default is 100).
    :return: A JSON object containing the most recent conversations.
    """
    print(f"Attempting to retrieve the {limit} most recent conversations.")
    try:
        # Use ScanIndexForward=False to sort by timestamp descending
        response = table.scan(
            Limit=limit,
            FilterExpression=Attr('timestamp').exists(),  # Ensure 'timestamp' exists
        )

        # Extract and sort by 'timestamp' in descending order
        items = sorted(
            response.get('Items', []),
            key=lambda x: x['timestamp'],
            reverse=True
        )

        # Filter the fields to include only relevant information
        filtered_items = [
            {
                'chat_id': item.get('chat_id', ''),
                'timestamp': item.get('timestamp', ''),
                'username': item.get('username', ''),
                'body': item.get('body', ''),
                'course_id': item.get('course_id', ''),
                'message_id': item.get('message_id', ''),
            }
            for item in items
        ]

        print(f"Retrieved {len(filtered_items)} most recent conversations.")
        return json.dumps({'conversations': filtered_items}, indent=2)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error retrieving most recent conversations: {error_code} - {error_message}")
        return json.dumps({'error': f"{error_code} - {error_message}"})


@timing_decorator
async def store_message_async(
        chat_id: str, 
        course_id: str, 
        message_body: str, 
        #username: str = "TAI",
        username: str,
        documents: List[Dict[str, Any]] = []):
    print(f"Attempting to store message for chat_id: {chat_id}, course_id: {course_id}, username: {username}")
    try:

        # Generate a unique message_id
        message_id = str(uuid.uuid4())

        # Insert the item into DynamoDB
        args = {
            'message_id': message_id,
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'course_id': course_id,
            'body': message_body,
            'username': username
        }
        if username == "TAI" and documents:
            args['documents'] = documents

        table.put_item(Item=args)
        print(f"Message stored successfully with message_id: {args['message_id']}")

        # Return the message_id
        return message_id
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error inserting message into chat history: {error_code} - {error_message}")
        return None




@timing_decorator
async def get_timing_history(last_database_curated: str):  # timestamp
    print(f"\n\n\n\nAttempting to retrieve chat history with interval: {last_database_curated}")
    
    try:
        # Initialisation des paramètres de scan avec alias pour timestamp
        scan_kwargs = {
            'FilterExpression': Attr('timestamp').gt(last_database_curated),
            'ProjectionExpression': '#ts, username, body, chat_id',  # Ajout de chat_id
            'ExpressionAttributeNames': {'#ts': 'timestamp'}  # Définissez l'alias pour timestamp
        }

        items = []
        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key

            response = table.scan(**scan_kwargs)
            batch_items = response.get('Items', [])
            items.extend(batch_items)
            print(f"Retrieved {len(batch_items)} items from chat history.")

            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

        # Trier par alias de timestamp (optionnel)
        items.sort(key=lambda x: x['timestamp'])

        # Filtrer pour ne conserver que les champs nécessaires
        filtered_items = [{'username': item['username'], 'body': item['body'], 'timestamp': item['timestamp'], 'chat_id': item['chat_id']} for item in items]

        return filtered_items

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error querying chat history: {error_code} - {error_message}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return []

    

@timing_decorator
async def get_messages_from_history(chat_id: str, n: Optional[int] = None) -> List[Dict[str, str]]:

    filtered_items = await get_chat_history(chat_id)

    # Ensure of getting even number of messages (user + lucy)
    if n is None :
        items = filtered_items  # Get all messages
    elif n % 2 != 0:  # If n is odd
        n += 1  # Make it even
        items = filtered_items[-n:]
    else:  # If n is even
        items = filtered_items[-n:]

    messages = [
        {"role": "assistant" if item['username'] == "Lucy" else "user", "content": item['body']}
        for item in items
    ]

    # for item in items:
    #     if item['username'] == "Lucy":
    #         current_role = "assistant"
    #         message_dict = {"role": current_role, "content": item['body']}
    #     else:
    #         current_role = "user"
    #         message_dict = {"role": current_role, "content": item['body']}
       
    #     messages.append(message_dict)

    #TODO: Verify and adapt to make sure the format is correct
    # if filtered_items is not None:
    #     # Check if the last message is an assistant message
    #     if messages[-1]['role'] == 'assistant':
    #         # Add an empty assistant message at the end
    #         messages.append({"role": "assistant", "content": ""})
    #         # raise Exception("The last message is not an assistant message.")
        
    #     # Check if the first message is a user message
    #     if messages[0]['role'] != 'user':
    #         # Add an empty user message at the beginning
    #         messages.insert(0, {'role': 'user', 'content': ''})
    #         print("WARNING/ERROR: The first message was not a user message. An empty user message was added at the beginning of the list.")
    #         # raise Exception("The first message is not a user message.")
    

    print(f"Retrieved {len(messages)} messages from chat history.")
    return messages



@timing_decorator
async def get_conversations_from_chat_ids(chat_ids: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """
    Retrieve conversations for multiple chat IDs in chronological order (oldest messages first).
    
    :param chat_ids: List of chat IDs.
    :return: Dictionary where each chat_id maps to its respective conversation.
    """
    conversations = {}
    
    for chat_id in chat_ids:
        try:
            print(f"Attempting to retrieve conversation for chat_id: {chat_id}")
            response = table.query(
                KeyConditionExpression=Key('chat_id').eq(chat_id),
                ScanIndexForward=True  # Order by ascending timestamp (oldest first)
            )
            items = response.get('Items', [])
            print(f"Retrieved {len(items)} messages for chat_id: {chat_id}")
            
            # Ensure messages are sorted by timestamp
            sorted_items = sorted(items, key=lambda x: x['timestamp'])
            
            # Format messages properly
            messages = [
                {"role": "Lucy" if item['username'] == "Lucy" else "user", "content": item['body']}
                for item in sorted_items
            ]
            
            conversations[chat_id] = messages
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Error retrieving conversation for chat_id {chat_id}: {error_code} - {error_message}")
            conversations[chat_id] = []
    
    return conversations







#DAILY ACTIVE USER
def strict_count_active_users(start_date: str) -> int:
    """
    Compte le nombre d'utilisateurs strictement actifs, c'est-à-dire ceux qui ont envoyé au moins
    un message chaque jour depuis start_date jusqu'à aujourd'hui.

    :param start_date: Date de début au format "YYYY-MM-DD".
    :return: Nombre d'utilisateurs strictement actifs.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        logging.error(f"❌ Format de start_date invalide: {start_date}")
        return 0

    today = datetime.utcnow().date()
    window_days = (today - start_dt.date()).days + 1
    logging.info(f"Calcul strict des utilisateurs actifs sur {window_days} jours, depuis {start_date} jusqu'à {today}")

    response = table.scan(
        FilterExpression=Key('#ts').gte(start_date),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    items = response.get('Items', [])
    logging.info(f"{len(items)} enregistrements récupérés pour le calcul strict depuis {start_date}")

    user_days = {}
    for item in items:
        username = item.get('username')
        ts = item.get('timestamp', '')
        if username and ts:
            day = ts[:10]  # On suppose que le format est ISO "YYYY-MM-DD..."
            if username not in user_days:
                user_days[username] = set()
            user_days[username].add(day)

    # Création de l'ensemble des jours attendus dans la période
    expected_days = {(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(window_days)}
    strict_active_users = sum(1 for days_set in user_days.values() if expected_days.issubset(days_set))
    logging.info(f"{strict_active_users} utilisateurs strictement actifs depuis {start_date} jusqu'à {today}")
    
    return strict_active_users


#WAU, MAU, SAU
def simple_count_active_users_in_window_range(start_date: str, end_date: str) -> int:
    """
    Compte le nombre d'utilisateurs uniques ayant envoyé au moins un message
    entre start_date et end_date (inclus).
    """
    logging.info(f"Calcul des utilisateurs actifs entre {start_date} et {end_date}")
    response = table.scan(
        FilterExpression=Key('#ts').between(start_date, end_date),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    items = response.get('Items', [])
    logging.info(f"{len(items)} enregistrements récupérés entre {start_date} et {end_date}")
    users = set(item['username'] for item in items if 'username' in item)
    logging.info(f"{len(users)} utilisateurs uniques trouvés entre {start_date} et {end_date}")
    return len(users)




def get_date_or_default(date_str: str, default_days: int) -> str:
    """
    Convertit une chaîne au format "YYYY-MM-DD" en une date formatée.
    Si la chaîne est vide ou invalide, retourne la date d'aujourd'hui moins default_days.
    """
    if not date_str:
        computed_date = (datetime.utcnow() - timedelta(days=default_days)).strftime("%Y-%m-%d")
        logging.info(f"Aucune date fournie, utilisation de la date par défaut: {computed_date}")
        return computed_date
    try:
        computed_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        logging.info(f"Date fournie utilisée: {computed_date}")
        return computed_date
    except ValueError:
        logging.error(f"❌ Format de date invalide pour '{date_str}'. Utilisation de la date par défaut.")
        computed_date = (datetime.utcnow() - timedelta(days=default_days)).strftime("%Y-%m-%d")
        return computed_date
    


def count_active_users(start_date: str) -> int:
    """
    DAU : Compte le nombre d'utilisateurs uniques ayant envoyé au moins un message depuis start_date jusqu'à aujourd'hui.
    """
    logging.info(f"Calcul des utilisateurs actifs (DAU) depuis {start_date}")
    response = table.scan(
        FilterExpression=Key('#ts').gte(start_date),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    items = response.get('Items', [])
    logging.info(f"{len(items)} enregistrements récupérés avec timestamp >= {start_date}")
    users = set(item['username'] for item in items if 'username' in item)
    logging.info(f"{len(users)} utilisateurs uniques trouvés depuis {start_date}")
    return len(users)



def simple_count_active_users_in_window(reference_date: str, window_required: int) -> int or str:
    """
    Pour WAU, MAU ou SAU : Si la période entre reference_date et aujourd'hui est d'au moins window_required jours,
    retourne le nombre d'utilisateurs actifs (au moins un message dans la fenêtre de window_required jours).
    Sinon, retourne "N/A".
    """
    try:
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d").date()
    except ValueError:
        logging.error(f"❌ Format de reference_date invalide: {reference_date}")
        return "N/A"
    today = datetime.utcnow().date()
    period = (today - ref_dt).days + 1
    if period < window_required:
        logging.info(f"Période insuffisante: {period} jours (< {window_required} jours). Retourne N/A.")
        return "N/A"
    # La fenêtre est définie de reference_date à (reference_date + window_required - 1)
    window_end = (ref_dt + timedelta(days=window_required - 1)).strftime("%Y-%m-%d")
    count = simple_count_active_users_in_window_range(reference_date, window_end)
    logging.info(f"Utilisateurs actifs sur la fenêtre de {window_required} jours (de {reference_date} à {window_end}): {count}")
    return count



def count_returning_users(past_start: str, recent_start: str) -> int:
    """
    Calcule le nombre d’utilisateurs qui étaient actifs dans la période [past_start, recent_start]
    et qui sont également actifs depuis recent_start.
    """
    logging.info(f"Calcul des utilisateurs retournant pour la période [{past_start} à {recent_start}]")
    past_response = table.scan(
        FilterExpression=Key('#ts').between(past_start, recent_start),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    past_items = past_response.get('Items', [])
    past_users = set(item['username'] for item in past_items if 'username' in item)
    logging.info(f"{len(past_users)} utilisateurs actifs trouvés dans la période passée")
    
    recent_response = table.scan(
        FilterExpression=Key('#ts').gte(recent_start),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    recent_items = recent_response.get('Items', [])
    recent_users = set(item['username'] for item in recent_items if 'username' in item)
    logging.info(f"{len(recent_users)} utilisateurs actifs trouvés depuis {recent_start}")
    
    returning_users = past_users.intersection(recent_users)
    logging.info(f"Nombre d'utilisateurs retournant: {len(returning_users)}")
    return len(returning_users)

def calculate_churn(reference_date: str) -> float:
    """
    Calcule le taux d'abandon (churn rate) en comparant le nombre d'utilisateurs actifs dans le mois précédent
    avec ceux du mois courant, en utilisant la date de référence.
    """
    try:
        ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
    except ValueError:
        logging.error(f"❌ Date de référence invalide: {reference_date}. Utilisation de la date actuelle.")
        ref_dt = datetime.utcnow()
    last_month_start = (ref_dt - timedelta(days=30)).strftime("%Y-%m-%d")
    this_month_start = reference_date  # On considère que reference_date marque le début du mois courant
    logging.info(f"Calcul du churn rate : Mois précédent depuis {last_month_start}, Mois courant depuis {this_month_start}")
    
    users_last_month = count_active_users(last_month_start)
    users_this_month = count_active_users(this_month_start)
    logging.info(f"Utilisateurs (mois précédent): {users_last_month}, (mois courant): {users_this_month}")
    if users_last_month == 0:
        return 0
    churn_rate = ((users_last_month - users_this_month) / users_last_month) * 100
    logging.info(f"Taux de churn: {churn_rate}%")
    return round(churn_rate, 2)

def sessions_per_user(since_date: str) -> float:
    """
    Calcule le nombre moyen de sessions (messages) par utilisateur en ne considérant que
    les enregistrements dont le 'timestamp' est postérieur ou égal à since_date.
    """
    try:
        _ = datetime.strptime(since_date, "%Y-%m-%d")
    except ValueError:
        logging.error(f"❌ Format de since_date invalide: {since_date}. Utiliser 'YYYY-MM-DD'.")
        return 0
    logging.info(f"Calcul du nombre moyen de sessions par utilisateur depuis {since_date}")
    response = table.scan(
        FilterExpression=Key('#ts').gte(since_date),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    items = response.get('Items', [])
    logging.info(f"{len(items)} enregistrements récupérés depuis {since_date}")
    user_sessions = {}
    for item in items:
        username = item.get('username')
        if username:
            user_sessions[username] = user_sessions.get(username, 0) + 1
    logging.info(f"{len(user_sessions)} utilisateurs uniques trouvés")
    avg_sessions = sum(user_sessions.values()) / len(user_sessions) if user_sessions else 0
    logging.info(f"Moyenne des sessions par utilisateur: {avg_sessions}")
    return round(avg_sessions, 2)

def rolling_retention(days: int = 14, reference_date: str = None) -> float:
    """
    Calcule le pourcentage d’utilisateurs qui reviennent après 'days' jours,
    en utilisant une date de référence si fournie, sinon la date actuelle.
    """
    if reference_date:
        try:
            ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
        except ValueError:
            logging.error(f"❌ Date de référence invalide: {reference_date}. Utilisation de la date actuelle.")
            ref_dt = datetime.utcnow()
    else:
        ref_dt = datetime.utcnow()
    start_period = (ref_dt - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    end_period = (ref_dt - timedelta(days=days)).strftime("%Y-%m-%d")
    logging.info(f"Calcul de la Rolling Retention pour la période [{start_period} à {end_period}]")
    
    past_response = table.scan(
        FilterExpression=Key('#ts').between(start_period, end_period),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    past_items = past_response.get('Items', [])
    users_past = set(item['username'] for item in past_items if 'username' in item)
    logging.info(f"{len(users_past)} utilisateurs trouvés dans la période passée [{start_period}, {end_period}]")
    
    current_start = reference_date if reference_date else datetime.utcnow().strftime("%Y-%m-%d")
    current_response = table.scan(
        FilterExpression=Key('#ts').gte(current_start),
        ProjectionExpression="username, #ts",
        ExpressionAttributeNames={"#ts": "timestamp"}
    )
    current_items = current_response.get('Items', [])
    users_current = set(item['username'] for item in current_items if 'username' in item)
    logging.info(f"{len(users_current)} utilisateurs trouvés depuis {current_start}")
    
    if not users_past:
        logging.info("Aucun utilisateur trouvé dans la période passée pour le calcul de la Rolling Retention.")
        return 0
    retained_users = users_past.intersection(users_current)
    retention_rate = (len(retained_users) / len(users_past)) * 100
    logging.info(f"Rolling Retention ({days} jours): {retention_rate}%")
    return round(retention_rate, 2)
