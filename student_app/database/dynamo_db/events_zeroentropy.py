import logging
from typing import Any, Dict, List, Optional
from botocore.exceptions import ClientError
import time
from functools import wraps
import boto3
import os
from dotenv import load_dotenv
import json
import traceback
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

# -------------------------------------------------------------------
# Logging configuration as requested (no additional print statements).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)
# -------------------------------------------------------------------

zclient = ZeroEntropy(api_key="ze_xyS13kPdsxUu0wfT")

# load environment variables
load_dotenv()

def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = await func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

def format_profile_segments(profile: Any):
    """
    Returns two parts:
    1) A base profile text (username, year, faculty, major, minor, etc.),
    2) The list of interests as a separate list.

    This function now uses getattr(...) instead of profile.get(...) to support
    StudentProfile objects that have attributes like 'username', 'university', etc.
    """

    # Safely retrieve each attribute with getattr
    username = getattr(profile, "username", "Unknown")
    university = getattr(profile, "university", "Unknown University")
    year = getattr(profile, "year", "Unknown Year")

    # Expecting lists for faculty, major, minor, interests
    faculty_list = getattr(profile, "faculty", []) or []
    major_list = getattr(profile, "major", []) or []
    minor_list = getattr(profile, "minor", []) or []
    interests_list = getattr(profile, "interests", []) or []

    logging.info(f"Formatting student profile: {username}")

    # Build the base text (excluding explicit interests)
    faculty_text = ""
    if faculty_list:
        if len(faculty_list) > 1:
            faculty_text = f"studying in {', '.join(faculty_list[:-1])}, and {faculty_list[-1]}"
        else:
            faculty_text = f"studying in {faculty_list[0]}"

    major_text = ""
    if major_list:
        if len(major_list) > 1:
            major_text = f"majoring in {', '.join(major_list[:-1])}, and {major_list[-1]}"
        else:
            major_text = f"majoring in {major_list[0]}"

    minor_text = ""
    if minor_list:
        if len(minor_list) > 1:
            minor_text = f"and minoring in {', '.join(minor_list[:-1])}, and {minor_list[-1]}"
        else:
            minor_text = f"and minoring in {minor_list[0]}"

    # Construct a short base text
    base_text = ""
    if faculty_text:
        base_text += f"{faculty_text} "
    if major_text:
        base_text += f"{major_text} "
    if minor_text:
        base_text += f"{minor_text} "

    base_text = base_text.strip()
    if not base_text.endswith("."):
        base_text += "."

    logging.info(f"Base Profile Text: {base_text}")
    logging.info(f"Interests List: {interests_list}")

    return base_text, interests_list

def build_date_filter():
    """
    Builds a Pinecone/ZeroEntropy filter_criteria to retrieve events
    within the current week (monday -> sunday), even if they span two months.
    """
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # monday
    end_of_week = start_of_week + timedelta(days=6)          # sunday

    logging.info(f"Filtering events between {start_of_week.date()} and {end_of_week.date()}.")

    year_str = str(start_of_week.year)
    start_month_str = start_of_week.strftime("%B")
    end_month_str = end_of_week.strftime("%B")

    start_days = [f"{float(i)}" for i in range(
        start_of_week.day,
        calendar.monthrange(start_of_week.year, start_of_week.month)[1] + 1
    )]
    end_days = [f"{float(i)}" for i in range(1, end_of_week.day + 1)]

    # If the entire week is in the same month
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
        # The week spans two different months
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
    logging.info(f"Filter criteria: {filter_criteria}")
    return filter_criteria

def retrieve_metadata_from_response(response, university: str):
    """
    Given a ZeroEntropy response, fetch the metadata for each document
    and build a list of event dictionaries.
    """
    logging.info(f"Response results: {response.results}")

    url = "https://api.zeroentropy.dev/v1/documents/get-document-info"
    headers = {
        "Authorization": "Bearer ze_xyS13kPdsxUu0wfT",
        "Content-Type": "application/json"
    }

    events = []
    for match in response.results:
        document_path = match.path
        logging.info(f"Document path: {document_path}")

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
            logging.error(f"Failed to retrieve metadata for document {document_path}. "
                          f"Status code: {metadata_response.status_code}")
    return events

def find_top_events_for_student(student_profile: Any, top_k=5):
    """
    Finds the top closest events by:
      1) Splitting the user's profile into a base text and interest list.
      2) For each interest in the profile, builds a query text 
         (base text + a clause mentioning that single interest).
      3) Executes a query per interest using the same date filter.
      4) Combines the results into one unified list (deduplicates if needed).
    """

    logging.info("Searching for the most relevant events for the student...")

    # step 1: get the base profile text and the list of interests
    base_text, interests_list = format_profile_segments(student_profile)

    # build the filter_criteria for the current week
    filter_criteria = build_date_filter()

    # Safely get the student's university (default if none provided)
    university = getattr(student_profile, "university", "default_university")

    # store aggregated events
    all_events = []

    # step 2: for each interest, build a new query text and run the search
    if not interests_list:
        # if the user has no interests, just query once with the base text
        query_text = base_text
        try:
            print(2)
            response = zclient.queries.top_documents(
                collection_name=university,
                query=query_text,
                k=top_k,
                filter=filter_criteria
            )
            events = retrieve_metadata_from_response(response, university)
            all_events.extend(events)
        except Exception as e:
            logging.error(f"Error occurred during query with no interests: {e}")
    else:
        for interest in interests_list:
            print(1)
            query_text = f"{base_text} he is interested in {interest}."
            logging.info(f"Querying for interest: {interest} | Query Text: {query_text}")

            try:
                response = zclient.queries.top_documents(
                    collection_name=university,
                    query=query_text,
                    k=top_k,
                    filter=filter_criteria
                )
                events = retrieve_metadata_from_response(response, university)
                all_events.extend(events)
            except Exception as e:
                logging.error(f"Error occurred during query for interest '{interest}': {e}")

    # optional: deduplicate events to avoid repeating the same event
    deduplicated = {}
    for evt in all_events:
        key = (evt["title"], evt["day"], evt["month"], evt["year"])
        if key not in deduplicated:
            deduplicated[key] = evt
    
    final_events = list(deduplicated.values())

    logging.info(f"Found {len(final_events)} unique matching events across all interests!")
    return final_events
