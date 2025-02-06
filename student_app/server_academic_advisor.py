import os
import asyncio
import logging
import datetime

from openai import OpenAI, AsyncOpenAI
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from typing import Dict, List
import json

import pandas as pd

import asyncio
import time
from student_app.database.dynamo_db.analytics import store_analytics_async

from student_app.model.input_query import InputQuery, InputQueryAI
from student_app.model.student_profile import StudentProfile
from student_app.database.dynamo_db.new_instance_chat import delete_all_items_and_adding_first_message

from student_app.database.dynamo_db.analytics import store_analytics_async
from student_app.database.dynamo_db.chat import get_chat_history, store_message_async, get_messages_from_history, get_timing_history

from student_app.profiling.profile_generation import LLM_profile_generation

from student_app.api_assistant.threads.thread_manager import (
    create_thread,
    get_cached_thread_id,
    add_user_message,
    create_and_poll_run,
    retrieve_run,
    retrieve_messages,
    add_message_to_thread
)
from student_app.api_assistant.assistant.handlers import on_event
from student_app.api_assistant.assistant.chat_creation import handle_requires_action
from student_app.api_assistant.assistant.assistant_manager import initialize_assistant

# Today's date
date = datetime.date.today()

import threading
import queue
from functools import wraps
from fastapi import BackgroundTasks
from redis.asyncio import Redis





# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)


# Environment variables
load_dotenv()

# AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
#client = OpenAI()


"""
redis_client = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,  # Enables human-readable data responses
)
"""



redis_client = Redis(
    host="cache-lucy-assistant-thread-mmmubb.serverless.use1.cache.amazonaws.com::6379",
    port=6379,
    decode_responses=True,  # Enables human-readable data responses
    ssl=True  # Required because "Encryption in Transit" is enabled
)


# FastAPI app configuration
app = FastAPI(
    title="Chat Service",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
from functools import wraps
import asyncio

client = AsyncOpenAI()

def timing_decorator(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)  # Call the synchronous function
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)  # Call the async function
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    # Check if the function is async, and return the appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper



#############################################DEUX FONCTIONS POUR LES ANALYTICS##################################

async def count_words(input_message: str) -> int:
    # Compte le nombre de mots dans la chaîne de caractères input_message
    word_count = len(input_message.split())
    print("\n")
    print("This is the number of word in the input:")
    print(word_count)
    print("\n")
    return word_count

async def count_student_questions(chat_history):
    question_count = 0
    if not chat_history:

        print("\n")
        print("This is the number of question per chat_id (first message here):")
        print(question_count)
        print("\n")
        
        return question_count
    
    for message in chat_history:
        if message['username'].lower() != 'lucy':
            question_count += 1
    
    print("\n")
    print("This is the number of question per chat_id:")
    print(question_count)
    print("\n")
    return question_count
 
@timing_decorator
async def classify_query(question: str) -> dict:
    """
    Classifies a student's question into predefined categories and generates a conversation title.
    Returns a dictionary with 'category' and 'conversation_title'.
    """

    # Define the JSON schema for the expected response
    response_schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["Financial Aids", "Events", "Policies", "Housing", "Courses", "Chitchat",]
            },
            "conversation_title": {
                "type": "string"
            }
        },
        "required": ["category", "conversation_title"],
        "additionalProperties": False
    }

    try:
        # Create the chat completion request with the specified response format
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a classifier. Categorize the user's question into one of these categories: "
                               "Financial Aids, Events, Policies, Housing, Courses, or Chitchat. "
                               "Only put Chitchat only when it is not related at all with university example: hi, how are you, what can you do etc... when the student is not asking for info but just want to talks to you otherwise choose another category"
                               "Also, generate a short conversation title using a clickbait style. "
                               "{\n"
                               '  "category": "one of: Financial Aids, Events, Policies, Housing, Courses, Chitchat",\n'
                               '  "conversation_title": "a short clickbait-style title"\n'
                               "}\n\n"
                },
                {"role": "user", "content": f"Question: {question}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "classification_response",
                    "strict": True,
                    "schema": response_schema
                }
            },
            max_tokens=100,
            temperature=0
        )

        # Extract and return the structured response
        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error in classify_query: {e}")
        # Fallback response in case of an error
        return {
            "category": "unknown",
            "conversation_title": "Untitled Conversation"
        }
############################################# END POINT FOR CHAT ##################################


# TRAITEMENT D'UN MESSAGE ÉLÈVE - Rajouter ici la fonction pour déterminer la route à choisir 
@app.post("/send_message_socratic_langgraph")
async def chat(request: Request, response: Response, input_query: InputQuery) -> StreamingResponse:
    chat_id = input_query.chat_id
    course_id = input_query.course_id
    username = input_query.username
    input_message = input_query.message
    university = input_query.university
    student_profile = input_query.student_profile
    major = input_query.major
    minor = input_query.minor
    year = input_query.year
    school = input_query.faculty
    is_first_message = input_query.is_first_message

    logging.info("this is the boolean value of is first message")
    logging.info(is_first_message)

    #logging.info(f"Redis server run: {await redis_client.ping()} for {input_message}")
    logging.info(f"Processing message from {username} at {university} for {input_message}")
    

    # Define the generator function
    @timing_decorator
    async def response_generator():
        try:
            async def background_store_message():
                try:
                    await store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message)
                    logging.info(f"Input message stored successfully in background for {input_message}")
                except Exception as e:
                    logging.error(f"Error while storing the input message in background: {str(e)} for {input_message}")

            asyncio.create_task(background_store_message())
            

            #################################NEW CODE FOR CLASSIFICATION ADDED ############################
             #NEW: classification task to get category and conversation title
            #classification_task = asyncio.create_task(classify_query(input_message))
            """
            thread_id_task = asyncio.create_task(
                get_cached_thread_id(chat_id, input_message, redis_client)
            )
            logging.info(f"Checking if thread ID in Cache for {input_message}")
            thread_id = await thread_id_task
            logging.info(f"Thread_id:{thread_id} for {input_message}")
            # Flag to track if the thread is reconstructed
            """
            reconstructed = False

            is_first_message = input_query.is_first_message
            logging.info("this is the boolean value of is first message")
            logging.info(is_first_message)

            #################################NEW CODE FOR CLASSIFICATION ADDED ############################
             #NEW: classification task to get category and conversation title
            #classification_task = asyncio.create_task(classify_query(input_message))

            # Définir la tâche de classification uniquement si is_first_message est True            
            history_items = []
        
            if is_first_message:
                print("first message task creating")
                classification_task = asyncio.create_task(classify_query(input_message))
                print(f"first message task created")
                print("awaiting task")
                classification_title_result = await classification_task
                classification_title_result = json.loads(classification_title_result)
                print(f"classification_title_result : {classification_title_result}")
                category = classification_title_result.get("category")
                conversation_title = classification_title_result.get("conversation_title")
                logging.info(f"Classification result: {classification_title_result}")
                wrapped_result = {"classification_title_result": classification_title_result}
                yield f"\n<CLASSIFICATION_AND_TITLE_RESULT>{json.dumps(wrapped_result)}<CLASSIFICATION_AND_TITLE_RESULT_END>\n"
                await asyncio.sleep(0.2)
            else:
                logging.info(f"Retrieving chat history for chat_id: {chat_id} for {input_message}")
                history_items = await get_chat_history(chat_id=chat_id)
                logging.info(f"Retrieved {len(history_items)} history items for {input_message}")
                logging.info("Skipping classification task as this is not the first message.")


            try:
                logging.info(f"Starting streaming run... for {input_message}")

                # Start the streaming run
                max_retries = 3
                retry_delay = 3  # seconds

                for attempt in range(max_retries):
                    try:
                        logging.info(f"Starting streaming run (attempt {attempt + 1}/{max_retries})... for {input_message}")
                        # Start the streaming run
                        async for data in handle_requires_action(client, university, username, major, minor, year, school, history_items, input_message):
                                if data is None:
                                    logging.info(f"Stream has completed. for {input_message}")
                                    break
                                else:
                                    yield data
                        logging.info(f"Streaming run created successfully for {input_message}")
                        break  # Exit retry loop if successful
                    except Exception as e:
                        logging.error(f"Failed to create streaming run on attempt {attempt + 1}: {str(e)} for {input_message}")
                        if attempt < max_retries - 1:
                            logging.info(f"Retrying run creation in {retry_delay} seconds... for {input_message}")
                            await asyncio.sleep(retry_delay)
                        else:
                            logging.error(f"Exceeded maximum retries for run creation for {input_message}")
                            yield f"\n<ERROR>{json.dumps({'error': 'Oops! An error occurred while finalizing your request.'})}<ERROR_END>\n"
                            return


                logging.info(f"Streaming run created and started for {input_message}")
                
            except KeyError as e:
                logging.error(f"KeyError during streaming run: {str(e)} for {input_message}", exc_info=True)
                yield f"\n<ERROR>{json.dumps({'error': 'A KeyError occurred while processing your request.'})}<ERROR_END>\n"
                return  # Stop execution after yielding the error

            except Exception as e:
                logging.error(f"Error during streaming run: {str(e)} for {input_message}", exc_info=True)
                yield f"\n<ERROR>{json.dumps({'error': 'Oops! An unexpected error occurred while processing your request.'})}<ERROR_END>\n"
                return  # Stop execution after yielding the error

        except Exception as e:
            logging.error(f"Error during response generation: {str(e)} for {input_message}")
            yield f"\n<ERROR>{json.dumps({'error': 'Error in generating response.'})}<ERROR_END>\n"
            return  # Stop execution after yielding the error
    
    try:
        logging.info(f"Received request to /send_message_socratic_langgraph for {input_message}")
        return StreamingResponse(response_generator(), media_type="text/plain")
    except Exception as e:
        logging.error(f"Error in /send_message_socratic_langgraph: {str(e)} for {input_message}")
        response.status_code = 500
        return {"error": f"Internal Server Error for {input_message}"}



# RÉCUPÉRATION DE L'HISTORIQUE DE CHAT (pour les conversations plus tard)
@app.get("/get_chat_history/{chat_id}")
async def get_chat_history_route(chat_id: str):
    return await get_chat_history(chat_id)



# SUPPRIMER L'HISTORIQUE DE CHAT CHAQUE CHARGEMENT DE LA PAGE - TO BE DEPRECIATED
@app.post("/delete_chat_history/{chat_id}")
async def delete_chat_history_route(chat_id: str):
    try:
        await delete_all_items_and_adding_first_message(chat_id)
        return {"message": "Chat history deleted successfully"}
    except Exception as e:
        logging.error(f"Erreur lors de la suppression de l'historique du chat : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'historique du chat")



# RÉCUPÉRATION DE L'HISTORIQUE DE CHAT (pour les conversations plus tard)
@app.get("/get_all_history/{timestamp}")
async def get_timing_history_route(timestamp: str):
    return await get_timing_history(timestamp)



# NOUVEL ENDPOINT POUR SAUVEGARDER LE MESSAGE AI
@timing_decorator
@app.post("/save_ai_message")
async def save_ai_message(ai_message: InputQueryAI):
    chat_id = ai_message.chatSessionId
    course_id = ai_message.courseId
    username = ai_message.username
    input_message = ai_message.input_message
    output_message = ai_message.message
    type = ai_message.type #Pas utilisé pour l'instant, on va faire la selection quand on récupérera le username if !== "Lucy" alors on mets "human" else "ai"
    uid = ai_message.uid
    university = ai_message.university

    print("input_message de l'utilisateur:")
    print(input_message)
    print("output_message de l'IA:")
    print(output_message)

    word_count_task = await count_words(input_message)

    #chat_history = await get_chat_history(chat_id)
    #number_of_question_per_chat_id = await count_student_questions(chat_history)
    #number_of_question_per_chat_id = number_of_question_per_chat_id + 1

    

    try:
        message_id = await store_message_async(chat_id, username=username, course_id=course_id, message_body=output_message)
        print(f"Stored message with ID: {message_id}")

        #data à récupérer et faire la logic 
        feedback = 'no'
        ask_for_advisor = 'no'

        #Rajouter ici la fonction pour sauvegarder les informations dans la table analytics 
       #await store_analytics_async(chat_id=chat_id, course_id=course_id, uid=uid, input_embedding=input_embeddings, output_embedding=output_embeddings, feedback=feedback, ask_for_advisor=ask_for_advisor, interaction_position=number_of_question_per_chat_id, word_count=word_count_task, ai_message_id=message_id, input_message=input_message, output_message=output_message, university=university)

    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du message AI : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du message AI")
    




#Endpoint for generate a student profile based on onboarding informations
@app.post("/student_profile")
async def create_student_profile(profile: StudentProfile):
    academic_advisor = profile.academic_advisor
    faculty = profile.faculty
    major = profile.major
    minor = profile.minor
    name = profile.name
    university = profile.university
    year = year = profile.year

    student_profile_prompt_answering = system_profile

    
    try:
        student_profile = LLM_profile_generation(name, academic_advisor, year, university, faculty, major, minor)
        return {"student_profile": student_profile}
    

    except Exception as e:
        logging.error(f"Error creating student profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating student profile")



#NOUVEAU CODE AVEC LE DEEP SEARCH ET ON LAISSE LE TAK AUSSI QUI S'ENVOIE CORRECTEMENT MAIS QUI EST MAL GÉRÉ PAR LE FRONT
import asyncio
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json

#app = FastAPI()

# Function to split text into chunks of 1-3 words, preserving formatting
def split_preserving_formatting(text):
    chunks = []
    lines = text.splitlines()

    for line in lines:
        if line.startswith("-"):
            bullet_content = line[1:].strip()
            words = bullet_content.split()
            i = 0
            while i < len(words):
                chunk_size = min(3, len(words) - i)
                chunks.append("- " + ' '.join(words[i:i + chunk_size]) if i == 0 else ' '.join(words[i:i + chunk_size]))
                i += chunk_size
        else:
            words = line.split()
            i = 0
            while i < len(words):
                chunk_size = min(3, len(words) - i)
                chunks.append(' '.join(words[i:i + chunk_size]))
                i += chunk_size
        chunks.append("\n")
    return chunks

@app.post("/send_message_fake_demo")
async def chat(request: Request, input_query: Dict) -> StreamingResponse:
    # Method for assistant API call 
    
    input_message = input_query.get("message")
    if not input_message:
        raise HTTPException(status_code=400, detail="Message is required.")

    
    # Return the response as JSON
    input_message = input_query.get("message")
    print("this is the input message")
    print(input_message)

    await asyncio.sleep(2)


    '''
    # Définition des associations de réponses graphiques
    answer_chart_associations: Dict[str, List[Dict]] = {
        "Show me some statistics": [
            {
                "answer_chart": {
                    "chartType": "bar",
                    "chartTitle": "Enrollment Statistics",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Number of Students",
                    "data": [
                        {"label": "CIS 2400", "x": 1, "y": 120},
                        {"label": "CIS 5020", "x": 2, "y": 85},
                        {"label": "CIS 1210", "x": 3, "y": 200},
                        {"label": "ESE 3060", "x": 4, "y": 60},
                    ]
                }
            }
        ],
        "What are the current student performance metrics?": [
            {
                "answer_chart": {
                    "chartType": "pie",
                    "chartTitle": "Student Performance Metrics",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Excellent", "x": 0, "y": 40},
                        {"label": "Good", "x": 0, "y": 35},
                        {"label": "Average", "x": 0, "y": 15},
                        {"label": "Below Average", "x": 0, "y": 10},
                    ]
                }
            }
        ],
        "What is the distribution of student majors?": [
            {
                "answer_chart": {
                    "chartType": "pie",
                    "chartTitle": "Distribution of Student Majors",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Computer Science", "x": 0, "y": 25},
                        {"label": "Engineering", "x": 0, "y": 20},
                        {"label": "Business", "x": 0, "y": 30},
                        {"label": "Humanities", "x": 0, "y": 15},
                        {"label": "Sciences", "x": 0, "y": 10},
                    ]
                }
            }
        ],
        "How has the enrollment trend changed over the years?": [
            {
                "answer_chart": {
                    "chartType": "line",
                    "chartTitle": "Enrollment Trend Over Years",
                    "xAxisTitle": "Year",
                    "yAxisTitle": "Number of Students",
                    "data": [
                        {"label": "2018", "x": 2018, "y": 1800},
                        {"label": "2019", "x": 2019, "y": 1900},
                        {"label": "2020", "x": 2020, "y": 1750},
                        {"label": "2021", "x": 2021, "y": 2100},
                        {"label": "2022", "x": 2022, "y": 2200},
                    ]
                }
            }
        ],
        "Show the graduation rates by department": [
            {
                "answer_chart": {
                    "chartType": "bar",
                    "chartTitle": "Graduation Rates by Department",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Graduation Rate (%)",
                    "data": [
                        {"label": "Computer Science", "x": 1, "y": 88},
                        {"label": "Engineering", "x": 2, "y": 76},
                        {"label": "Business", "x": 3, "y": 84},
                        {"label": "Humanities", "x": 4, "y": 90},
                        {"label": "Sciences", "x": 5, "y": 72},
                    ]
                }
            }
        ],
        "How is the GPA distribution across different years?": [
            {
                "answer_chart": {
                    "chartType": "line",
                    "chartTitle": "GPA Distribution Over the Years",
                    "xAxisTitle": "Year",
                    "yAxisTitle": "Average GPA",
                    "data": [
                        {"label": "2018", "x": 2018, "y": 3.2},
                        {"label": "2019", "x": 2019, "y": 3.3},
                        {"label": "2020", "x": 2020, "y": 3.25},
                        {"label": "2021", "x": 2021, "y": 3.35},
                        {"label": "2022", "x": 2022, "y": 3.4},
                    ]
                }
            }
        ],
        "What are the monthly expenses in different departments?": [
            {
                "answer_chart": {
                    "chartType": "column",
                    "chartTitle": "Monthly Departmental Expenses",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Expense ($)",
                    "data": [
                        {"label": "Computer Science", "x": 1, "y": 50000},
                        {"label": "Engineering", "x": 2, "y": 75000},
                        {"label": "Business", "x": 3, "y": 40000},
                        {"label": "Humanities", "x": 4, "y": 30000},
                        {"label": "Sciences", "x": 5, "y": 60000},
                    ]
                }
            }
        ],
        "Show the scholarship allocation by student category": [
            {
                "answer_chart": {
                    "chartType": "doughnut",
                    "chartTitle": "Scholarship Allocation by Student Category",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Merit-based", "x": 0, "y": 55},
                        {"label": "Need-based", "x": 0, "y": 30},
                        {"label": "Athletic", "x": 0, "y": 10},
                        {"label": "Diversity", "x": 0, "y": 5},
                    ]
                }
            }
        ],
        "What are the current retention rates?": [
            {
                "answer_chart": {
                    "chartType": "bar",
                    "chartTitle": "Student Retention Rates by Year",
                    "xAxisTitle": "Year",
                    "yAxisTitle": "Retention Rate (%)",
                    "data": [
                        {"label": "2019", "x": 2019, "y": 85},
                        {"label": "2020", "x": 2020, "y": 87},
                        {"label": "2021", "x": 2021, "y": 82},
                        {"label": "2022", "x": 2022, "y": 90},
                    ]
                }
            }
        ]
    }
    '''

    # Known responses with line breaks and bullet points
    '''
    known_responses: Dict[str, str] = {
        "Hey Lucy let’s plan my classes": """Hi Mathieu! Welcome back. I’m here to help you choose your courses for next semester. Let’s get started.""",
        "I want a tech elective that explore any AI topic, I don't want classes on Friday, and I don't want a project-based class": """Hi Mathieu! Welcome back. Let’s get started.""",
        "Show me some statistics": """Here are some enrollment statistics for your courses:""",  # Placeholder response for the chart
        "What are the current student performance metrics?": """Here are the current student performance metrics:""",
        "4": """Great! And how many of those classes have you already decided on?""",
        "I’ve already decided to take cis2400, cis1210, and ese3060": """Got it. So we’re looking for one more class to complete your schedule. What type of class are you looking for? \n- What requirement do you want to fulfill?\n- Do you have any preferences regarding class size?\n- Are there specific days or times that work best for you?\n- What type of assignments do you prefer? \n\n List me any details that you would like""",
        "I want a tech elective that explore any AI topic, I don't want classes on Friday, and I don't want a project-based": """Great, that gives me plenty of flexibility in finding the best course for you.\n\nJust to summarize:\n- You need one more technical elective.\n- You’re interested in AI.\n- You prefer classes with no classes on Fridays.\n- You don’t want a project-based course.\n- Class size isn’t a concern, and you’re open to any instructor.\n\nDoes that all sound correct?""",
        "Yes": """Awesome! I’ll search for the best available options based on these criteria.""",
        "CIS 5020 is good, can you tell me when and where are M.Hammish OH": """Great choice! CIS 5020 please find below details on Dr. Hammish Office Hours:""",
        "Now validate and register my choices": """Done! You’re now set for CIS 5020 - Advanced Topics in AI. You’ve got all your courses lined up for next semester:\n- **CIS 2400** on Monday and Wednesday from 3:00 PM to 5:00 PM.\n- **CIS 5020** on Monday and Wednesday from 10:00 AM to 11:30 AM.\n- **CIS 1210** on Tuesday and Thursday from 11:00 AM to 1:00 PM.\n- **ESE 3060** Lectures on Tuesday from 5:00 PM to 7:00 PM.\n\nThis semester will be a lot of work rated **9/10** for difficulty and **8/10** for work required of the classes your are taking but you will validate a lot of degree requirements.\nGo on and register for your classes on PATH@PENN:""",
        "That’s all I need for now. Thanks, Lucy!": """You’re welcome, Mathieu! Good luck with your upcoming semester. If you need anything else, just reach out. Have a great day!""",
    }
    '''

    known_responses: Dict[str, str] = {
    "Hey Lucy let’s plan my classes": """Hi Mathieu! Welcome back. I’m here to help you choose your courses for next semester. Let’s get started.""",
    "I want a tech elective that explores any AI topic, I don't want classes on Friday, and I don't want a project-based class": """Hi Mathieu! Welcome back. Let’s get started.""",
    "Show me some statistics": """Here are some enrollment statistics for your courses:\n\n- **CIS 2400**: **120 students enrolled**\n- **CIS 5020**: **85 students enrolled**\n- **CIS 1210**: **200 students enrolled**\n- **ESE 3060**: **60 students enrolled**\n\nThe most popular course this semester is **CIS 1210** with **200 students**, indicating strong interest in foundational topics.""",
    "Compare course enrollment trends": """Here is a comparison of course enrollment statistics between 2022 and 2023:\n\n- **CIS 2400**: 2022 - **120 students**, 2023 - **130 students** (Increase of 8.3%)\n- **CIS 5020**: 2022 - **85 students**, 2023 - **90 students** (Increase of 5.9%)\n- **CIS 1210**: 2022 - **200 students**, 2023 - **210 students** (Increase of 5.0%)\n- **ESE 3060**: 2022 - **60 students**, 2023 - **65 students** (Increase of 8.3%)\n\nThe data shows a consistent increase in enrollment across all courses from 2022 to 2023. **CIS 1210** remains the most popular course with the highest number of enrollments, indicating sustained strong interest in this foundational subject.""",
    "What are the current student performance metrics?": """Here are the current student performance metrics:\n\n- **40%** of students are performing at an **Excellent** level.\n- **35%** are rated as **Good**.\n- **15%** are in the **Average** category.\n- **10%** fall below average.\n\n**Actionable Insight**: A significant portion of students (40%) are excelling, showing strong academic engagement across core subjects.""",
    "What is the distribution of student majors?": """The distribution of majors among students is as follows:\n\n- **Computer Science**: **25%**\n- **Engineering**: **20%**\n- **Business**: **30%**\n- **Humanities**: **15%**\n- **Sciences**: **10%**\n\n**Insight**: The largest proportion of students, **30%**, are majoring in Business, suggesting a trend towards business-related fields.""",
    "How has the enrollment trend changed over the years?": """Here’s a look at the enrollment trends over the past years:\n\n- **2018**: **1,800 students**\n- **2019**: **1,900 students**\n- **2020**: **1,750 students**\n- **2021**: **2,100 students**\n- **2022**: **2,200 students**\n\nEnrollment has steadily increased, with a **22% rise since 2018** and a particularly strong recovery after 2020.""",
    "What is the retention rate by department?": """Here’s the retention rate by department:\n\n- **Computer Science**: **88%**\n- **Engineering**: **76%**\n- **Business**: **84%**\n- **Humanities**: **90%**\n- **Sciences**: **72%**\n\n**Insight**: The highest retention rate is in **Humanities** at **90%**, while **Sciences** show the lowest at **72%**. Focus on targeted retention programs in Sciences could improve these numbers.""",
    "What is the department budget allocation?": """Here’s the current budget allocation by department:\n\n- **Computer Science**: **80%** utilized\n- **Engineering**: **95%** utilized\n- **Business**: **60%** utilized\n- **Humanities**: **70%** utilized\n- **Sciences**: **85%** utilized\n\n**Actionable Insight**: Engineering has the highest budget utilization at **95%**, while Business has unutilized funds. Allocating funds more effectively could improve resource availability in areas with higher utilization.""",
    "What is the enrollment trend over years?": """Here’s the enrollment trend by year:\n\n- **2018**: **1,800 students**\n- **2019**: **1,900 students**\n- **2020**: **1,750 students**\n- **2021**: **2,100 students**\n- **2022**: **2,200 students**\n\n**Trend**: Enrollment shows consistent growth, especially after the recovery period in 2020, with a **22% increase since 2018**.""",
    "Show the graduation rates by department": """Here’s a breakdown of graduation rates by department:\n\n- **Computer Science**: **88%**\n- **Engineering**: **76%**\n- **Business**: **84%**\n- **Humanities**: **90%**\n- **Sciences**: **72%**\n\nThe **Humanities** department has the highest graduation rate at **90%**, while **Sciences** have the lowest at **72%**.""",
    "How is the GPA distribution across different years?": """Here’s the GPA trend over recent years:\n\n- **2018**: Average GPA of **3.2**\n- **2019**: Average GPA of **3.3**\n- **2020**: Average GPA of **3.25**\n- **2021**: Average GPA of **3.35**\n- **2022**: Average GPA of **3.4**\n\nGPAs have shown a **gradual increase** over the years, with students consistently improving performance.""",
    "What are the monthly expenses in different departments?": """Monthly expenses across departments are as follows:\n\n- **Computer Science**: **$50,000**\n- **Engineering**: **$75,000**\n- **Business**: **$40,000**\n- **Humanities**: **$30,000**\n- **Sciences**: **$60,000**\n\nThe **Engineering** department has the highest expenses at **$75,000 per month**.""",
    "Show the scholarship allocation by student category": """Here’s how scholarships are allocated:\n\n- **Merit-based**: **55%**\n- **Need-based**: **30%**\n- **Athletic**: **10%**\n- **Diversity**: **5%**\n\n**Merit-based scholarships** form the largest category, comprising **55%** of the total scholarship allocation.""",
    "What is the distribution of majors?": """Here’s the breakdown of majors across students:\n\n- **Computer Science**: **25%**\n- **Engineering**: **20%**\n- **Business**: **30%**\n- **Humanities**: **15%**\n- **Sciences**: **10%**\n\n**Insight**: Business leads as the most popular major with **30%** of students.""",
    "What is the student retention rate by department?": """Here are the student retention rates by department:\n\n- **Computer Science**: **88%**\n- **Engineering**: **76%**\n- **Business**: **84%**\n- **Humanities**: **90%**\n- **Sciences**: **72%**\n\n**Actionable Insight**: Retention is lowest in the Sciences department at **72%**. Focused support for science students could boost these rates.""",
    "What are the student scores by course?": """Here’s the distribution of average scores by course:\n\n- **CIS 2400**: **85%**\n- **CIS 5020**: **90%**\n- **CIS 1210**: **78%**\n- **ESE 3060**: **82%**\n\n**Insight**: CIS 5020 shows the highest average score, indicating strong student performance in this advanced course.""",
    "What is the distribution of scores by course?": """Here’s the score distribution by course:\n\n- **CIS 2400**: Range [65, 75, 80, 85, 95]\n- **CIS 5020**: Range [70, 80, 85, 90, 100]\n- **CIS 1210**: Range [60, 70, 75, 78, 85]\n- **ESE 3060**: Range [50, 65, 72, 80, 90]\n\n**Actionable Insight**: CIS 5020 has a higher top range, showcasing challenging assessments and high achievers.""",
    "Show the monthly expenses by department": """Here’s a breakdown of monthly expenses by department:\n\n- **Computer Science**: **$50,000**\n- **Engineering**: **$75,000**\n- **Business**: **$40,000**\n- **Humanities**: **$30,000**\n- **Sciences**: **$60,000**\n\n**Insight**: Engineering has the highest expense, suggesting substantial investments in lab resources and equipment.""",
    "What is the impact of extra-curricular activities on grades?": """Here’s the impact of extra-curricular hours on GPA:\n\n- **Student A**: 5 hours - **GPA 3.5**\n- **Student B**: 10 hours - **GPA 3.2**\n- **Student C**: 15 hours - **GPA 3.7**\n- **Student D**: 20 hours - **GPA 3.0**\n\n**Insight**: Moderate participation (10-15 hours) correlates with higher GPAs, balancing activities with academics effectively.""",
    "How does faculty feedback vary by department?": """Here’s how faculty feedback varies:\n\n- **Computer Science**: **+15** points\n- **Engineering**: **-5** points\n- **Business**: **+10** points\n- **Humanities**: **+8** points\n- **Sciences**: **-3** points\n\n**Insight**: Engineering shows a slight negative trend, while Business has highly positive feedback, reflecting effective instructional practices as you can see on graph 4.""",
    "What are the current retention rates?": """Here are the student retention rates by year:\n\n- **2019**: **85%**\n- **2020**: **87%**\n- **2021**: **82%**\n- **2022**: **90%**\n\nRetention rates reached a high of **90%** in 2022, reflecting improved support and engagement initiatives.""",
    "4": """Great! And how many of those classes have you already decided on?""",
    "I’ve already decided to take cis2400, cis1210, and ese3060": """Got it. So we’re looking for one more class to complete your schedule. What type of class are you looking for? \n- What requirement do you want to fulfill?\n- Do you have any preferences regarding class size?\n- Are there specific days or times that work best for you?\n- What type of assignments do you prefer? \n\n List me any details that you would like""",
    "I want a tech elective that explores any AI topic, I don't want classes on Friday, and I don't want a project-based": """Great, that gives me plenty of flexibility in finding the best course for you.\n\nJust to summarize:\n- You need one more technical elective.\n- You’re interested in AI.\n- You prefer classes with no classes on Fridays.\n- You don’t want a project-based course.\n- Class size isn’t a concern, and you’re open to any instructor.\n\nDoes that all sound correct?""",
    "Yes": """Awesome! I’ll search for the best available options based on these criteria.""",
    "CIS 5020 is good, can you tell me when and where are M.Hammish OH": """Great choice! CIS 5020, please find below details on Dr. Hammish's Office Hours:""",
    "Now validate and register my choices": """Done! You’re now set for CIS 5020 - Advanced Topics in AI. You’ve got all your courses lined up for next semester:\n- **CIS 2400** on Monday and Wednesday from 3:00 PM to 5:00 PM.\n- **CIS 5020** on Monday and Wednesday from 10:00 AM to 11:30 AM.\n- **CIS 1210** on Tuesday and Thursday from 11:00 AM to 1:00 PM.\n- **ESE 3060** Lectures on Tuesday from 5:00 PM to 7:00 PM.\n\nThis semester will be a lot of work rated **9/10** for difficulty and **8/10** for workload, but you will complete several degree requirements.\n\nYou can register for your classes on PATH@PENN:""",
    "That’s all I need for now. Thanks, Lucy!": """You’re welcome, Mathieu! Good luck with your upcoming semester. If you need anything else, just reach out. Have a great day!""",
    "Most common types of questions asked to Lucy across different categories?":"""**Overall Insight**: The Enrollment Assistant is seeing increased engagement in **Financial Aid (+150 questions)** and **Career Services (+100)**, highlighting these as high-importance areas. **Academic Advising** also rose by **+80 questions**, while **Program Information** and **Admission Process** inquiries stabilized or slightly decreased (**-50** and **-20**, respectively). Average question complexity remains highest in **Career Services (8.0)** and **Financial Aid (7.5)**, indicating detailed student needs in these areas. Expanding support here will likely enhance overall student satisfaction and success.""",
    "What is the average financial aid package": """Hey there! 😊 The average financial aid package at UPenn for the 2023-2024 academic year is **$66,222**. This package is more than the cost of tuition and includes grants and work-study funding. UPenn is committed to meeting 100% of demonstrated financial need for its students.\nWould you like me to check any specific details about financial aid eligibility or application processes? 💸""",
    "My parents earn $120k; how much aid could I expect?": """Hey! 😊 To give you the most accurate information about how much financial aid you might expect with a family income of $120k, I'll need to check the latest details from UPenn's financial aid office. Let me do that for you right now! 🕵️‍♂️\nI'll get back to you in a moment.\nHere's what you can expect regarding financial aid at UPenn with a family income of $120,000:\n**Financial Aid Overview**\n**Need-Blind Admissions:** UPenn is need-blind for domestic students, meaning your financial need won't affect your admission decision.\n**Expected Family Contribution (EFC):** For a family earning $120,000, the EFC might be significant, potentially ranging from $30,000 to $40,000 per year. This depends on other financial factors like savings and assets.\n**Financial Aid Package**\n**Grant Aid and Work-Study**: You might receive around $45,000 in grant aid per year, though this can vary based on your specific financial situation.\n**No Loans:** UPenn does not include loans in the financial aid packages for students with demonstrated need.\nTools for Estimation\n**Net Price Calculator:** You can use UPenn's Net Price Calculator or the MyIntuition tool for a more personalized estimate.\nIf you have any specific questions or need help with the financial aid application process, feel free to ask! Would you like me to check anything else related to financial aid? 💸""",
    "您好": """你好！😊 有什么我可以帮你的吗？如果你有关于宾夕法尼亚大学的问题，无论是学术上的还是行政上的，都可以问我哦！""",
    }


    # Dictionary to associate specific documents with certain questions/responses
    document_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                "answer_document": {
                    "document_id": "1",
                    "link": "http://localhost:5001/static/yc_popup/course_path@penn.html",
                    "document_name": "Course registration PATH@PENN",
                    "source_type": "course_resource"
                }
            },
            {
                "answer_document": {
                    "document_id": "2",
                    "link": "http://localhost:5001/static/yc_popup/syllabus_cis_5190.html",
                    "document_name": "Syllabus CIS 5190",
                    "source_type": "course_resource"
                }
            }
        ],
        "Now validate and register my choices": [
            {
                "answer_document": {
                    "document_id": "4",
                    "link": "http://localhost:5001/static/yc_popup/course_path@penn.html",
                    "document_name": "Course registration Path@penn",
                    "source_type": "course_resource"
                }
            }
        ],
        "Yes": [
            {
                "answer_document": {
                    "document_id": "5",
                    "link": "http://localhost:5001/static/yc_popup/syllabus_cis_5190.html",
                    "document_name": "Syllabus CIS 5190",
                    "source_type": "course_resource"
                }
            },

            {
                "answer_document": {
                    "document_id": "7",
                    "link": "http://localhost:5001/static/yc_popup/syllabus_cis_5190.html",
                    "document_name": "Syllabus CIS 5220",
                    "source_type": "course_resource"
                }
            },

            {
                "answer_document": {
                    "document_id": "8",
                    "link": "http://localhost:5001/static/yc_popup/syllabus_cis_5200.html",
                    "document_name": "Syllabus CIS 5200",
                    "source_type": "course_resource"
                }
            }
        ],
        "CIS 5020 is good, can you tell me when and where are M.Hammish OH": [
            {
                "answer_document": {
                    "document_id": "5",
                    "link": "http://localhost:5001/static/academic_advisor/Levine_Hall.pdf",
                    "document_name": "PennAccess: Levine Hall",
                    "source_type": "course_resource"
                }
            }
        ]
    }

    # Related questions for each response
    related_questions: Dict[str, List[str]] = {
        "That’s all I need for now. Thanks, Lucy!": [
            "What are the most popular AI courses?",
            "Can I combine AI with another elective?",
            "Is there a beginner AI course available?"
        ]
    }

    # Image associations for specific responses
    image_associations: Dict[str, List[Dict]] = {
        "CIS 5020 is good, can you tell me when and where are M.Hammish OH": [
            {
                "image_id": "img3",
                "image_url": "http://localhost:5001/static/academic_advisor/map_upenn.png",
                "image_description": "Hall Building"
            },

            {
                "image_id": "img4",
                "image_url": "http://localhost:5001/static/academic_advisor/ESE_3060_GOOD.png",
                "image_description": "Dr. Hammish"
            },

        ]
    }

    # New JSON for "answer_waiting"
    answer_waiting_associations: Dict[str, List[Dict]] = {
        "Yes": [
            {
                    "Sentence1": "Deep Searching begin...",
                    "Sentence2": "Navigating through 6 different sources...",
                    "Sentence3": "One last effort..."
            }
        ]
    }


    answer_reddit_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "comment": "UPenn is amazing but intense! Make sure to balance academics with social life—it’s easy to get swept up in the pace. Use campus resources like the Weingarten Learning Center for academic support and CAPS for mental health. And don’t underestimate the power of a solid group of friends who get what you’re going through!",
                    "score": "1.1k",
            }
        ]
    }


    '''
    answer_instagram_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "title": "What is the BEST things about Upenn?",
                    "nbr_view": "15k",
                    "link": "https://ui.shadcn.com/",
                    "picture":"http://localhost:5001/static/academic_advisor/short_insta.png"
            }
        ]
    }
    '''


    answer_instagram_club_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "username": "@penngleeclub",
                    "title": "Penn Glee Club",
                    "followers": "2.1k",
                    "posts": "327",
                    "link": 'https://www.instagram.com/penngleeclub/',
                    "picture":"http://localhost:5001/static/academic_advisor/insta_club.png"
            }
        ]
    }

    answer_linkedin_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "name": "Peter Mellark",
                    "picture": "http://localhost:5001/static/academic_advisor/picture_linkedin2.png",
                    "headline": "http://localhost:5001/static/academic_advisor/banniere_linkedin.png",
                    "sentence":"Wharton MBA Candidate",
                    "link": "https://www.linkedin.com/in/lyla-jones-550348138/",
            }
        ]
    }

    
    answer_youtube_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "title": "A day in the life at UPenn",
                    "link": "https://www.youtube.com/watch?v=o2f-4h03XfY",
                    'miniature':"http://localhost:5001/static/academic_advisor/mini_youtube.png",
                    "nbr_view": "187k",
            },

            {
                    "title": "Ultimate Freshman Housing Tour (2024)",
                    "link": "https://www.youtube.com/watch?v=-82kDMIikZw",
                    'miniature':"http://localhost:5001/static/academic_advisor/mini_youtube2.png",
                    "nbr_view": "19k",
            }
        ]
    }


    answer_quora_associations: Dict[str, List[Dict]] = {
        "I’ve already decided to take cis2400, cis1210, and ese3060": [
            {
                    "comment": "To get the most out of UPenn, dive into every opportunity—join clubs, go to events, and push yourself to explore new things. The relationships you build, from classmates to alumni, have a lasting impact. Take advantage of everything UPenn and Philly have to offer—it’s all part of the journey!",
                    "score": "5.2k",
            }
        ]
    }
    


    # Dictionary for answer_TAK associated with specific input messages
    answer_TAK_associations: Dict[str, List[Dict]] = {
        "Hey Lucy let’s plan my classes": [
            {
                "document_id": "4",
                "question": "How many classes are you planning to take next semester?",
                "answer_options": [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5"
                ],
                "other_specification": {
                    "label": "If other, please specify",
                    "placeholder": "e.g., None"
                }
            }
        ]
    }

    ''' WITH OLD INTERFACE WITH NO MULTIPLE SERIES
    answer_chart_associations: Dict[str, List[Dict]] = {
        "Show me some statistics": [
            {
                "answer_chart": {
                    "chartType": "bar",
                    "chartTitle": "Enrollment Statistics",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Number of Students",
                    "data": [
                        {"label": "CIS 2400", "x": 1, "y": 120},
                        {"label": "CIS 5020", "x": 2, "y": 85},
                        {"label": "CIS 1210", "x": 3, "y": 200},
                        {"label": "ESE 3060", "x": 4, "y": 60},
                    ]
                }
            }
        ],
        "What are the current student performance metrics?": [
            {
                "answer_chart": {
                    "chartType": "pie",
                    "chartTitle": "Student Performance Metrics",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Excellent", "x": 0, "y": 40},
                        {"label": "Good", "x": 0, "y": 35},
                        {"label": "Average", "x": 0, "y": 15},
                        {"label": "Below Average", "x": 0, "y": 10},
                    ]
                }
            }
        ],
        "What is the enrollment trend over years?": [
            {
                "answer_chart": {
                    "chartType": "line",
                    "chartTitle": "Enrollment Trend Over Years",
                    "xAxisTitle": "Year",
                    "yAxisTitle": "Number of Students",
                    "data": [
                        {"label": "2018", "x": 2018, "y": 1800},
                        {"label": "2019", "x": 2019, "y": 1900},
                        {"label": "2020", "x": 2020, "y": 1750},
                        {"label": "2021", "x": 2021, "y": 2100},
                        {"label": "2022", "x": 2022, "y": 2200},
                    ]
                }
            }
        ],
        "What is the retention rate by department?": [
            {
                "answer_chart": {
                    "chartType": "pyramid",
                    "chartTitle": "Student Retention Rate by Department",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Retention Rate (%)",
                    "data": [
                        {"label": "Computer Science", "x": 1, "y": 88},
                        {"label": "Engineering", "x": 2, "y": 76},
                        {"label": "Business", "x": 3, "y": 84},
                        {"label": "Humanities", "x": 4, "y": 90},
                        {"label": "Sciences", "x": 5, "y": 72},
                    ]
                }
            }
        ],
        "What is the department budget allocation?": [
            {
                "answer_chart": {
                    "chartType": "gauge",
                    "chartTitle": "Department Budget Utilization",
                    "xAxisTitle": "",
                    "yAxisTitle": "Utilization (%)",
                    "data": [
                        {"label": "Computer Science", "x": 0, "y": 80},
                        {"label": "Engineering", "x": 0, "y": 95},
                        {"label": "Business", "x": 0, "y": 60},
                        {"label": "Humanities", "x": 0, "y": 70},
                        {"label": "Sciences", "x": 0, "y": 85},
                    ]
                }
            }
        ],
        "What is the distribution of majors?": [
            {
                "answer_chart": {
                    "chartType": "treemap",
                    "chartTitle": "Distribution of Student Majors",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Computer Science", "x": 0, "y": 25},
                        {"label": "Engineering", "x": 0, "y": 20},
                        {"label": "Business", "x": 0, "y": 30},
                        {"label": "Humanities", "x": 0, "y": 15},
                        {"label": "Sciences", "x": 0, "y": 10},
                    ]
                }
            }
        ],
        "What are the student scores by course?": [
            {
                "answer_chart": {
                    "chartType": "scatter",
                    "chartTitle": "Student Scores by Course",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Score (%)",
                    "data": [
                        {"label": "CIS 2400", "x": 1, "y": 85},
                        {"label": "CIS 5020", "x": 2, "y": 90},
                        {"label": "CIS 1210", "x": 3, "y": 78},
                        {"label": "ESE 3060", "x": 4, "y": 82},
                    ]
                }
            }
        ],
        "Show the monthly expenses by department": [
            {
                "answer_chart": {
                    "chartType": "heatmap",
                    "chartTitle": "Monthly Departmental Expenses",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Months",
                    "data": [
                        {"label": "Computer Science", "x": 1, "y": 50000},
                        {"label": "Engineering", "x": 2, "y": 75000},
                        {"label": "Business", "x": 3, "y": 40000},
                        {"label": "Humanities", "x": 4, "y": 30000},
                        {"label": "Sciences", "x": 5, "y": 60000},
                    ]
                }
            }
        ],
        "What is the distribution of scores by course?": [
            {
                "answer_chart": {
                    "chartType": "boxplot",
                    "chartTitle": "Score Distribution by Course",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Score Range",
                    "data": [
                        {"label": "CIS 2400", "x": 1, "y": [65, 75, 80, 85, 95]},
                        {"label": "CIS 5020", "x": 2, "y": [70, 80, 85, 90, 100]},
                        {"label": "CIS 1210", "x": 3, "y": [60, 70, 75, 78, 85]},
                        {"label": "ESE 3060", "x": 4, "y": [50, 65, 72, 80, 90]},
                    ]
                }
            }
        ],
        "What is the scholarship allocation by student category?": [
            {
                "answer_chart": {
                    "chartType": "doughnut",
                    "chartTitle": "Scholarship Allocation by Student Category",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "data": [
                        {"label": "Merit-based", "x": 0, "y": 55},
                        {"label": "Need-based", "x": 0, "y": 30},
                        {"label": "Athletic", "x": 0, "y": 10},
                        {"label": "Diversity", "x": 0, "y": 5},
                    ]
                }
            }
        ],
        "What is the impact of extra-curricular activities on grades?": [
            {
                "answer_chart": {
                    "chartType": "bubble",
                    "chartTitle": "Impact of Extra-Curricular on Grades",
                    "xAxisTitle": "Hours Spent in Activities",
                    "yAxisTitle": "GPA",
                    "data": [
                        {"label": "Student A", "x": 5, "y": 3.5, "z": 10},
                        {"label": "Student B", "x": 10, "y": 3.2, "z": 20},
                        {"label": "Student C", "x": 15, "y": 3.7, "z": 30},
                        {"label": "Student D", "x": 20, "y": 3.0, "z": 40},
                    ]
                }
            }
        ],
        "How does faculty feedback vary by department?": [
            {
                "answer_chart": {
                    "chartType": "waterfall",
                    "chartTitle": "Faculty Feedback by Department",
                    "xAxisTitle": "Department",
                    "yAxisTitle": "Feedback Score Change",
                    "data": [
                        {"label": "Computer Science", "x": 1, "y": 15},
                        {"label": "Engineering", "x": 2, "y": -5},
                        {"label": "Business", "x": 3, "y": 10},
                        {"label": "Humanities", "x": 4, "y": 8},
                        {"label": "Sciences", "x": 5, "y": -3},
                    ]
                }
            }
        ]
    }
    '''
    answer_chart_associations: Dict[str, List[Dict]] = {
        "Compare course enrollment trends": [
            {
                "answer_chart": {
                    "chartType": "bar",
                    "chartTitle": "Enrollment Statistics by Course (2022 vs 2023)",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Number of Students",
                    "series": [
                        {
                            "seriesName": "2023",
                            "data": [
                                {"label": "CIS 2400", "x": 1, "y": 130},
                                {"label": "CIS 5020", "x": 2, "y": 90},
                                {"label": "CIS 1210", "x": 3, "y": 210},
                                {"label": "ESE 3060", "x": 4, "y": 65}
                            ]
                        },
                        {
                            "seriesName": "2022",
                            "data": [
                                {"label": "CIS 2400", "x": 1, "y": 120},
                                {"label": "CIS 5020", "x": 2, "y": 85},
                                {"label": "CIS 1210", "x": 3, "y": 200},
                                {"label": "ESE 3060", "x": 4, "y": 60}
                            ]
                        }
                    ]
                }
            }
        ],
        "What are the current student performance metrics?": [
            {
                "answer_chart": {
                    "chartType": "pie",
                    "chartTitle": "Student Performance Metrics (2023)",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "series": [
                        {
                            "seriesName": "Performance Levels",
                            "data": [
                                {"label": "Excellent", "x": 0, "y": 42},
                                {"label": "Good", "x": 0, "y": 32},
                                {"label": "Average", "x": 0, "y": 18},
                                {"label": "Below Average", "x": 0, "y": 8}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the enrollment trend over years?": [
            {
                "answer_chart": {
                    "chartType": "line",
                    "chartTitle": "Enrollment Trend Over Years (2018-2023)",
                    "xAxisTitle": "Year",
                    "yAxisTitle": "Number of Students",
                    "series": [
                        {
                            "seriesName": "Undergraduate",
                            "data": [
                                {"label": "2018", "x": 2018, "y": 1850},
                                {"label": "2019", "x": 2019, "y": 1900},
                                {"label": "2020", "x": 2020, "y": 1780},
                                {"label": "2021", "x": 2021, "y": 2050},
                                {"label": "2022", "x": 2022, "y": 2200},
                                {"label": "2023", "x": 2023, "y": 2250}
                            ]
                        },
                        {
                            "seriesName": "Graduate",
                            "data": [
                                {"label": "2018", "x": 2018, "y": 1100},
                                {"label": "2019", "x": 2019, "y": 1150},
                                {"label": "2020", "x": 2020, "y": 1050},
                                {"label": "2021", "x": 2021, "y": 1300},
                                {"label": "2022", "x": 2022, "y": 1350},
                                {"label": "2023", "x": 2023, "y": 1450}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the retention rate by department?": [
            {
                "answer_chart": {
                    "chartType": "pyramid",
                    "chartTitle": "Student Retention Rate by Department",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Retention Rate (%)",
                    "series": [
                        {
                            "seriesName": "2023",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 92},
                                {"label": "Engineering", "x": 2, "y": 78},
                                {"label": "Business", "x": 3, "y": 87},
                                {"label": "Humanities", "x": 4, "y": 91},
                                {"label": "Sciences", "x": 5, "y": 74}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the department budget allocation?": [
            {
                "answer_chart": {
                    "chartType": "gauge",
                    "chartTitle": "Department Budget Utilization (2023)",
                    "xAxisTitle": "",
                    "yAxisTitle": "Utilization (%)",
                    "series": [
                        {
                            "seriesName": "2023 Budget Utilization",
                            "data": [
                                {"label": "Computer Science", "x": 0, "y": 85},
                                {"label": "Engineering", "x": 0, "y": 92},
                                {"label": "Business", "x": 0, "y": 65},
                                {"label": "Humanities", "x": 0, "y": 78},
                                {"label": "Sciences", "x": 0, "y": 89}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the distribution of majors?": [
            {
                "answer_chart": {
                    "chartType": "treemap",
                    "chartTitle": "Distribution of Student Majors (2023)",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "series": [
                        {
                            "seriesName": "Major Distribution",
                            "data": [
                                {"label": "Computer Science", "x": 0, "y": 28},
                                {"label": "Engineering", "x": 0, "y": 22},
                                {"label": "Business", "x": 0, "y": 30},
                                {"label": "Humanities", "x": 0, "y": 12},
                                {"label": "Sciences", "x": 0, "y": 8}
                            ]
                        }
                    ]
                }
            }
        ],
        "What are the student scores by course?": [
            {
                "answer_chart": {
                    "chartType": "scatter",
                    "chartTitle": "Average Student Scores by Course (2023)",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Average Score (%)",
                    "series": [
                        {
                            "seriesName": "2023 Scores",
                            "data": [
                                {"label": "CIS 2400", "x": 1, "y": 85},
                                {"label": "CIS 5020", "x": 2, "y": 90},
                                {"label": "CIS 1210", "x": 3, "y": 78},
                                {"label": "ESE 3060", "x": 4, "y": 82}
                            ]
                        }
                    ]
                }
            }
        ],
        "Show the monthly expenses by department": [
            {
                "answer_chart": {
                    "chartType": "heatmap",
                    "chartTitle": "Monthly Departmental Expenses (2023)",
                    "xAxisTitle": "Departments",
                    "yAxisTitle": "Months",
                    "series": [
                        {
                            "seriesName": "2023 Monthly Expenses",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 52000},
                                {"label": "Engineering", "x": 2, "y": 78000},
                                {"label": "Business", "x": 3, "y": 42000},
                                {"label": "Humanities", "x": 4, "y": 31000},
                                {"label": "Sciences", "x": 5, "y": 62000}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the distribution of scores by course?": [
            {
                "answer_chart": {
                    "chartType": "boxplot",
                    "chartTitle": "Score Distribution by Course (2023)",
                    "xAxisTitle": "Courses",
                    "yAxisTitle": "Score Range",
                    "series": [
                        {
                            "seriesName": "Score Range",
                            "data": [
                                {"label": "CIS 2400", "x": 1, "y": [65, 75, 82, 85, 95]},
                                {"label": "CIS 5020", "x": 2, "y": [70, 80, 85, 90, 100]},
                                {"label": "CIS 1210", "x": 3, "y": [60, 70, 75, 78, 85]},
                                {"label": "ESE 3060", "x": 4, "y": [50, 65, 72, 80, 90]}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the scholarship allocation by student category?": [
            {
                "answer_chart": {
                    "chartType": "doughnut",
                    "chartTitle": "Scholarship Allocation by Student Category (2023)",
                    "xAxisTitle": "",
                    "yAxisTitle": "",
                    "series": [
                        {
                            "seriesName": "Scholarship Allocation",
                            "data": [
                                {"label": "Merit-based", "x": 0, "y": 50},
                                {"label": "Need-based", "x": 0, "y": 35},
                                {"label": "Athletic", "x": 0, "y": 10},
                                {"label": "Diversity", "x": 0, "y": 5}
                            ]
                        }
                    ]
                }
            }
        ],
        "What is the impact of extra-curricular activities on grades?": [
            {
                "answer_chart": {
                    "chartType": "bubble",
                    "chartTitle": "Impact of Extra-Curricular Activities on GPA (2023)",
                    "xAxisTitle": "Hours Spent in Activities",
                    "yAxisTitle": "GPA",
                    "series": [
                        {
                            "seriesName": "Extra-Curricular Impact",
                            "data": [
                                {"label": "Student A", "x": 5, "y": 3.6, "z": 10},
                                {"label": "Student B", "x": 10, "y": 3.3, "z": 20},
                                {"label": "Student C", "x": 15, "y": 3.7, "z": 30},
                                {"label": "Student D", "x": 20, "y": 3.2, "z": 40}
                            ]
                        }
                    ]
                }
            }
        ],
        "How does faculty feedback vary by department?": [
        {
            "answer_charts": [
                {
                    "chartType": "waterfall",
                    "chartTitle": "Faculty Feedback Score Change by Department",
                    "xAxisTitle": "Department",
                    "yAxisTitle": "Feedback Score Change",
                    "series": [
                        {
                            "seriesName": "Feedback Change 2024",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 20},
                                {"label": "Engineering", "x": 2, "y": -8},
                                {"label": "Business", "x": 3, "y": 12},
                                {"label": "Humanities", "x": 4, "y": 9},
                                {"label": "Sciences", "x": 5, "y": -5}
                            ]
                        },
                        {
                            "seriesName": "Feedback Change 2023",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 15},
                                {"label": "Engineering", "x": 2, "y": -3},
                                {"label": "Business", "x": 3, "y": 10},
                                {"label": "Humanities", "x": 4, "y": 7},
                                {"label": "Sciences", "x": 5, "y": -2}
                            ]
                        }
                    ]
                },
                {
                    "chartType": "bubble",
                    "chartTitle": "Faculty Satisfaction by Department",
                    "xAxisTitle": "Department",
                    "yAxisTitle": "Satisfaction Score",
                    "series": [
                        {
                            "seriesName": "Satisfaction Level 2024",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 4.2, "z": 30},
                                {"label": "Engineering", "x": 2, "y": 3.8, "z": 25},
                                {"label": "Business", "x": 3, "y": 4.5, "z": 35},
                                {"label": "Humanities", "x": 4, "y": 4.0, "z": 28},
                                {"label": "Sciences", "x": 5, "y": 3.7, "z": 20}
                            ]
                        },
                        {
                            "seriesName": "Satisfaction Level 2023",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 4.0, "z": 28},
                                {"label": "Engineering", "x": 2, "y": 3.6, "z": 23},
                                {"label": "Business", "x": 3, "y": 4.3, "z": 33},
                                {"label": "Humanities", "x": 4, "y": 3.9, "z": 27},
                                {"label": "Sciences", "x": 5, "y": 3.5, "z": 18}
                            ]
                        }
                    ]
                },
                {
                    "chartType": "line",
                    "chartTitle": "Faculty Interaction Hours by Department",
                    "xAxisTitle": "Department",
                    "yAxisTitle": "Interaction Hours",
                    "series": [
                        {
                            "seriesName": "Interaction Hours 2024",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 25},
                                {"label": "Engineering", "x": 2, "y": 30},
                                {"label": "Business", "x": 3, "y": 28},
                                {"label": "Humanities", "x": 4, "y": 18},
                                {"label": "Sciences", "x": 5, "y": 20}
                            ]
                        },
                        {
                            "seriesName": "Interaction Hours 2023",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 20},
                                {"label": "Engineering", "x": 2, "y": 25},
                                {"label": "Business", "x": 3, "y": 22},
                                {"label": "Humanities", "x": 4, "y": 15},
                                {"label": "Sciences", "x": 5, "y": 18}
                            ]
                        }
                    ]
                },
                {
                    "chartType": "bar",
                    "chartTitle": "Faculty Research Publications by Department",
                    "xAxisTitle": "Department",
                    "yAxisTitle": "Number of Publications",
                    "series": [
                        {
                            "seriesName": "Publications 2024",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 50},
                                {"label": "Engineering", "x": 2, "y": 40},
                                {"label": "Business", "x": 3, "y": 35},
                                {"label": "Humanities", "x": 4, "y": 30},
                                {"label": "Sciences", "x": 5, "y": 45}
                            ]
                        },
                        {
                            "seriesName": "Publications 2023",
                            "data": [
                                {"label": "Computer Science", "x": 1, "y": 45},
                                {"label": "Engineering", "x": 2, "y": 38},
                                {"label": "Business", "x": 3, "y": 32},
                                {"label": "Humanities", "x": 4, "y": 28},
                                {"label": "Sciences", "x": 5, "y": 40}
                            ]
                        }
                    ]
                }
            ]
        }
    ],
    "Most common types of questions asked to Lucy across different categories?": [
    {
        "answer_charts": [
            {
                "chartType": "waterfall",
                "chartTitle": "Change in Number of Questions by Category",
                "xAxisTitle": "Category",
                "yAxisTitle": "Change in Number of Questions",
                "series": [
                    {
                        "seriesName": "Change 2024",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 150},
                            {"label": "Program Information", "x": 2, "y": -50},
                            {"label": "Career Services", "x": 3, "y": 100},
                            {"label": "Academic Advising", "x": 4, "y": 80},
                            {"label": "Admission Process", "x": 5, "y": -20}
                        ]
                    },
                    {
                        "seriesName": "Change 2023",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 100},
                            {"label": "Program Information", "x": 2, "y": -30},
                            {"label": "Career Services", "x": 3, "y": 90},
                            {"label": "Academic Advising", "x": 4, "y": 70},
                            {"label": "Admission Process", "x": 5, "y": -10}
                        ]
                    }
                ]
            },
            {
                "chartType": "bubble",
                "chartTitle": "Question Complexity by Category",
                "xAxisTitle": "Category",
                "yAxisTitle": "Average Complexity Score",
                "series": [
                    {
                        "seriesName": "Complexity 2024",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 7.5, "z": 300},
                            {"label": "Program Information", "x": 2, "y": 6.2, "z": 250},
                            {"label": "Career Services", "x": 3, "y": 8.0, "z": 320},
                            {"label": "Academic Advising", "x": 4, "y": 7.0, "z": 280},
                            {"label": "Admission Process", "x": 5, "y": 6.5, "z": 200}
                        ]
                    },
                    {
                        "seriesName": "Complexity 2023",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 7.0, "z": 280},
                            {"label": "Program Information", "x": 2, "y": 6.0, "z": 230},
                            {"label": "Career Services", "x": 3, "y": 7.8, "z": 310},
                            {"label": "Academic Advising", "x": 4, "y": 6.8, "z": 260},
                            {"label": "Admission Process", "x": 5, "y": 6.3, "z": 190}
                        ]
                    }
                ]
            },
            {
                "chartType": "line",
                "chartTitle": "Trend in Number of Questions Over Time by Category",
                "xAxisTitle": "Month",
                "yAxisTitle": "Number of Questions",
                "series": [
                    {
                        "seriesName": "Financial Aid",
                        "data": [
                            {"label": "Jan", "x": 1, "y": 120},
                            {"label": "Feb", "x": 2, "y": 130},
                            {"label": "Mar", "x": 3, "y": 140},
                            {"label": "Apr", "x": 4, "y": 150},
                            {"label": "May", "x": 5, "y": 160},
                            {"label": "Jun", "x": 6, "y": 170},
                            {"label": "Jul", "x": 7, "y": 180},
                            {"label": "Aug", "x": 8, "y": 190},
                            {"label": "Sep", "x": 9, "y": 200},
                            {"label": "Oct", "x": 10, "y": 210},
                            {"label": "Nov", "x": 11, "y": 220},
                            {"label": "Dec", "x": 12, "y": 230}
                        ]
                    },
                    {
                        "seriesName": "Program Information",
                        "data": [
                            {"label": "Jan", "x": 1, "y": 80},
                            {"label": "Feb", "x": 2, "y": 85},
                            {"label": "Mar", "x": 3, "y": 90},
                            {"label": "Apr", "x": 4, "y": 95},
                            {"label": "May", "x": 5, "y": 100},
                            {"label": "Jun", "x": 6, "y": 105},
                            {"label": "Jul", "x": 7, "y": 110},
                            {"label": "Aug", "x": 8, "y": 115},
                            {"label": "Sep", "x": 9, "y": 120},
                            {"label": "Oct", "x": 10, "y": 125},
                            {"label": "Nov", "x": 11, "y": 130},
                            {"label": "Dec", "x": 12, "y": 135}
                        ]
                    },
                    {
                        "seriesName": "Career Services",
                        "data": [
                            {"label": "Jan", "x": 1, "y": 100},
                            {"label": "Feb", "x": 2, "y": 110},
                            {"label": "Mar", "x": 3, "y": 120},
                            {"label": "Apr", "x": 4, "y": 130},
                            {"label": "May", "x": 5, "y": 140},
                            {"label": "Jun", "x": 6, "y": 150},
                            {"label": "Jul", "x": 7, "y": 160},
                            {"label": "Aug", "x": 8, "y": 170},
                            {"label": "Sep", "x": 9, "y": 180},
                            {"label": "Oct", "x": 10, "y": 190},
                            {"label": "Nov", "x": 11, "y": 200},
                            {"label": "Dec", "x": 12, "y": 210}
                        ]
                    },
                    {
                        "seriesName": "Academic Advising",
                        "data": [
                            {"label": "Jan", "x": 1, "y": 90},
                            {"label": "Feb", "x": 2, "y": 95},
                            {"label": "Mar", "x": 3, "y": 100},
                            {"label": "Apr", "x": 4, "y": 105},
                            {"label": "May", "x": 5, "y": 110},
                            {"label": "Jun", "x": 6, "y": 115},
                            {"label": "Jul", "x": 7, "y": 120},
                            {"label": "Aug", "x": 8, "y": 125},
                            {"label": "Sep", "x": 9, "y": 130},
                            {"label": "Oct", "x": 10, "y": 135},
                            {"label": "Nov", "x": 11, "y": 140},
                            {"label": "Dec", "x": 12, "y": 145}
                        ]
                    },
                    {
                        "seriesName": "Admission Process",
                        "data": [
                            {"label": "Jan", "x": 1, "y": 70},
                            {"label": "Feb", "x": 2, "y": 75},
                            {"label": "Mar", "x": 3, "y": 80},
                            {"label": "Apr", "x": 4, "y": 85},
                            {"label": "May", "x": 5, "y": 90},
                            {"label": "Jun", "x": 6, "y": 95},
                            {"label": "Jul", "x": 7, "y": 100},
                            {"label": "Aug", "x": 8, "y": 105},
                            {"label": "Sep", "x": 9, "y": 110},
                            {"label": "Oct", "x": 10, "y": 115},
                            {"label": "Nov", "x": 11, "y": 120},
                            {"label": "Dec", "x": 12, "y": 125}
                        ]
                    }
                ]
            },
            {
                "chartType": "bar",
                "chartTitle": "Top 5 Most Asked Question Types by Category",
                "xAxisTitle": "Category",
                "yAxisTitle": "Number of Questions",
                "series": [
                    {
                        "seriesName": "Top Questions 2024",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 300},
                            {"label": "Program Information", "x": 2, "y": 250},
                            {"label": "Career Services", "x": 3, "y": 320},
                            {"label": "Academic Advising", "x": 4, "y": 280},
                            {"label": "Admission Process", "x": 5, "y": 200}
                        ]
                    },
                    {
                        "seriesName": "Top Questions 2023",
                        "data": [
                            {"label": "Financial Aid", "x": 1, "y": 280},
                            {"label": "Program Information", "x": 2, "y": 230},
                            {"label": "Career Services", "x": 3, "y": 310},
                            {"label": "Academic Advising", "x": 4, "y": 260},
                            {"label": "Admission Process", "x": 5, "y": 190}
                        ]
                    }
                ]
            }
        ]
    },
],

}

    



    answer_COURSE_associations: Dict[str, List[Dict]] = {
        "I want a tech elective that explore any AI topic, I don't want classes on Friday, and I don't want a project-based class": [
            {
            "document_id": "4",
            "title": "CIS 5960 - Applied Machine Learning",
            "code": "CIS",
            "Semester": "Fall",
            "Credit": "1 CU",
            "Prerequisites": "MATH 3210, CIS 3210",
            "Work": "2.5",
            "CourseQuality": "3.5",
            "Difficulty": "2",
            "Description": "Introduction to fundamental concepts and algorithms to cover supervised, unsupervised and reinforcement learning.",
            "Prospectus_link": "http://localhost:5001/static/yc_popup/course_path@penn.html",
            "Syllabus_link": "http://localhost:5001/static/yc_popup/syllabus_cis_5190.html",
            "CoursesSlot": [
                {
                "CourseID": "235",
                "TeacherName": "Dr. John Louise",
                "TeacherQuality": "4",
                "Days": ["Mon", "Wed"],
                "StartTime": "10:00",
                "EndTime": "11:30"
                },
                {
                "CourseID": "808",
                "TeacherName": "Dr. Jane Smith",
                "TeacherQuality": "3.5",
                "Days": ["Tue", "Thu"],
                "StartTime": "14:00",
                "EndTime": "15:30"
                },
                {
                "CourseID": "715",
                "TeacherName": "Dr. Emily Johnson",
                "TeacherQuality": "4.2",
                "Days": ["Fri"],
                "StartTime": "15:00",
                "EndTime": "17:00"
                }
            ]
            },


            {
                "document_id": "5",
                "title": "CIS 5220 - Deep Learning for Data Science",
                "code": "CIS",
                "Semester": "Fall",
                "Credit": "1 CU",
                "Prerequisites": "MATH 3210, CIS 5310",
                "Work": "3",
                "CourseQuality": "2",
                "Difficulty": "4",
                "Description": "Introduction to fundamental concepts of deep learning to cover supervised, unsupervised, and reinforcement learning.",
                "Prospectus_link": "http://localhost:5001/static/yc_popup/course_path@penn.html",
                "Syllabus_link": "http://localhost:5001/static/yc_popup/syllabus_cis_5190.html",
                "CoursesSlot": [
                    {
                    "CourseID": "340",
                    "TeacherName": "Dr. Michael Brown",
                    "TeacherQuality": "4.5",
                    "Days": ["Mon", "Wed"],
                    "StartTime": "11:00",
                    "EndTime": "12:30"
                    },
                    {
                    "CourseID": "210",
                    "TeacherName": "Dr. Sarah Lee",
                    "TeacherQuality": "4.0",
                    "Days": ["Tue", "Thu"],
                    "StartTime": "15:00",
                    "EndTime": "16:30"
                    },
                    {
                    "CourseID": "650",
                    "TeacherName": "Dr. Alan Turing",
                    "TeacherQuality": "4.7",
                    "Days": ["Mon"],
                    "StartTime": "15:00",
                    "EndTime": "17:00"
                    }
                ]
                }

        ]
    }

    # Check if the question is known
    response_message = known_responses.get(input_message, "Sorry, I don't understand the question.")

    # Get the documents, related questions, images, answer_TAK and answer_waiting associated with the input message
    answer_REDDIT_data = answer_reddit_associations.get(input_message, None)
    answer_QUORA_data = answer_quora_associations.get(input_message, None)
    answer_YOUTUBE_data = answer_youtube_associations.get(input_message, None)
    #answer_INSTA_data = answer_instagram_associations.get(input_message, None)
    answer_INSTA_CLUB_data = answer_instagram_club_associations.get(input_message, None)
    answer_LINKEDIN_data = answer_linkedin_associations.get(input_message, None)
    
    documents = document_associations.get(input_message, [])
    related_qs = related_questions.get(input_message, [])
    images = image_associations.get(input_message, [])
    answer_TAK_data = answer_TAK_associations.get(input_message, [])
    answer_COURSE_data = answer_COURSE_associations.get(input_message, [])
    answer_waiting_data = answer_waiting_associations.get(input_message, [])
    # Vérification si le message d'entrée nécessite un graphique
    answer_CHART_data = answer_chart_associations.get(input_message, None)
    

    # Return the simulated response as streaming
    async def message_stream():
        # Send the text in streaming
        chunks = split_preserving_formatting(response_message)

        for chunk in chunks:
            yield chunk + " "  # Send chunks of text as raw text
            await asyncio.sleep(0.08)

        # Send answer_waiting JSON if available
        if answer_waiting_data:
            answer_waiting_json = json.dumps({"answer_waiting": answer_waiting_data})
            yield f"\n<ANSWER_WAITING>{answer_waiting_json}<ANSWER_WAITING_END>\n"
            await asyncio.sleep(0.5)  # Wait for 6 seconds before sending the next part of the message

            waiting_text_answer="_**[LUCY is processing the search…]**_"


            # Send final response after waiting
            final_response = """Thanks for your patience, Mathieu! I’ve found three courses that match your criteria for a technical elective in AI, I have taken 5XX level classes given you are a senior and have validated already three 4XX tech electives. Here they are:\n\n **Option 1: CIS 5190 - Applied Machine Learning**\n- *Description:* The course introduces fundamental concepts and algorithms that enable computers to learn from experience, with an emphasis on practical application to real problems. It covers supervised learning (decision trees, logistic regression, support vector machines, neural networks, and deep learning), unsupervised learning (clustering, dimensionality reduction), and reinforcement learning.\n- *Schedule:* Monday and Wednesday, 10:00 AM - 11:30 AM\n- *Format:* Lecture-based with practical assignments\n- *Instructor:* Dr. Emily Zhang\n- *Class Size:* Medium (30-40 students)\nI know that you are minoring in data science so this course might interest you:\n\n### **Option 2: CIS 5220 - Deep Learning for Data Science**\n- *Description:* This course provides a comprehensive introduction to machine learning techniques specifically tailored for visual data. The class includes a series of hands-on projects where students develop models for tasks such as image classification, object detection, and video analysis.\n- *Schedule:* Monday and Wednesday, 2:00 PM - 3:30 PM\n- *Format:* Lecture-based with practical assignments\n- *Instructor:* Dr. Michael Rivera\n- *Class Size:* Small (20-25 students)\n\n **Option 3: CIS 5200 - Machine Learning**\n- *Description:* This course intends to provide a thorough modern introduction to the field of machine learning. It is designed for students who want to understand not only what machine learning algorithms do and how they can be used, but also the fundamental principles behind how and why they work.\n- *Schedule:* Monday and Wednesday, 1:45-3:15 PM\n- *Format:* Lecture-based with practical assignments\n- *Instructor:* Dr. Linda Nguyen\n- *Class Size:* Large (50-60 students)\nDo any of these options stand out to you, or would you like more details on any of them?"""

            waiting_chunks = split_preserving_formatting(waiting_text_answer)
            for chunk in waiting_chunks:
                yield chunk + " "
                await asyncio.sleep(0.08)

            await asyncio.sleep(3)

            final_chunks = split_preserving_formatting(final_response)
            for chunk in final_chunks:
                yield chunk + " "
                await asyncio.sleep(0.08)

        await asyncio.sleep(0.2)

        # Send images as JSON if available
        if images:
            image_data_json = json.dumps({"image_data": images})
            yield f"\n<IMAGE_DATA>{image_data_json}<IMAGE_DATA_END>\n"
            await asyncio.sleep(0.2)

        if answer_REDDIT_data:
            answer_REDDIT_json = json.dumps({"reddit": answer_REDDIT_data})
            yield f"\n<REDDIT>{answer_REDDIT_json}<REDDIT_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer

        if answer_QUORA_data:
            answer_QUORA_json = json.dumps({"quora": answer_QUORA_data})
            yield f"\n<QUORA>{answer_QUORA_json}<QUORA_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer

        if answer_YOUTUBE_data:
            answer_YOUTUBE_json = json.dumps({"youtube": answer_YOUTUBE_data})
            yield f"\n<YOUTUBE>{answer_YOUTUBE_json}<YOUTUBE_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer


        '''
        if answer_INSTA_data:
            answer_INSTA_json = json.dumps({"insta": answer_INSTA_data})
            yield f"\n<INSTA>{answer_INSTA_json}<INSTA_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer
        '''

        if answer_INSTA_CLUB_data:
            answer_INSTA_CLUB_json = json.dumps({"insta_club": answer_INSTA_CLUB_data})
            yield f"\n<INSTA_CLUB>{answer_INSTA_CLUB_json}<INSTA_CLUB_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer


        if answer_LINKEDIN_data:
            answer_LINKEDIN_json = json.dumps({"linkedin": answer_LINKEDIN_data})
            yield f"\n<LINKEDIN>{answer_LINKEDIN_json}<LINKEDIN_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer


        
        # Send documents one by one if available
        if documents:
            for document in documents:
                yield f"\n<JSON_DOCUMENT_START>{json.dumps(document)}<JSON_DOCUMENT_END>\n"
                await asyncio.sleep(0.2)


        # Send related questions as JSON if available
        if related_qs:
            related_qs_json = json.dumps({"related_questions": related_qs})
            yield f"\n<RELATED_QUESTIONS>{related_qs_json}<RELATED_QUESTIONS_END>\n"
            await asyncio.sleep(0.2)

        # Send answer_TAK as JSON if available
        if answer_TAK_data:
            answer_TAK_json = json.dumps({"answer_TAK_data": answer_TAK_data})
            yield f"\n<ANSWER_TAK>{answer_TAK_json}<ANSWER_TAK_END>\n"
            await asyncio.sleep(0.2)

        # Si des données de graphique sont présentes, les envoyer entre les balises ANSWER_CHART
        if answer_CHART_data:
            answer_CHART_json = json.dumps({"answer_CHART_data": answer_CHART_data})
            yield f"\n<ANSWER_CHART>{answer_CHART_json}<ANSWER_CHART_END>\n"
            await asyncio.sleep(0.2)  # Pause avant de continuer


        # Send answer_COURSE as JSON if available
        if answer_COURSE_data:
            answer_COURSE_json = json.dumps({"answer_COURSE_data": answer_COURSE_data})
            yield f"\n<ANSWER_COURSE>{answer_COURSE_json}<ANSWER_COURSE_END>\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(message_stream(), media_type="text/plain")




def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=8004)