import os
import requests
import json
from typing import Optional, List, Dict

import boto3
from botocore.exceptions import ClientError


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
PPLX_API_KEY = os.getenv("PPLX_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')


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

####################################################### INVOKE PERPLEXITY API #######################################################
def run_perplexity_API(PPLX_API_KEY, system_prompt, user_input):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
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
####################################################### INVOKE PERPLEXITY API #######################################################


####################################################### RETRIEVE CHAT HISTORY #######################################################
# Configuration de la connexion à DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name="eu-west-3",  # Assurez-vous que la région est correcte
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Référence à la table 
#ADD AN ENVIRONMENT VARIABLE FOR TABLE
table = dynamodb.Table("dev_chat_academic_advisor")

def get_chat_history(chat_id):
        print("\n")
        print(f"Attempting to retrieve chat history for chat_id: {chat_id}")
        try:
            response = table.query(
                KeyConditionExpression='chat_id = :chat_id',
                ExpressionAttributeValues={':chat_id': chat_id},
                ScanIndexForward=True  # Tri ascendant par timestamp (du plus ancien au plus récent)
            )
            items = response.get('Items', [])
            print(f"Retrieved {len(items)} items from chat history.")

            return items
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Error querying chat history: {error_code} - {error_message}")
            return []
####################################################### RETRIEVE CHAT HISTORY #######################################################


####################################################### GET "N" MESSAGES FROM CHAT HISTORY #######################################################
def get_messages_from_history(history_items: List, n: Optional[int] = None) -> List[Dict[str, str]]:
    
    if n is None:
        items = history_items # Get all messages
    elif n is not None and n%2 != 0:
        n += 1
        items = history_items[-n:]
        print("Items: ", items)
    elif n is not None and n%2 == 0:
        items = history_items[-n:]
        
    messages = []

    for item in items:
        if item['username'] == "Lucy":
            message_dict = {"role": "assistant", "content": item['body']}
            messages.append(message_dict)
        else:
            message_dict = {"role": "user", "content": item['body']}
            messages.append(message_dict)
    
    print(messages)
    return messages

    
####################################################### GET "N" MESSAGES FROM CHAT HISTORY #######################################################


####################################################### SET PROMPT WITH HISTORY #######################################################
def set_prompt_with_history(system_prompt: str, chat_history: List[Dict[str, str]], user_prompt: str) -> List[Dict[str, str]]:

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        *chat_history,
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    print(messages)
    return messages
####################################################### SET PROMPT WITH HISTORY #######################################################


####################################################### STREAM PERPLEXITY API #######################################################    
def run_perplexity_API_stream(PPLX_API_KEY, system_prompt: str, user_input: str):
    url = "https://api.perplexity.ai/chat/completions"  # Ensure this is the correct endpoint
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input
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
####################################################### STREAM PERPLEXITY API #######################################################    


####################################################### STREAM PERPLEXITY API WITH HISTORY #######################################################    
def LLM_pplx_stream_with_history(PPLX_API_KEY, messages: List[Dict[str, str]]):
    url = "https://api.perplexity.ai/chat/completions"  # Ensure this is the correct endpoint
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": messages,
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
####################################################### STREAM PERPLEXITY API WITH HISTORY ####################################################### 





####################################################### TESTING #######################################################    
## Stream perplexity API
system_prompt = "Be precise and concise. "

# TODO: Create user prompt function to include input content
user_input = "What did you say for my visa ?"

## Invoke perplexity API
# run_perplexity_API(PPLX_API_KEY=PPLX_API_KEY, system_prompt=system_prompt, user_input=user_input)

# for content in run_perplexity_API_stream(PPLX_API_KEY=PPLX_API_KEY, system_prompt=system_prompt, user_input=user_input):
#     print(content, end='', flush=True)

## Get chat history
history_items = get_chat_history(chat_id="8d35f7b1-41e5-4dfe-a33d-4592f768d5d5")
# print(history_items)

## Get messages from chat history
messages = get_messages_from_history(history_items=history_items, n=8)
print('lenght of messages: ', len(messages))

## Set prompt with history
prompt = set_prompt_with_history(system_prompt=system_prompt, user_prompt=user_input, chat_history=messages)


## Stream perplexity API with history
for content in LLM_pplx_stream_with_history(PPLX_API_KEY=PPLX_API_KEY, messages=prompt):
    print(content, end='', flush=True)



####################################################### TESTING #######################################################    
