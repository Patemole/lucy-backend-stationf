import os
import time
import requests
import json
import logging
from functools import wraps

from typing import List, Dict

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
PPLX_API_KEY = os.getenv("PPLX_API_KEY")


# Define the decorator
def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper


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
    "llama-3.1-sonar-small-128k-online",
    "llama-3.1-sonar-large-128k-online"
]

####################################################### INVOKE PERPLEXITY API #######################################################
def run_perplexity_API(PPLX_API_KEY, system_prompt, user_input):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
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



####################################################### STREAM PERPLEXITY API #######################################################    
def run_perplexity_API_stream(PPLX_API_KEY, system_prompt: str, user_input: str):
    from dotenv import load_dotenv
    import os

    load_dotenv()
    PPLX_API_KEY = os.getenv("PPLX_API_KEY")

    url = "https://api.perplexity.ai/chat/completions"  # Ensure this is the correct endpoint
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
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
@timing_decorator
async def LLM_pplx_stream_with_history(messages: List[Dict[str, str]], model="llama-3-sonar-small-32k-online"):
    load_dotenv()
    PPLX_API_KEY = os.getenv("PPLX_API_KEY")

    url = "https://api.perplexity.ai/chat/completions"

    if isinstance(messages, list) and all(isinstance(message, dict) for message in messages): 
        print(f"Messages: \n\n {messages} \n\n")

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0,
            "stream": True,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {PPLX_API_KEY}"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, stream=True)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8').split('data: ')[1])
                        if chunk['choices'][0]['delta'].get('content'):
                            yield chunk['choices'][0]['delta']['content'] + "|"
                    except json.JSONDecodeError as json_err:
                        logging.error(f"JSON decoding error: {json_err}")
                    except Exception as e:
                        logging.error(f"Error occurred while processing chunk: {e}")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
    else:
        raise ValueError("Invalid input. Messages must be a list of dictionaries.")
    
    
####################################################### STREAM PERPLEXITY API WITH HISTORY #######################################################




# ####################################################### TESTING #######################################################    
# ## Stream perplexity API
# system = """Act as an academic advisor named Lucy from {university}. 
# Your goal is to assist students with general guidance and provide recommendations based solely on information from {university}'s official website: site:upenn.edu.

# Format your response as follows and stricly highlight 3 sections with bold titles answer, sources and related questions in this exact order: 

# [Provide a concise, informative answer to the student's query, using only information from {university}'s website. Use bullet points and bold titles for clarity when appropriate.]
# \n\n**Sources**:
# [List at least 2-3 specific URLs from site:upenn.edu that support your answer. Format as a numbered list.]
# \n\n**Related Questions**:
# [Suggest 3 potential follow-up questions the student might have, based on your response. Present as an unordered list of bullet points.]


# Important guidelines:
# Only use information only and only from site:upenn.edu 
# Do not reference or use data from any other sources.
# If the query cannot be answered using the available information, clearly state this and suggest where the student might find the information within the university system.
# Ensure your guidance is clear, concise, and actionable.
# Tailor your tone to be helpful and supportive, appropriate for a university advisor.
# Use markdown formatting to enhance readability (e.g., bold for emphasis, headers for sections).
# """

# # # TODO: Create user prompt function to include input content
# user_input = "how do i register at upenn ?"

# # ## Invoke perplexity API
# # # run_perplexity_API(PPLX_API_KEY=PPLX_API_KEY, system_prompt=system_prompt, user_input=user_input)

# # # for content in run_perplexity_API_stream(PPLX_API_KEY=PPLX_API_KEY, system_prompt=system_prompt, user_input=user_input):
# # #     print(content, end='', flush=True)

# # ## Get chat history
# history_items = get_chat_history(chat_id="8d35f7b1-41e5-4dfe-a33d-4592f768d5d5")
# # # print(history_items)

# # ## Get messages from chat history
# messages = get_messages_from_history(history_items=history_items, n=8)
# # print('lenght of messages: ', len(messages))

# ## Reformat system prompt
# new_system_prompt = reformat_system_prompt(system_prompt=system, university="UPenn")
# print(new_system_prompt)

# # ## Set prompt with history
# prompt = set_prompt_with_history(system_prompt=new_system_prompt, user_prompt=user_input, chat_history=messages)


# # ## Stream perplexity API with history
# # for content in LLM_pplx_stream_with_history(PPLX_API_KEY=PPLX_API_KEY, messages=prompt):
# #     print(content, end='', flush=True)

# ## Use Lucy
# LLM_lucy_stream_with_history(PPLX_API_KEY=PPLX_API_KEY, messages=prompt)

# prompt =  [{'role': 'system', 'content': "Act as an academic advisor named Lucy from upenn. \nYour goal is to assist students with general guidance and provide recommendations based solely on information from upenn's official website: site:upenn.edu.\n\nFormat your response as follows and stricly highlight 3 sections with bold titles answer, sources and related questions in this exact order: \n\n[Provide a concise, informative answer to the student's query, using only information from upenn's website. Use bullet points and bold titles for clarity when appropriate.]\n\n\n**Sources**:\n[List at least 2-3 specific URLs from site:upenn.edu that support your answer. Format as a numbered list.]\n\n\n**Related Questions**:\n[Suggest 3 potential follow-up questions the student might have, based on your response. Present as an unordered list of bullet points.]\n\n\nImportant guidelines:\nOnly use information only and only from site:upenn.edu \nDo not reference or use data from any other sources.\nIf the query cannot be answered using the available information, clearly state this and suggest where the student might find the information within the university system.\nEnsure your guidance is clear, concise, and actionable.\nTailor your tone to be helpful and supportive, appropriate for a university advisor.\nUse markdown formatting to enhance readability (e.g., bold for emphasis, headers for sections).\n"}, {'role': 'user', 'content': 'what is econ0100 about ?'}, {'role': 'assistant', 'content': '**What is Econ 0100 about?**\n\nEcon 0100, titled "Introduction to Micro Economics," is an introductory course that provides an overview of economic analysis and its applications. The course covers key concepts such as the theory of supply and demand, costs and revenues of the firm under different market structures (perfect competition, monopoly, and oligopoly), pricing of factors of production, income distribution, and the theory of international trade. This course primarily focuses on microeconomics and is suitable for students with a background in mathematics and data science, as it involves the application of economic principles to real-world scenarios.\n\n**Sources**:\n1. [https://catalog.upenn.edu/courses/econ/](https://catalog.upenn.edu/courses/econ/)\n2. [https://economics.sas.upenn.edu/undergraduate/course-information](https://economics.sas.upenn.edu/undergraduate/course-information)\n\n**Related Questions**:\n- What are the specific prerequisites for Econ 0100?\n- How does Econ 0100 align with my minor in Mathematics and Data Science?\n- Can I take Econ 0100 as part of my minor in Mathematics and Data Science?'}, {'role': 'user', 'content': '\nmy student profil is: Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship and my question is whatsup ?. \nPlease only search information on this domain: site:upenn.edu and refine the search with the student profile. \nOnly mention my Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship info when needed.\n'}] 

# LLM_pplx_stream_with_history(messages=prompt)


# ####################################################### TESTING #######################################################    
