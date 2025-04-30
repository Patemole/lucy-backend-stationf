from zeroentropy import ZeroEntropy
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import time
import httpx
import urllib.parse



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


async def fetch_document_metadata(path: str, collection_name: str, api_key: str):
    """Fetches metadata for a specific document using its path."""
    url = "https://api.zeroentropy.dev/v1/documents/get-document-info"
    payload = {
        "collection_name": collection_name,
        "path": path,
        "include_content": False
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
            data = response.json()
            # Extract metadata, handle potential missing keys gracefully
            metadata = data.get('document', {}).get('metadata', {})
            if metadata:
                logging.debug(f"Successfully fetched metadata for path: {path}")
                return metadata
            else:
                logging.warning(f"No metadata found in response for path: {path}")
                return {}
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error fetching metadata for {path}: {e.response.status_code} - {e.response.text}")
        return {}
    except httpx.RequestError as e:
        logging.error(f"Request error fetching metadata for {path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error fetching metadata for {path}: {e}")
        return {}


@timing_decorator
async def search_top_pages(query: str, collection_name: str, size: int = 5):
    """
    Search for documents matching a query, retrieve top snippets, fetch their metadata,
    and return combined information.

    :param query: the search query string.
    :param collection_name: the name of the collection to search.
    :param size: the maximum number of top results to return.
    :return: a list of dictionaries, each containing 'content' and 'metadata'.
    """
    if not api_key:
        logging.error("ZeroEntropy API key not found. Cannot perform search.")
        return []

    try:
        # 1. Perform the top snippets search
        logging.info(f"Searching top snippets for query: '{query}' in collection '{collection_name}'")
        response = zclient.queries.top_snippets(
            collection_name=collection_name,
            query=query,
            k=size,
            precise_responses=True # Keep precise responses
        )
        snippet_results = response.results
        logging.info(f"Found {len(snippet_results)} snippets for query: '{query}'")

        if not snippet_results:
            return []

        # 2. Extract paths and fetch metadata concurrently
        paths_to_fetch = list(set([result.path for result in snippet_results if hasattr(result, 'path')]))
        if not paths_to_fetch:
            logging.warning("No paths found in snippet results to fetch metadata.")
            # Optionally return snippets without metadata here if desired
            # For now, we proceed assuming metadata is needed for sources
            return []

        logging.info(f"Fetching metadata for {len(paths_to_fetch)} unique paths.")
        metadata_tasks = [fetch_document_metadata(path, collection_name, api_key) for path in paths_to_fetch]
        fetched_metadata_list = await asyncio.gather(*metadata_tasks)

        # Create a mapping from path to its fetched metadata
        metadata_map = {path: metadata for path, metadata in zip(paths_to_fetch, fetched_metadata_list) if metadata}
        logging.info(f"Successfully fetched metadata for {len(metadata_map)} paths.")

        # 3. Combine snippet content with fetched metadata
        combined_results = []
        for snippet in snippet_results:
            if hasattr(snippet, 'path') and snippet.path in metadata_map:
                # Get the metadata for this snippet's path
                metadata = metadata_map[snippet.path]

                # URL-encode the file_url if it exists
                raw_file_url = metadata.get('file_url')
                encoded_file_url = raw_file_url # Default to raw if encoding fails or not needed
                if raw_file_url:
                    try:
                        # Parse the URL
                        parsed_url = urllib.parse.urlparse(raw_file_url)
                        # Decode path first in case it's partially encoded, then encode using quote_plus
                        decoded_path = urllib.parse.unquote(parsed_url.path)
                        encoded_path = urllib.parse.quote_plus(decoded_path)
                        # Reconstruct the URL with the encoded path
                        encoded_url_parts = parsed_url._replace(path=encoded_path)
                        encoded_file_url = urllib.parse.urlunparse(encoded_url_parts)
                        logging.debug(f"Encoded URL for path {snippet.path}: {encoded_file_url}")
                    except Exception as url_err:
                        logging.warning(f"Could not parse/encode file_url '{raw_file_url}': {url_err}. Using raw URL.")
                        encoded_file_url = raw_file_url # Fallback to raw

                # Create a new metadata dictionary with the potentially encoded URL
                updated_metadata = metadata.copy()
                updated_metadata['file_url'] = encoded_file_url # Store the encoded URL

                combined_results.append({
                    'content': snippet.content if hasattr(snippet, 'content') else '',
                    'metadata': updated_metadata # Use the metadata with the encoded URL
                })
            else:
                # Handle snippets whose metadata couldn't be fetched or had no path
                logging.warning(f"Could not find/fetch metadata for snippet with path: {getattr(snippet, 'path', 'N/A')}. Including content only.")
                # Decide whether to include snippets without metadata
                # Option 1: Include with empty metadata
                # combined_results.append({
                #     'content': snippet.content if hasattr(snippet, 'content') else '',
                #     'metadata': {}
                # })
                # Option 2: Skip (current implementation based on chat_creation needing metadata for sources)
                continue

        logging.info(f"Returning {len(combined_results)} combined results.")
        return combined_results

    except Exception as e:
        logging.exception(f"Error during search_top_pages: {e}") # Use exception for stack trace
        return []

