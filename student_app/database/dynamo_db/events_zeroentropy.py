from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
import time
from functools import wraps
import boto3
import os
from dotenv import load_dotenv
import json
import traceback
import logging
from typing import List, Dict
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import uuid
import asyncio
from zeroentropy import ZeroEntropy
import time
import requests
from datetime import datetime, timedelta
import calendar  # to get the number of days in a given month/year

zclient = ZeroEntropy(api_key="ze_xyS13kPdsxUu0wfT")

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
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
import time
from functools import wraps
import boto3
import os
from dotenv import load_dotenv
import json
import traceback
import logging
from typing import List, Dict
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import uuid
import asyncio
from zeroentropy import ZeroEntropy
import time
import requests
from datetime import datetime, timedelta
import calendar  # to get the number of days in a given month/year

# load environment variables
load_dotenv()

# set up zeroentropy
zclient = ZeroEntropy(api_key="ze_xyS13kPdsxUu0wfT")

# aws credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# dynamodb
dynamodb = boto3.resource(
    'dynamodb',
    region_name="eu-west-3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# openai
client = OpenAI()

# pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX_NAME = os.getenv('INDEX_NAME')
index = pc.Index(INDEX_NAME)

# reference to the table
table = dynamodb.Table("test-event-HFU") 

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

def format_profile_segments(profile: dict):
    """
    Returns two parts:
    1) A base profile text (username, year, faculty, major, minor, etc.),
    2) The list of interests as a separate list.
    """
    print(f"🔹 Formatting student profile: {profile.get('username', 'Unknown Student')}")

    username = profile.get("username", "Unknown")
    university = profile.get("university", "Unknown University")
    year = profile.get("year", "Unknown Year")
    
    faculty_list = profile.get("faculty", []) or []
    major_list = profile.get("major", []) or []
    minor_list = profile.get("minor", []) or []
    interests_list = profile.get("interests", []) or []

    # prepare the faculty text
    faculty_text = ""
    if faculty_list:
        if len(faculty_list) > 1:
            faculty_text = f"studying in {', '.join(faculty_list[:-1])}, and {faculty_list[-1]}"
        else:
            faculty_text = f"studying in {faculty_list[0]}"

    # prepare the major text
    major_text = ""
    if major_list:
        if len(major_list) > 1:
            major_text = f"majoring in {', '.join(major_list[:-1])}, and {major_list[-1]}"
        else:
            major_text = f"majoring in {major_list[0]}"
    
    # prepare the minor text
    minor_text = ""
    if minor_list:
        if len(minor_list) > 1:
            minor_text = f"and minoring in {', '.join(minor_list[:-1])}, and {minor_list[-1]}"
        else:
            minor_text = f"and minoring in {minor_list[0]}"
    
    # build the base text without explicitly listing all interests
    # (we'll handle them separately)
    base_text = f""
    if faculty_text:
        base_text += f"{faculty_text} "
    if major_text:
        base_text += f"{major_text} "
    #if minor_text:
        #base_text += f"{minor_text} "

    # trim trailing spaces
    base_text = base_text.strip()
    #base_text = ""
    if not base_text.endswith("."):
        base_text += "."

    print(f"✅ Base Profile Text: {base_text}")
    print(f"✅ Interests List: {interests_list}")

    return base_text, interests_list

def build_date_filter():
    """
    Builds the filter_criteria to retrieve events within the current week
    (monday -> sunday), even if they span two different months.
    """
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # monday
    end_of_week = start_of_week + timedelta(days=6)          # sunday

    print(f"Filtering events between {start_of_week.date()} and {end_of_week.date()}.")

    # convert to strings as needed
    year_str = str(start_of_week.year)
    start_month_str = start_of_week.strftime("%B")  
    end_month_str = end_of_week.strftime("%B")

    start_days = [f"{float(i)}" for i in range(
        start_of_week.day,
        calendar.monthrange(start_of_week.year, start_of_week.month)[1] + 1
    )]
    end_days = [f"{float(i)}" for i in range(1, end_of_week.day + 1)]

    # if the entire week is in the same month
    if start_of_week.month == end_of_week.month:
        filter_criteria = {
            "$and": [
                {
                    "year": {"$eq": year_str}
                },
                {
                    "month": {"$eq": start_month_str}
                },
                {
                    "day": {
                        "$in": [f"{float(i)}"
                                for i in range(start_of_week.day, end_of_week.day + 1)]
                    }
                }
            ]
        }
    else:
        # the week spans two different months
        filter_criteria = {
            "$and": [
                {
                    "year": {"$eq": year_str}
                },
                {
                    "$or": [
                        {
                            "$and": [
                                {"month": {"$eq": start_month_str}},
                                {"day": {"$in": start_days}}
                            ]
                        },
                        {
                            "$and": [
                                {"month": {"$eq": end_month_str}},
                                {"day": {"$in": end_days}}
                            ]
                        }
                    ]
                }
            ]
        }
    return filter_criteria

def find_top_events_for_student(student_profile: dict, top_k=5):
    """
    Finds the top closest events by:
    1) Splitting the user's profile into a base text and interest list.
    2) For each interest in the profile, builds a query text 
       (base text + a clause mentioning that single interest).
    3) Executes a query per interest using the same date filter.
    4) Combines the results into one unified list (duplicates can be deduplicated if needed).
    """

    print("🔹 Searching for the most relevant events for the student...")

    # step 1: get the base profile text and the list of interests
    base_text, interests_list = format_profile_segments(student_profile)

    # build the filter_criteria for the current week
    filter_criteria = build_date_filter()

    # the collection name/university to query
    university = student_profile.get("university", "default_university")

    # store aggregated events
    all_events = []

    # step 2: for each interest, build a new query text and run the search
    if not interests_list:
        # if the user has no interests, just query once with the base text
        query_text = base_text
        try:
            response = zclient.queries.top_pages(
                collection_name=university,
                query=query_text,
                k=top_k,
                filter=filter_criteria
            )
            events = retrieve_metadata_from_response(response, university)
            all_events.extend(events)
        except Exception as e:
            print(f"❌ Error occurred during query with no interests: {e}")
    else:
        for interest in interests_list:
            # build interest-specific text
            # e.g. "<base_text> i am interested in Robotics."
            query_text = f"{base_text}, he is interested in {interest}."
            print(f"\n🔸 Querying for interest: {interest}\nQuery Text: {query_text}\n")

            # run the search
            try:
                response = zclient.queries.top_pages(
                    collection_name=university,
                    query=query_text,
                    k=top_k,
                    filter=filter_criteria
                )
                events = retrieve_metadata_from_response(response, university)
                all_events.extend(events)
            except Exception as e:
                print(f"❌ Error occurred during query for interest '{interest}': {e}")

    # optional: deduplicate events if you want to avoid repeating the same event
    # here we can deduplicate by document path or by some unique event identifier
    # for example, we can create a dictionary keyed by (title + day + month) or by 'document_path'
    deduplicated = {}
    for evt in all_events:
        # you can combine key fields as you see fit
        # here, let's do it by (title, day, month, year) for simplicity
        key = (evt["title"], evt["day"], evt["month"], evt["year"])
        if key not in deduplicated:
            deduplicated[key] = evt
    
    final_events = list(deduplicated.values())

    print(f"\n✅ Found {len(final_events)} unique matching events across all interests!")
    return final_events

def retrieve_metadata_from_response(response, university):
    """
    Given a ZeroEntropy response, fetch the metadata for each document
    and build a list of event dictionaries.
    """
    print(f"response.results: {response.results}")
    
    url = "https://api.zeroentropy.dev/v1/documents/get-document-info"
    headers = {
        "Authorization": "Bearer ze_xyS13kPdsxUu0wfT",
        "Content-Type": "application/json"
    }

    events = []
    for match in response.results:
        document_path = match.path
        print(f"Document path: {document_path}")

        payload = {
            "collection_name": university,
            "path": document_path,
            "include_content": False
        }

        metadata_response = requests.post(url, json=payload, headers=headers)
        if metadata_response.status_code == 200:
            metadata = metadata_response.json().get("document", {}).get("metadata", {})
            similarity_score = match.score

            events.append({
                "title": metadata.get("title", "Untitled Event"),
                "audience": metadata.get("audience", "Unknown"),
                "banner": metadata.get("banner", "Unknown"),
                "category": metadata.get("category", "General"),
                "day": metadata.get("day", "Unknown"),
                "description": metadata.get("description", "No description available"),
                "end_day": metadata.get("end_day", "Unknown"),
                "end_time": metadata.get("end_time", "Unknown"),
                "location": metadata.get("location", "No location specified"),
                "month": metadata.get("month", "Unknown"),
                "organizer": metadata.get("organizer", "No organizer specified"),
                "start_time": metadata.get("start_time", "Unknown"),
                "sub_category": metadata.get("sub_category", "General"),
                "tags": metadata.get("tags", []),
                "year": metadata.get("year", "Unknown"),
                "university": metadata.get("university", "Unknown"),
                "similarity_score": round(similarity_score, 4)
            })
        else:
            print(f"❌ Failed to retrieve metadata for document {document_path}. "
                  f"Status code: {metadata_response.status_code}")

    return events


# Example usage:
if __name__ == "__main__":
    sample_profile = {
        "username": "Mathieu",
        "university": "holyfamily",
        "year": "freshman",
        "faculty": ["nursing"],
        "major": ["Computer Science"],
        "minor": [],
        "interests": ["Sports", "Robotics", "Church"]
    }

    results = find_top_events_for_student(sample_profile)
    
    print("\n🔹 **Top 5 Events for Student:**")
    for idx, event in enumerate(results, start=1):
        print(f"\n🎯 Event {idx}: {event['title']}")
        print(f"   📍 Location: {event['location']}")
        print(f"   📅 Date: {event['day']}")
        print(f"   🏛 Organizer: {event['organizer']}")
        print(f"   🎭 Category: {event['category']}")
        print(f"   👥 Audience: {event['audience']}")
        print(f"   🏷 Tags:  {event['tags']}")
        print(f"   🔢 Similarity Score: {event['similarity_score']}")

