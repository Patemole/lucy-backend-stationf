from exa_py import Exa
import os
from functools import wraps
import time

from dotenv import load_dotenv

load_dotenv()

# Définir le décorateur
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print("For the route treatment")
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

@timing_decorator
async def exa_api_url_and_summary(query: str, keyword:str, domain: str):
        exa_client = Exa(api_key=os.environ.get("EXA_API_KEY"))

        result = exa_client.search_and_contents(
            query,
            type="auto",
            num_results=10,
            # text={
            #     "include_html_tags": True
            # },
            include_domains=[domain],
            highlights=True,
            summary={
                "query": "Summarize the entire content in a comprehensive and informative manner using bullet points. Include all key points, details, and data presented on the website such as links, dates or numbers."
            },
            include_text=[keyword],
        )

        url_and_summary = [{
            "url": search.url,
            "summary": search.summary 
        }
        for search in result.results]

        urls = [search.url for search in result.results]

        # print(url_and_summary)
        return url_and_summary, urls

     