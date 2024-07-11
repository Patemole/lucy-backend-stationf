# scraping.py

import requests

def fetch_content_with_jinai(url):
    jinai_url = f"https://r.jina.ai/{url}"
    response = requests.get(jinai_url)
    
    if response.status_code == 200:
        return response.text
    else:
        return f"Error fetching content from {url}: {response.status_code}"
