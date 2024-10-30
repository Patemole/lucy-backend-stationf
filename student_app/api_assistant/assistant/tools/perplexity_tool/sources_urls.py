import requests
import os
import json

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Function to search for web sources using Google Custom Search JSON API
def google_source_search(query, university, num_results=3):
    print(f"QUERY FOR GOOGLE SEARCH: {query}")
    # Your Google Custom Search API key
    API_KEY = GOOGLE_API_KEY
    
    # Your Custom Search Engine ID
    SEARCH_ENGINE_ID = 'c43aac779112b4278'
    
    # Google Custom Search JSON API endpoint
    url = "https://www.googleapis.com/customsearch/v1"

    domain_restricted_query = f"{query} site:{university}.edu"
    
    # Search parameters
    params = {
        'q': domain_restricted_query,  # The search query (student's input)
        'cx': SEARCH_ENGINE_ID,  # Custom Search Engine ID
        'key': API_KEY,  # API Key
        'num': num_results,  # Number of results to return
    }
    
    # Make the request to the API
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Create a list to hold all the source results
        source_results = []
        
        # Iterate over each result to create the JSON object for each source
        if 'items' in data:
            for i, item in enumerate(data['items']):
                # Create the JSON output for each source
                result = {
                    "name": item.get('title', 'No title'),  # Changed to 'name'
                    "url": item.get('link', 'No URL')  # Changed to 'url'
                }
                source_results.append(result)
                
            return source_results  # Return the list of JSON objects as a JSON string
        
        else:
            return "No sources found"
    else:
        return f"Error: {response.status_code}, {response.text}"
