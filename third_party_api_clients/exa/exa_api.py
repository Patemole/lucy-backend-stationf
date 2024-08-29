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
async def exa_api_url_and_summary(query: str, domain: str, keyword:str = None):
        exa_client = Exa(api_key=os.environ.get("EXA_API_KEY"))

        # summary_prompt = f"Summarize the entire content in a comprehensive and informative manner using bullet points. Include all key points, details, and data presented on the website such as links, dates or numbers. Make sure that most information is related to the query of the user: {query}"
        summary_prompt = f"Summarize the entire content in a comprehensive and informative manner using bullet points. Include all key points, details, and data presented on the website such as links, dates or numbers."

        result = exa_client.search_and_contents(
            query,
            type="auto",
            num_results=4,
            # text={
            #     "include_html_tags": True
            # },
            include_domains=[domain],
            # highlights=True,
            summary={
                "query": summary_prompt
            },
            # include_text=[keyword],
            # start_published_date="2023-12-31T23:00:01.000Z"
        )

        # url_and_summary = [{
        #     "url": search.url,
        #     "summary": search.summary 
        # }
        # for search in result.results]

        date_and_summary = ''.join([f"Published in {search.published_date}: {search.summary}\n" for search in result.results])
        print(f"DATED SUMMARY : {date_and_summary}")

        # published_date= [search.published_date for search in result.results]

        # summary= [search.summary for search in result.results]

        urls = [{
             "answer_document": {
                 "document_id": str(index + 1),
                 "link": search.url,
                 "document_name": search.title,
                 "source_type": "course_resource"
             }
        }for index, search in enumerate(result.results)]

        # {
        #     "answer_document": {
        #         "document_id": "1",
        #         "link": "http://localhost:5001/static/yc_popup/course_path@penn.html",
        #         "document_name": "Course registration PATH@PENN",
        #         "source_type": "course_resource"
        #     }
        # },

        print(f"URLS: {urls}")

        # print(f"SUMMARY: {summary}")
        return date_and_summary, urls

     