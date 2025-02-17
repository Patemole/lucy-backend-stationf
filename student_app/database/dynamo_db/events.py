from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
from datetime import datetime
import time
from functools import wraps
import boto3
import os
from dotenv import load_dotenv
import json
import traceback
import logging
from datetime import datetime, timedelta
from typing import List, Dict

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
table = dynamodb.Table("test-event-HFU") 
#table = dynamodb.Table("prod_preprod_feedback")
#table = dynamodb.Table("prod_prod_feedback")

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


async def fetch_events_from_dynamoDB_all_events() -> List[Dict]:

    """
    Récupère tous les événements du calendrier stockés dans DynamoDB avec logs détaillés.
    """
    logging.info("Début de la récupération des événements depuis DynamoDB.")

    try:
        # Vérifie si la connexion à DynamoDB est correcte
        logging.info("Tentative de connexion à la table DynamoDB.")
        logging.info(f"Nom de la table utilisée: {table.name}")

        # Exécuter un scan() pour récupérer tous les événements
        logging.info("Lancement de la requête scan() sur la table DynamoDB...")
        response = table.scan()
        
        # Vérification si la requête s'est bien déroulée
        logging.info(f"Réponse brute de scan(): {response}")

        # Vérifier si des items sont retournés
        items = response.get("Items", [])
        logging.info(f"Nombre d'événements récupérés: {len(items)}")

        if not items:
            logging.warning("⚠ Aucun événement récupéré depuis la table DynamoDB.")

        # Transformer les données en une liste de dictionnaires
        events = [
            {
                "title": item.get("Title", "Untitled Event"),
                "audience": item.get("Audience", "Unknown"),
                "banner": item.get("Banner", "Unknown"),
                "category": item.get("Category", "General"),
                "day": item.get("Day", "Unknown"),
                "description": item.get("Description", "No description available"),
                "end_day": item.get("End_day", "Unknown"),
                "end_time": item.get("End_time", "Unknown"),
                "location": item.get("Location", "No location specified"),
                "month": item.get("Month", "Unknown"),
                "organizer": item.get("Organizer", "No organizer specified"),
                "start_time": item.get("Start_time", "Unknown"),
                "sub-category": item.get("Sub-Category", "General"),
                "tags": item.get("Tags and Keywords", []),
                "year": item.get("Year", "Unknown"),
            }
            for item in items
        ]

        logging.info(f"✅ Transformation réussie - Nombre d'événements après parsing: {len(events)}")

        return events

    except ClientError as e:
        logging.error(f"❌ Erreur ClientError lors de la récupération des événements: {str(e)}")
        return []
    
    except Exception as e:
        logging.error(f"❌ Erreur inattendue lors de la récupération des événements: {str(e)}")
        return []
 



@timing_decorator
async def fetch_events_from_dynamoDB() -> List[Dict]:
    """
    Récupère les événements du calendrier pour la semaine en cours depuis DynamoDB avec logs détaillés.
    """
    logging.info("Début de la récupération des événements depuis DynamoDB.")

    try:
        # Vérifie la connexion à DynamoDB
        logging.info("Tentative de connexion à la table DynamoDB.")
        logging.info(f"Nom de la table utilisée: {table.name}")

        # Exécuter un scan() pour récupérer tous les événements
        logging.info("Lancement de la requête scan() sur la table DynamoDB...")
        response = table.scan()

        # Vérification si la requête s'est bien déroulée
        logging.info(f"Réponse brute de scan(): {response}")

        # Récupérer tous les événements
        items = response.get("Items", [])
        logging.info(f"Nombre total d'événements récupérés: {len(items)}")

        if not items:
            logging.warning("⚠ Aucun événement récupéré depuis la table DynamoDB.")
            return []

        # Définir les dates pour la semaine en cours
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())  # Lundi de cette semaine
        end_of_week = start_of_week + timedelta(days=6)  # Dimanche de cette semaine

        logging.info(f"Filtrage des événements entre {start_of_week.date()} et {end_of_week.date()}.")

        # Fonction pour convertir une date en objet datetime
        def parse_event_date(day: str, month: str, year: str):
            try:
                day = int(float(day)) if day.replace('.', '', 1).isdigit() else None
                year = int(year) if year.isdigit() else today.year  # Si l'année est manquante, on met l'année actuelle
                month_dict = {
                    "January": 1, "February": 2, "March": 3, "April": 4,
                    "May": 5, "June": 6, "July": 7, "August": 8,
                    "September": 9, "October": 10, "November": 11, "December": 12
                }
                month = month_dict.get(month, None)  # Convertir le mois en numéro

                if day and month and year:
                    return datetime(year, month, day)
                return None  # Retourne None si une des valeurs est invalide
            except Exception as e:
                logging.warning(f"Erreur lors de la conversion de la date: {day}, {month}, {year}. Erreur: {str(e)}")
                return None

        # Filtrer les événements qui sont dans la semaine en cours
        filtered_events = []
        for item in items:
            event_date = parse_event_date(item.get("Day", ""), item.get("Month", ""), item.get("Year", ""))
            
            if event_date and start_of_week <= event_date <= end_of_week:
                filtered_events.append({
                    "title": item.get("Title", "Untitled Event"),
                    "audience": item.get("Audience", "Unknown"),
                    "banner": item.get("Banner", "Unknown"),
                    "category": item.get("Category", "General"),
                    "day": item.get("Day", "Unknown"),
                    "description": item.get("Description", "No description available"),
                    "end_day": item.get("End_day", "Unknown"),
                    "end_time": item.get("End_time", "Unknown"),
                    "location": item.get("Location", "No location specified"),
                    "month": item.get("Month", "Unknown"),
                    "organizer": item.get("Organizer", "No organizer specified"),
                    "start_time": item.get("Start_time", "Unknown"),
                    "sub_category": item.get("Sub-Category", "General"),
                    "tags": item.get("Tags and Keywords", []),
                    "year": item.get("Year", "Unknown"),
                })

        logging.info(f"✅ {len(filtered_events)} événements trouvés pour la semaine en cours.")

        return filtered_events

    except ClientError as e:
        logging.error(f"❌ Erreur ClientError lors de la récupération des événements: {str(e)}")
        return []
    
    except Exception as e:
        logging.error(f"❌ Erreur inattendue lors de la récupération des événements: {str(e)}")
        return []


