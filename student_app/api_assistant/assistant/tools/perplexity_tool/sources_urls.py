import os
import json
from urllib.parse import urlparse
import httpx  # Async HTTP client

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Async function to search for web sources using Google Custom Search JSON API
async def google_source_search(query, university, num_results=3):
    print(f"QUERY FOR GOOGLE SEARCH: {query}")
    
    # Google Custom Search API details
    API_KEY = GOOGLE_API_KEY
    SEARCH_ENGINE_ID = 'c43aac779112b4278'
    url = "https://www.googleapis.com/customsearch/v1"
    
    domain_restricted_query = f"{query} site:{university}.edu"
    
    # Search parameters
    params = {
        'q': domain_restricted_query,
        'cx': SEARCH_ENGINE_ID,
        'key': API_KEY,
        'num': num_results
    }
    
    # Make the async request to the Google Custom Search API
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Prepare list for source results
        source_results = []
        
        # Iterate over each result to create JSON object for each source
        if 'items' in data:
            for item in data['items']:
                # Extract domain and construct favicon URL
                #parsed_url = urlparse(item.get('link', ''))
                #favicon_url = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
                
                # Check if favicon URL is valid using a HEAD request
                #try:
                    #async with client.head(favicon_url, timeout=3) as favicon_response:
                        #if favicon_response.status_code != 200:
                            #favicon_url = None
                #except httpx.RequestError:
                    #favicon_url = None
                
                # Construct result JSON
                result = {
                    "name": item.get('title', 'No title'),
                    "url": item.get('link', 'No URL'),
                    #"favicon": favicon_url
                }
                source_results.append(result)
            
            return source_results
        
        else:
            return "No sources found"
    else:
        return f"Error: {response.status_code}, {response.text}"
