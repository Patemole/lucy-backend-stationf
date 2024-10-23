import aiohttp
import os
from datetime import datetime
import asyncio
from functools import wraps
import time

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)

def timing_decorator(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

@timing_decorator
async def get_up_to_date_info(query, image_bool, university, username, major, minor, year, school):
    """
    Calls the Perplexity API asynchronously to retrieve up-to-date information based on the query.
    """
    logging.info(f"Retrieving up-to-date info for query: {query} from university: {university}")
    
    PPLX_API_KEY = os.getenv('PPLX_API_KEY')

    if not PPLX_API_KEY:
        logging.error("Perplexity API key not found.")
        return "Error: Perplexity API key not found."

    url = "https://api.perplexity.ai/chat/completions"  # Replace with the actual Perplexity API endpoint
    current_date = datetime.now().strftime("%B %d, %Y")

    system_prompt = (
        f"""
            You are a reliable academic advisor at {university}, and you provide accurate, up-to-date, and factual information. 
            Only research on site:{university}.edu. 
            We are currently in the Fall 2024 semester, and today's date is {current_date}.

            Student details:
            - Name: {username}
            - School: {school}
            - Year: {year}
            - Majors: {major} (can be undeclared if none)
            - Minors: {minor} (can be undeclared if none)
        """
    )

    payload = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "max_tokens": 500,
        "stream": False,
        "return_citations": True,
        "return_related_questions": True
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }

    try:
        logging.info(f"Sending request to Perplexity API for query: {query}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    logging.info("Data successfully retrieved from Perplexity API.")
                    return content
                else:
                    logging.error(f"Error: {response.status}")
                    error_message = await response.text()
                    logging.error(f"API Error response: {error_message}")
                    return f"Error: {response.status} - {error_message}"
    except Exception as e:
        logging.error(f"Error retrieving information from Perplexity API: {str(e)}")
        return f"Error retrieving information: {str(e)}"

def get_sources_json(sources):
    """
    Generates a list of sources in the specified format.

    Parameters:
    - sources (list): A list of dictionaries where each contains 'link' and 'document_name'.

    Returns:
    - list: A list of dictionaries in the required output format.
    """
    logging.info("Generating sources JSON.")
    tool_output = []

    for source in sources:
        tool_output.append({
            "answer_document": {
                "document_id": "4",  # Fixed value
                "link": source.get('url', ''),  # Dynamically fetched from input
                "document_name": source.get('name', ''),  # Dynamically fetched from input
                "source_type": "course_resource"  # Fixed value
            }
        })
    
    logging.info(f"Generated {len(tool_output)} sources.")
    return tool_output