from exa_py import Exa
import os

from dotenv import load_dotenv

load_dotenv()


def exa_api_url_and_summary(query: str, keyword:str, domain: str):
        exa_client = Exa(api_key=os.environ.get("EXA_API_KEY"))

        result = exa_client.search_and_contents(
            query,
            type="auto",
            num_results=10,
            # text={
            #     "include_html_tags": True
            # },
            include_domains=domain,
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

        # print(url_and_summary)
        return url_and_summary

# def exa_api_url