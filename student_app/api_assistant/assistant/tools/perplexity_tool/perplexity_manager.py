# backend/assistant/tools/perplexity_tool/perplexity_manager.py
import requests
import os
from datetime import datetime


def get_up_to_date_info(query, university, username, major, minor, year, school):
    """
    Calls the Perplexity API to retrieve up-to-date information based on the query.

    Parameters:
    - query (str): The user's query requiring current information.

    Returns:
    - str: The information retrieved from the Perplexity API.
    """
    # Load Perplexity API key from environment variables
    PPLX_API_KEY = os.getenv('PPLX_API_KEY')

    # Check if API key is available
    if not PPLX_API_KEY:
        return "Error: Perplexity API key not found."

    # Set up the API endpoint and headers
    url = "https://api.perplexity.ai/chat/completions"  # Replace with the actual Perplexity API endpoint

    current_date = datetime.now().strftime("%B %d, %Y")

    print(f"Query to perplexity is: {query} \n")

    system_prompt = (
        f"""
            You are a reliable academic advisor at {university}, and you provide accurate, up-to-date, and factual information. 
            You only provide answers based on current and verified data.
            Only research on site:{university}.edu 
            no other websites and sources should be used. 
            We are currently in the Fall 2024 semester and today date is {current_date} use this to make sure to have relevant information and not past information.

            information about the student:
            - His name is {username}
            - He is in the {school}
            - He is in his {year} senior
            - His majors are {major} (can be undeclared if none)
            - His minors are {minor} (can be undeclared if none)
            
            When answering the student's question you should take into acount the above information about him to only retrieve and state what is relevant for him 
        """
    )
    # Prepare the payload with system prompt and the user query
    payload = {
        "model": "llama-3.1-sonar-large-128k-online",  # Model specification
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "max_tokens": 500,
        "stream": False,
        "return_citations": True
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }

    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response (assuming JSON format)
        data = response.json()

        if response.status_code == 200:
                data = response.json()
                print("DATA FROM PPLX API /// CHECK IF CITATIONS OR NOT")
                print(data)
                content = data['choices'][0]['message']['content']
                print(content)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

        return content

    except requests.exceptions.RequestException as e:
        # Handle any exceptions related to the request
        return f"Error retrieving information: {str(e)}"
