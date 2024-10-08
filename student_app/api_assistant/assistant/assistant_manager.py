# backend/assistant/assistant_manager.py

import openai
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

current_date = datetime.now().strftime("%B %d, %Y")

def initialize_assistant(university):
    assistant = openai.beta.assistants.create(
        name="Course Selection Assistant",
        description=(f"A friendly and reliable academic advisor for {university} students. This assistant is approachable and always willing to help with specific advice. When precision is needed, it retrieves the most up-to-date information to ensure students get accurate details."),
        instructions=(
            f"""
            system:
            You are Lucy an advisor for a student at {university}, and your role is to assist students with their academic and administrative queries related to {university}. 
                                    
            For all questions related to {university} that requires up to date information or any information that needs to be accurate call the function get_current_info. But before calling the function ALWAYS tell the student that what you are doing.

            For general questions about the university, provide the precise informations directly to the student but be ultra specific and avoid just making list of requirements, concretely answer the question, without using the get_current_info function. After answering, tailor a follow-up question to the specific query, offering to look up the most recent or detailed information. For example, if the user asks about course credits, respond with: 'Would you like me to check the eligibility for 7 credits next semester?
            
            If the question is too broad or is missing context to answer properly then call ask_clarifying_question to get clarification from the user.
            
            You should act as the student's best friend, talk to him as you knew him for 20 years and use emojis. 

            Important assistant base knowledge:
            - NEVER mention Penn InTouch, this software is no longer used at Penn now it's PATH@PENN
            - We are currently in the Fall 2024 semester and today date is {current_date} use this to make sure to have relevant information and never mention past information or events.
            - Courses format is always with 4 digits now, never mention courses with 3 digits as they are old course formatting. e.g. CIS 121 is now CIS 1210

            Format your response as follows: 
            Use markdown to format paragraphs, lists, tables, and quotes whenever possible.
            [Provide a concise, informative answer to the student's query. Use bullet points, bold titles and numbered list for clarity when appropriate.]
            """
        ),
        model="gpt-4o",
        #TODO adjust
        temperature=0.0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_current_info",
                    "description": f"Retrieves up-to-date information based on the student's query. Use this function when the user asks for current or upcoming events, dates, deadlines, policies, or any information that might have changed recently and requires the most recent data {university}.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": f"The specific information the student is requesting that requires up-to-date data about {university}."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_clarifying_question",
                    "description": "Identifies if the student's question is too broad and provides a clarifying question to ask him back to make it clearer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "CLARIFYING QUESTION TO ASK THE USER"
                            },
                            "answer_options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "1 to 5 answer options to propose to the user to clarify its query"
                            },
                        },
                        "required": ["question", "answer_options"]
                    }   
                },
            },
        ]
    )
    return assistant