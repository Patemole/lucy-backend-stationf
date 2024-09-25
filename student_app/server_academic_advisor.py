import os
import asyncio
import logging
import datetime

from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from functools import wraps
import phospho
from typing import Dict, Union, List, AsyncIterable
import asyncio
from fastapi import FastAPI, Request, Response
import json

import pandas as pd

import asyncio
import time
from student_app.database.dynamo_db.chat import get_chat_history, store_message_async
from student_app.database.dynamo_db.analytics import store_analytics_async

from student_app.model.input_query import InputQuery, InputQueryAI
from student_app.model.student_profile import StudentProfile
from student_app.database.dynamo_db.new_instance_chat import delete_all_items_and_adding_first_message

from student_app.database.dynamo_db.analytics import store_analytics_async
from student_app.LLM.academic_advisor_perplexity_API_request import LLM_pplx_stream_with_history
from student_app.database.dynamo_db.chat import get_chat_history, store_message_async, get_messages_from_history
from student_app.prompts.create_prompt_with_history_perplexity import reformat_prompt, reformat_messages ,set_prompt_with_history

from student_app.profiling.profile_generation import LLM_profile_generation
from student_app.prompts.academic_advisor_perplexity_search_prompts import system_normal_search, system_normal_search_V2, system_fusion, system_chitchat
from student_app.prompts.academic_advisor_predefined_messages import predefined_messages_prompt, predefined_messages_prompt_V2
from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

from student_app.prompts.academic_advisor_perplexity_search_prompts import system_profile
from student_app.prompts.academic_advisor_user_prompts import user_with_profil

from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

from api_assistant.assistant.assistant_manager import initialize_assistant
from api_assistant.threads.thread_manager import (
    create_thread,
    add_user_message,
    create_and_poll_run,
    retrieve_run,
    retrieve_messages
)
from api_assistant.assistant.handlers import handle_requires_action
from api_assistant.assistant.tools.filter_tool.filter_manager import apply_filters
from api_assistant.assistant.tools.filter_tool.data_loader import load_course_data
# Today's date
date = datetime.date.today()
import sseclient  # Ensure this is installed: pip install sseclient-py
import requests


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

# Pinecone
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
client = OpenAI()

# Perplexity
# PPLX_API_KEY = os.getenv('PPLX_API_KEY')

#Phospho
PHOSPHO_KEY = os.getenv('PHOSPHO_KEY')
PHOSPHO_PROJECT_ID = os.getenv('PHOSPHO_PROJECT_ID')
phospho.init(api_key='b08542208fd42d8640c0f88d006f31c9cc11453ec5f489e160cfcefa1028cac5bcd4d4ab43bcba45a6052081a22c56b8', project_id='38fc0ee240ee43a7bac2a36419258dcd')



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

#############################################DEUX FONCTIONS POUR LES ANALYTICS##################################

async def count_words(input_message: str) -> int:
    # Compte le nombre de mots dans la chaîne de caractères input_message
    word_count = len(input_message.split())
    print("\n")
    print("This is the number of word in the input:")
    print(word_count)
    print("\n")
    return word_count

async def get_embedding(input_message: str, model="text-embedding-3-small"):
   input_message = input_message.replace("\n", " ")
   embeddings = client.embeddings.create(input = [input_message], model=model).data[0].embedding
   print("\n")
   print("This is the embeddings for the question:")
   print(embeddings)
   print("\n")
   return embeddings


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

#############################################DEUX FONCTIONS POUR LES ANALYTICS##################################

#chat_router = APIRouter(prefix='/chat', tags=['chat'])

# TRAITEMENT D'UN MESSAGE ÉLÈVE - Rajouter ici la fonction pour déterminer la route à choisir 
@app.post("/send_message_socratic_langgraph")
async def chat(request: Request, response: Response, input_query: InputQuery) -> StreamingResponse:
    chat_id = input_query.chat_id
    course_id = input_query.course_id  # Get course_id from input_query
    username = input_query.username
    input_message = input_query.message
    university = input_query.university #A rajouter pour avoir le bon search engine par la suite
    student_profile = input_query.student_profile


    # In your main processing function

    
    def process_assistant(message: str):
        """
        Function to process the assistant interaction with SSE streaming support.

        Args:
            message (str): The user's input message.

        Yields:
            str: Chunks of the assistant's reply, delimited by "|".
        """
        # Initialize the assistant
        assistant = initialize_assistant()

        # Create a new thread for the conversation
        thread = create_thread()

        # Add the user's message to the thread
        add_user_message(thread.id, message)

        # Load the DataFrame once at the beginning
        df_expanded = pd.read_csv('../api_assistant/assistant/tools/filter_tool/combined_courses_final.csv')

        # Create a run for the assistant using your existing function
        run = create_and_poll_run(thread.id, assistant.id)

        # Check if the run requires action (e.g., function call)
        if run.status == 'requires_action':
            # Handle required actions (function calls)
            run, filtered_data, _, _ = handle_requires_action(run, thread.id, assistant.id, df=df_expanded)
            # If the function called is get_filters, return the filtered data as JSON
            if filtered_data is not None:
                # Return the filtered courses directly as JSON
                yield json.dumps({"filtered_courses": filtered_data})
                return  # End the function as we've returned the data
        elif run.status == 'completed':
            # Proceed to stream the assistant's response using SSE
            # Construct the SSE endpoint URL for the thread
            sse_url = f"https://api.openai.com/v1/beta/threads/{thread.id}/events"

            # Prepare the headers with your API key
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Accept': 'text/event-stream'
            }

            # Create a requests session
            session = requests.Session()

            # Send a GET request to the SSE endpoint
            response = session.get(sse_url, headers=headers, stream=True)

            # Create an SSE client to process the event stream
            client = sseclient.SSEClient(response)

            try:
                for event in client.events():
                    if event.event == 'thread.message.delta':
                        # Event data is a message delta
                        data = json.loads(event.data)
                        delta = data.get('delta', {})
                        content_segments = delta.get('content', [])
                        for segment in content_segments:
                            if segment.get('type') == 'text':
                                text_value = segment['text']['value']
                                if text_value:
                                    # Yield the text value with delimiter
                                    yield text_value + "|"
                    elif event.event == 'thread.message.completed':
                        # Assistant's message is completed
                        break
                    elif event.event == 'error':
                        # Handle errors
                        error_data = json.loads(event.data)
                        yield f"An error occurred: {error_data.get('message', 'Unknown error')}"
                        break
                    # Handle other events as needed
            except Exception as e:
                yield f"An exception occurred: {str(e)}"
            finally:
                # Close the session
                session.close()
        else:
            # Handle other run statuses (e.g., failed)
            yield f"Run ended with status: {run.status}."




    # Call the inner function and get the response
    # response is either a String of the assistant response is return "assistant_reply: " or it is a dict of JSON output for each courses found -> type is List[Dict]
    response = await process_assistant(input_message)


    try:
        return StreamingResponse(LLM_pplx_stream_with_history(messages=prompt, model=model), media_type="text/event-stream")
        # return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Error while streaming response from Perplexity LLM with history: {str(e)}")


    """"
    print(f"chat_id: {chat_id}, course_id: {course_id}, username: {username}, input_message: {input_message}")

    prompt_answering, question_type, model = await academic_advisor_router_treatment(input_message=input_message)
    
    print(f"Student profil from firestore : {student_profile}")
    #student_profile = "Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"

    domain = f"site:{university}.edu"

    # Get all items from chat history
    # try:
    #     history_items = await get_chat_history(chat_id=chat_id)
    # except Exception as e:
    #     logging.error(f"Error while retrieving chat history items : {str(e)}")

    # Retrieve the "n" messages from the items of the chat history
    try:
        messages = await get_messages_from_history(chat_id=chat_id, n=6)
    except Exception as e:
        logging.error(f"Error while retrieving 'n' messages from chat history items: {str(e)}")

    predefined_messages = []

    if question_type == "normal":
        try:
            system_prompt = await reformat_prompt(prompt=system_fusion, university=university, date=date, domain=domain, student_profile=student_profile)
        except Exception as e:
            logging.error(f"Error while reformating system prompt: {str(e)}")

        try:
            predefined_messages = await reformat_messages(messages=predefined_messages_prompt_V2, university=university, student_profile=student_profile)
        except Exception as e:
            logging.error(f"Error while reformating the predefined messages: {str(e)}")

        try:
            user_prompt = await reformat_prompt(prompt=user_with_profil, input=input_message, domain=domain)
        except Exception as e:
            logging.error(f"Error while reformating user prompt: {str(e)}")

    elif question_type == "chitchat":
        try:
            system_prompt = await reformat_prompt(prompt=system_chitchat, university=university, student_profile=student_profile)
        except Exception as e:
            logging.error(f"Error while reformating system prompt: {str(e)}")
        user_prompt = input_message

    try:
        prompt = await set_prompt_with_history(system_prompt=system_prompt, user_prompt=user_prompt, chat_history=messages, predefined_messages=predefined_messages)
    except:
        logging.error(f"Error while setting prompt with history: {str(e)}")

    # Async storage of the input
    try:
        await store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message)
    except Exception as e:
        logging.error(f"Error while storing the input message: {str(e)}")

    # Stream the response
    # def event_stream():
    #     for content in LLM_pplx_stream_with_history(PPLX_API_KEY=PPLX_API_KEY, messages=prompt):
    #         # print(content, end='', flush=True)
    #         yield content + "|"

    # Stream response from Perplexity LLM with history 
    try:
        return StreamingResponse(LLM_pplx_stream_with_history(messages=prompt, model=model), media_type="text/event-stream")
        # return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Error while streaming response from Perplexity LLM with history: {str(e)}")
"""

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



# NOUVEL ENDPOINT POUR SAUVEGARDER LE MESSAGE AI
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


    phospho.log(input=input_message, output=output_message)


    #Pour générer l'embedding de la réponse de Lucy
    input_embeddings = await get_embedding(input_message)
    output_embeddings = await get_embedding(output_message)

    word_count_task = await count_words(input_message)

    chat_history = await get_chat_history(chat_id)
    number_of_question_per_chat_id = await count_student_questions(chat_history)
    number_of_question_per_chat_id = number_of_question_per_chat_id + 1

    

    try:
        message_id = await store_message_async(chat_id, username=username, course_id=course_id, message_body=output_message)
        print(f"Stored message with ID: {message_id}")

        #data à récupérer et faire la logic 
        feedback = 'no'
        ask_for_advisor = 'no'

        #Rajouter ici la fonction pour sauvegarder les informations dans la table analytics 
        await store_analytics_async(chat_id=chat_id, course_id=course_id, uid=uid, input_embedding=input_embeddings, output_embedding=output_embeddings, feedback=feedback, ask_for_advisor=ask_for_advisor, interaction_position=number_of_question_per_chat_id, word_count=word_count_task, ai_message_id=message_id, input_message=input_message, output_message=output_message, university=university)

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
    """
    Endpoint to handle user messages, interact with the AI assistant, and return appropriate responses.
    
    - If the assistant invokes a function (e.g., `get_filters`), apply the filter and return the filtered JSON.
    - If no function is invoked, return the assistant's textual response.
    
    Args:
        request (Request): The incoming HTTP request.
        input_query (Dict): The JSON payload containing the user's message.
    
    Returns:
        StreamingResponse: The assistant's response, either as JSON or plain text.
    """
    input_message = input_query.get("message")
    if not input_message:
        raise HTTPException(status_code=400, detail="Message is required.")

    
    # Return the response as JSON
    input_message = input_query.get("message")
    print("this is the input message")
    print(input_message)

    await asyncio.sleep(2)

    # Known responses with line breaks and bullet points
    known_responses: Dict[str, str] = {
        "Hey Lucy let’s plan my classes": """Hi Mathieu! Welcome back. I’m here to help you choose your courses for next semester. Let’s get started.""",
        "I want a tech elective that explore any AI topic, I don't want classes on Friday, and I don't want a project-based class": """Hi Mathieu! Welcome back. Let’s get started.""",
        "4": """Great! And how many of those classes have you already decided on?""",
        "I’ve already decided to take cis2400, cis1210, and ese3060": """Got it. So we’re looking for one more class to complete your schedule. What type of class are you looking for? \n- What requirement do you want to fulfill?\n- Do you have any preferences regarding class size?\n- Are there specific days or times that work best for you?\n- What type of assignments do you prefer? \n\n List me any details that you would like""",
        "I want a tech elective that explore any AI topic, I don't want classes on Friday, and I don't want a project-based": """Great, that gives me plenty of flexibility in finding the best course for you.\n\nJust to summarize:\n- You need one more technical elective.\n- You’re interested in AI.\n- You prefer classes with no classes on Fridays.\n- You don’t want a project-based course.\n- Class size isn’t a concern, and you’re open to any instructor.\n\nDoes that all sound correct?""",
        "Yes": """Awesome! I’ll search for the best available options based on these criteria.""",
        "CIS 5020 is good, can you tell me when and where are M.Hammish OH": """Great choice! CIS 5020 please find below details on Dr. Hammish Office Hours:""",
        "Now validate and register my choices": """Done! You’re now set for CIS 5020 - Advanced Topics in AI. You’ve got all your courses lined up for next semester:\n- **CIS 2400** on Monday and Wednesday from 3:00 PM to 5:00 PM.\n- **CIS 5020** on Monday and Wednesday from 10:00 AM to 11:30 AM.\n- **CIS 1210** on Tuesday and Thursday from 11:00 AM to 1:00 PM.\n- **ESE 3060** Lectures on Tuesday from 5:00 PM to 7:00 PM.\n\nThis semester will be a lot of work rated **9/10** for difficulty and **8/10** for work required of the classes your are taking but you will validate a lot of degree requirements.\nGo on and register for your classes on PATH@PENN:""",
        "That’s all I need for now. Thanks, Lucy!": """You’re welcome, Mathieu! Good luck with your upcoming semester. If you need anything else, just reach out. Have a great day!""",
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
    documents = document_associations.get(input_message, [])
    related_qs = related_questions.get(input_message, [])
    images = image_associations.get(input_message, [])
    answer_TAK_data = answer_TAK_associations.get(input_message, [])
    answer_COURSE_data = answer_COURSE_associations.get(input_message, [])
    answer_waiting_data = answer_waiting_associations.get(input_message, [])

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
    uvicorn.run(app, host="0.0.0.0", port=8004)