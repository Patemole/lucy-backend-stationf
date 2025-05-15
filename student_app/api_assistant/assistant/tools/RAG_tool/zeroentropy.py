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
from typing import List, Union



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
    """Fetches the full document info object for a specific document using its path."""
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
            # Extract the entire document object
            document_info = data.get('document', {})
            if document_info:
                logging.debug(f"Successfully fetched document info for path: {path}")
                return document_info # Return the whole document object
            else:
                logging.warning(f"No document info found in response for path: {path}")
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
async def search_top_pages(query: str, collection_name: str, program: Union[str, List[str]] = "all", size: int = 5):
    """
    Search for documents matching a query, retrieve top snippets, fetch their metadata,
    and return combined information.

    :param query: the search query string.
    :param collection_name: the name of the collection to search.
    :param program: the program(s) to filter by (string or list of strings). Defaults to "all".
    :param size: the maximum number of top results to return.
    :return: a list of dictionaries, each containing 'content' and 'metadata'.
    """
    if not api_key:
        logging.error("ZeroEntropy API key not found. Cannot perform search.")
        return []

    try:
        if collection_name.lower() == "kedge":
            # 1. Perform the top pages search with program filtering
            logging.info(f"Searching top pages for query: '{query}' in collection '{collection_name}' with program filter: '{program}' or 'all'")
            
            current_program_terms = []
            if isinstance(program, str):
                # If program is a string, use it as a single term (unless it's 'all')
                if program.lower() != "all":
                    current_program_terms.append(program)
            elif isinstance(program, list):
                # If program is a list, use its string elements
                for p_item in program:
                    if isinstance(p_item, str) and p_item.lower() != "all":
                        current_program_terms.append(p_item)
                    elif not isinstance(p_item, str):
                        logging.warning(f"Ignoring non-string item in program list: {p_item}")
            else:
                logging.warning(f"Program parameter has unexpected type: {type(program)}. Defaulting to effectively filter by 'all'.")

            # Add "all" to the list of terms and ensure uniqueness
            program_filter_values = list(set(current_program_terms + ["all"]))
            
            logging.info(f"Applying program filter for ZeroEntropy with values: {program_filter_values}")
              
            response = zclient.queries.top_pages(
                collection_name=collection_name,
                query=query,
                k=size,
                include_content=True,
                filter={
                    "program": { # Assuming the metadata field is named 'program'
                        "$in": program_filter_values
                    }
                }
            )
        else:
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
                # Get the full document info object for this snippet's path
                document_info = metadata_map[snippet.path]
                original_metadata = document_info.get('metadata', {}) # Get nested metadata

                # Get the top-level file_url (ZeroEntropy API URL)
                raw_file_url = document_info.get('file_url')
                encoded_file_url = raw_file_url # Default

                # URL-encode the ZeroEntropy file_url if it exists
                if raw_file_url:
                    try:
                        parsed_url = urllib.parse.urlparse(raw_file_url)
                        # Encode path + query string safely
                        encoded_path = urllib.parse.quote(parsed_url.path, safe='/')
                        encoded_query = urllib.parse.quote(parsed_url.query, safe='=&?')
                        encoded_url_parts = parsed_url._replace(path=encoded_path, query=encoded_query)
                        encoded_file_url = urllib.parse.urlunparse(encoded_url_parts)
                        logging.debug(f"Using encoded ZeroEntropy URL for path {snippet.path}: {encoded_file_url}")
                    except Exception as url_err:
                        logging.warning(f"Could not parse/encode ZeroEntropy file_url '{raw_file_url}': {url_err}. Using raw URL.")
                        encoded_file_url = raw_file_url # Fallback

                # Create the final metadata dictionary for the result
                # Using the (encoded) ZeroEntropy URL as 'file_url'
                # and filename/title from the nested metadata
                final_metadata = {
                    'file_url': encoded_file_url if encoded_file_url else '', # Use the encoded ZE URL
                    'filename': original_metadata.get('filename', ''),
                    'title': original_metadata.get('title', '')
                    # Add other fields from original_metadata if needed elsewhere
                }

                combined_results.append({
                    'content': snippet.content if hasattr(snippet, 'content') else '',
                    'metadata': final_metadata # Use the specifically constructed metadata
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

