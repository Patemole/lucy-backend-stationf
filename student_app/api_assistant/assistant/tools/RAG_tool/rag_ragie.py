import requests
import os
from functools import wraps
import time
import asyncio


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
async def retrieve_chunks(query, university, top_k=3, rerank=True):
    """
    Retrieve top chunks for a given query from Ragie.

    Args:
        query (str): The query string to search for.
        api_key (str): The API key for authentication.
        top_k (int): Number of top chunks to retrieve. Default is 3.
        rerank (bool): Whether to enable reranking for better results. Default is True.

    Returns:
        dict: A dictionary containing the retrieved chunks and associated metadata.
    """
    # API endpoint for retrieval
    url = 'https://api.ragie.ai/retrievals'

    
    RAGIE_API_KEY = os.getenv('RAGIE_API_KEY')

    # Prepare the headers with authorization
    headers = {
        'Authorization': f'Bearer {RAGIE_API_KEY}',
        'Content-Type': 'application/json',
    }

    # Prepare the payload with the query and retrieval settings
    payload = {
        'query': query,
        'top_k': top_k,
        'rerank': rerank,
        'partition': university
    }

    try:
        # Send the POST request to retrieve chunks
        response = requests.post(url, headers=headers, json=payload)

        # Check if the response is successful
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "query": query,
                "retrieved_chunks": result.get('scored_chunks', []),
                "metadata": {
                    "total_chunks": len(result.get('scored_chunks', [])),
                    "rerank_enabled": rerank,
                    "top_k_requested": top_k,
                    "university": university
                }
            }
        else:
            return {
                "status": "error",
                "error_message": f"Failed to retrieve chunks. Status code: {response.status_code}",
                "response_text": response.text
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
        }


