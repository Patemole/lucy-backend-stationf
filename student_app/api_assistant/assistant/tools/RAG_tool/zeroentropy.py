from zeroentropy import ZeroEntropy
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import time



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
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(f"Starting {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = await func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

load_dotenv()

# retrieve the api key from the environment variable
api_key = os.getenv("ZEROENTROPY_API_KEY")

# initialize the zero entropy client using the environment variable
zclient = ZeroEntropy(api_key=api_key)


@timing_decorator
async def search_top_pages(query: str, collection_name: str, size: int = 5):
    """
    search for documents matching a query and return the top pages.

    :param query: the search query string.
    :param collection_name: the name of the collection to search.
    :param size: the maximum number of top results to return.
    :return: a list of search results.
    """
    try:

        # perform the search using the zeroentropy documents.search endpoint
        response = zclient.queries.top_snippets(
            collection_name=collection_name,
            query=query,
            k=size,
            precise_responses=False
        )
        # assuming the response contains a 'documents' attribute with the results
        results = response.results
        logging.info(f"found {len(results)} results for query: '{query}'")
        aggregated_content = ""
        for doc in results:
            logging.info(f"content: {doc.content}")
            # assuming each document has metadata with a title and a score property
            aggregated_content += doc.content + "\n"
        return aggregated_content
    except Exception as e:
        logging.error(f"error during search: {e}")
        return []

