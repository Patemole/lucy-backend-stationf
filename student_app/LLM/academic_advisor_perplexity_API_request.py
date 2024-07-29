import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
PPLX_API_KEY = os.getenv("PPLX_API_KEY")



# All the available models on Perplexity
# TODO: To be updated (Last update: 29th July 2024)
models = [
    "llama-3-sonar-small-32k-online",
    "llama-3-sonar-small-32k-chat",
    "llama-3-sonar-large-32k-online",
    "llama-3-sonar-large-32k-chat", 
    "llama-3-8b-instruct", 
    "llama-3-70b-instruct", 
    "mixtral-8x7b-instruct",
]


def run_perplexity_API(PPLX_API_KEY):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "How many stars are there in our galaxy?"
            }
        ],
        "max_tokens": 30,
        "temperature": 0,
        "top_p": 0.9,
        "return_citations": True,
        "return_images": False,
        "stream": False,
        "top_k": 1024,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        json_response = response.json()
        content = json_response['choices'][0]['message']['content']
        print(content)
        return content

    except Exception as e:
        print("Error", e)

    

    
def run_perplexity_API_stream(PPLX_API_KEY):
    url = "https://api.perplexity.ai/chat/completions"  # Ensure this is the correct endpoint
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "How many stars are there in our galaxy?"
            }
        ],
        "max_tokens": 30,
        "temperature": 0,
        "top_p": 0.9,
        "return_citations": True,
        "return_images": False,
        "stream": True,
        "top_k": 1024,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }

    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8').split('data: ')[1])
                    if chunk['choices'][0]['delta'].get('content'):
                        yield chunk['choices'][0]['delta']['content']
                except (json.JSONDecodeError, IndexError):
                    continue



# run_perplexity_API(PPLX_API_KEY=PPLX_API_KEY)


# for content in run_perplexity_API_stream(PPLX_API_KEY=PPLX_API_KEY):
#     print(content, end='', flush=True)

