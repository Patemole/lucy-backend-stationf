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
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import uuid
import asyncio

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name="eu-west-3",
    #region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
client = OpenAI()

PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = os.getenv('INDEX_NAME')
index = pc.Index(INDEX_NAME)



# Référence à la table 
table = dynamodb.Table("test-event-HFU") 

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



def format_event(event: dict) -> str:
    """
    Convert an event dictionary into a structured natural-language sentence.
    """
    print(f"event is {event}")
    title = event.get("title", "Untitled Event")
    description = event.get("description", "No description available")
    category = event.get("category", "General")
    sub_category = event.get("sub_category", "General")
    audience = event.get("audience", "General Audience")
    organizer = event.get("organizer", "No organizer specified")
    
    # Process tags and keywords
    tags = event.get("tags", [])
    #tags_text = ", ".join(tags) if tags else "No specific tags"

    # Format the event details into a readable sentence
    event_text = f"{title}. {description} This event is organized by {organizer} under the category of {category} and sub-category of {sub_category}. "
    event_text += f"It is intended for {audience}. Tags include: {tags}."
    print(f"event formatting: {event_text}")
    return event_text


def generate_embeddings(text_list, model="text-embedding-3-small"):
    """
    Generate embeddings for a list of text inputs using OpenAI.
    Returns a list of embedding vectors.
    """
    print(f"🔹 Generating embeddings for {len(text_list)} events...")
    
    response = client.embeddings.create(input=text_list, model=model)
    embeddings = [data.embedding for data in response.data]
    print(f"✅ Generated embeddings: {len(embeddings)}!")
    return embeddings


def upload_to_pinecone():
    """
    Processes events, generates embeddings, and uploads them to Pinecone with metadata.
    """
    events = asyncio.run(fetch_events_from_dynamoDB())
    # Step 1: Convert event details into structured text
    event_texts = [format_event(event) for event in events]

    # Step 2: Generate embeddings
    embedding_vectors = generate_embeddings(event_texts)

    # Step 3: Prepare data for Pinecone
    vectors = []
    for event, embedding in zip(events, embedding_vectors):
        # Generate unique ID for each event
        event_id = str(uuid.uuid4())  # Generates a random UUID
        
        # Attach metadata
        metadata = {
            "title": event.get("title", "Untitled Event"),
            "audience": event.get("audience", "Unknown"),
            "sub_category": event.get("sub_category", "General"),
            "category": event.get("category", "General"),
            "day": event.get("day", "Unknown"),
            "description": event.get("description", "No description available"),
            "end_day": event.get("end_day", "Unknown"),
            "end_time": event.get("end_time", "Unknown"),
            "location": event.get("location", "No location specified"),
            "month": event.get("month", "Unknown"),
            "organizer": event.get("organizer", "No organizer specified"),
            "start_time": event.get("start_time", "Unknown"),
            "tags": event.get("tags", []),
            "year": event.get("year", "Unknown"),
            "banner": event.get("banner", "Unknown"),
        }

        # Append to Pinecone upload batch
        vectors.append({"id": event_id, "values": embedding, "metadata": metadata})

    # Step 4: Upload to Pinecone
    index.upsert(vectors)

    print(f"✅ Successfully uploaded {len(vectors)} events to Pinecone!")


def format_profile(profile: dict) -> str:
    """
    Convert a student profile dictionary into a structured natural-language sentence.
    """
    print(f"🔹 Formatting student profile: {profile.get('name', 'Unknown Student')}")

    name = profile.get("name", "Unknown")
    university = profile.get("university", "Unknown University")
    year = profile.get("year", "Unknown Year")
    
    faculty_list = profile.get("faculty", []) or []
    major_list = profile.get("major", []) or []
    minor_list = profile.get("minor", []) or []
    interest = profile.get("interest", "Various topics")

    description_parts = []
    if major_list:
        majors_text = " and ".join(major_list)
        description_parts.append(f"{majors_text} major")
    if minor_list:
        minors_text = " and ".join(minor_list)
        description_parts.append(f"{minors_text} minor")
    if faculty_list:
        faculty_text = " and ".join(faculty_list)
        description_parts.append(f"{faculty_text}")

    if description_parts:
        academic_desc = " and ".join(description_parts)
        profile_text = f"{name}, a {academic_desc} at {university}, class of {year}"
    else:
        profile_text = f"{name} at {university}, class of {year}"
    
    profile_text += f", is interested in {interest}."

    looking_for = []
    if profile.get("looking_for_events"):
        looking_for.append("events")
    if profile.get("looking_for_clubs"):
        looking_for.append("clubs")
    if profile.get("looking_for_internships"):
        looking_for.append("internships")
    if profile.get("looking_for_sports_events"):
        looking_for.append("sports events")

    if looking_for:
        looking_str = ", ".join(looking_for[:-1]) + f", and {looking_for[-1]}" if len(looking_for) > 1 else looking_for[0]
        profile_text += f" Looking for {looking_str}."

    print(f"✅ Formatted Profile Text: {profile_text}")
    return profile_text


def find_top_events_for_student(student_profile: dict, top_k=20):
    """
    Finds the top 5 closest events to a student's profile using Pinecone.
    """
    print("🔹 Searching for the most relevant events for the student...")

    # Step 1: Format and embed the student profile
    profile_text = format_profile(student_profile)
    profile_embedding = generate_embeddings([profile_text])[0]  

    # Step 2: Query Pinecone to find the closest events
    query_result = index.query(vector=profile_embedding, top_k=top_k, include_metadata=True)

    # Step 3: Extract and display results
    events = []
    for match in query_result["matches"]:
        event = match["metadata"]
        similarity_score = match["score"]

        events.append({
            "title": event.get("title", "Untitled Event"),
            "audience": event.get("audience", "Unknown"),
            "category": event.get("category", "General"),
            "day": event.get("day", "Unknown"),
            "description": event.get("description", "No description available"),
            "end_day": event.get("end_day", "Unknown"),
            "end_time": event.get("end_time", "Unknown"),
            "location": event.get("location", "No location specified"),
            "month": event.get("month", "Unknown"),
            "organizer": event.get("organizer", "No organizer specified"),
            "start_time": event.get("start_time", "Unknown"),
            "tags": event.get("tags", []),
            "year": event.get("year", "Unknown"),
            "banner": event.get("banner", "Unknown"),
            "sub_category": event.get("sub_category", "General"),
            "similarity_score": round(similarity_score, 4)
        })

    print(f"✅ Found {len(events)} matching events!")
    return events