# main.py  ──────────────────────────────────────────────────────────
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File, Form, Request, Response
import json
from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint
from fastapi.responses import RedirectResponse
import firebase_admin
from firebase_admin import credentials, auth, firestore
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Tuple
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
import resend
from pydantic import BaseModel, HttpUrl
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from student_app.profiling.profile_generation import scrape_instagram, scrape_linkedin_profile, enrich_person_data
import os
import asyncio
import logging
import datetime
#import requests
import httpx  # ✅ Remplace `requests` par `httpx`

from openai import OpenAI, AsyncOpenAI
from fastapi import FastAPI, HTTPException, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

from pydantic import BaseModel
from typing import Dict, List
import json


import asyncio
import time
from student_app.database.dynamo_db.analytics import store_analytics_async

from student_app.model.input_query import InputQuery, InputQueryAI
from student_app.model.student_profile import StudentProfile
from student_app.database.dynamo_db.new_instance_chat import delete_all_items_and_adding_first_message

from student_app.database.dynamo_db.analytics import store_analytics_async
from student_app.database.dynamo_db.chat import get_chat_history, store_message_async, get_messages_from_history, get_timing_history
from student_app.database.dynamo_db.events import fetch_events_from_dynamoDB
from student_app.database.dynamo_db.events_zeroentropy import find_top_events_for_student

from student_app.database.dynamo_db.feedback import store_feedback_without_popup_async

from student_app.profiling.profile_generation import LLM_profile_generation
from student_app.profiling.onboarding_sentence import onboarding_sentence

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
#from student_app.api_assistant.assistant.config.universities import holyfamily
from student_app.api_assistant.assistant.config import universities

from student_app.profiling.profile_generation import scrape_instagram, scrape_linkedin_profile
from functools import wraps
import asyncio
import asyncio
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json

# Today's date
date = datetime.date.today()

import threading
import queue
from functools import wraps
from fastapi import BackgroundTasks

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError, EmailStr
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import uvicorn
from student_app.database.dynamo_db.feedback import store_feedback_async
from student_app.database.dynamo_db.academic_advisor_email import store_academic_advisor_email_async
from typing import Optional



# ────────────── Config logging ──────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lucy-backend")


# ────────────── App & CORS ──────────────
app = FastAPI(title="Lucy API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://upenn.localhost:3001",
        "http://yale.localhost:3001",
        "http://holyfamily.localhost:3001",
        "http://kedge.localhost:3001",
        "http://harvard.localhost:3001",
        "http://cornell.localhost:3001",
        "http://columbia.localhost:3001",
        "http://localhost:3001",
        "https://preprod.upenn.my-lucy.com",  # Ajouter pour la pré-prod UPenn
        "https://preprod.yale.my-lucy.com",   # Ajouter pour la pré-prod Yale (exemple)
        "https://preprod.holyfamily.my-lucy.com", # Ajouter pour la pré-prod HolyFamily (exemple)
        "https://preprod.kedge.my-lucy.com", # Ajouter pour la pré-prod Kedge (exemple)
        "https://preprod.harvard.my-lucy.com", # Ajouter pour la pré-prod Harvard (exemple)
        "https://preprod.cornell.my-lucy.com", # Ajouter pour la pré-prod Cornell (exemple)
        "https://preprod.columbia.my-lucy.com", # Ajouter pour la pré-prod Columbia (exemple)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Requested-With",
        # Ajoutez ici tout autre en-tête personnalisé que votre frontend pourrait envoyer
    ], # Rendre plus explicite que ["*"]
)

# ────────────── Middleware de log (optionnel mais pratique) ──────────────
@app.middleware("http")
async def log_request(request, call_next):
    logger.info("➡️  %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("⬅️  %s", response.status_code)
    return response

# ────────────── Static files ──────────────
BASE_DIR = os.path.dirname(__file__)

static_teacher_dir          = os.path.join(BASE_DIR, "../analytics/analytics_teacher")
static_academic_advisor_dir = os.path.join(BASE_DIR, "../analytics_academic")
static_yc_popup_dir         = os.path.join(BASE_DIR, "../pop_up_page_yc")

app.mount("/static/teacher",          StaticFiles(directory=static_teacher_dir),          name="static_teacher")
app.mount("/static/academic_advisor", StaticFiles(directory=static_academic_advisor_dir), name="static_academic_advisor")
app.mount("/static/yc_popup",         StaticFiles(directory=static_yc_popup_dir),         name="static_yc_popup")

# ────────────── Endpoints applicatifs ──────────────---------------------------------------------------------

# ────────────── Class for Endpoints------------------------------------------------------------------------------
class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str

class LinkedInScrapingRequest(BaseModel):
    first_name: str
    last_name: str
    university: str
    user_id: str

class InstagramUsernameRequest(BaseModel):
    username: str
    user_id: str

class LinkedinLinkRequest(BaseModel):
    url: str
    user_id: str

class ImageUrlPayload(BaseModel):
    imageUrl: HttpUrl # Valide automatiquement que c'est une URL HTTP(S)


# Classe de validation OAuth 1.0
class LTIRequestValidator(RequestValidator):
    def check_client_key(self, client_key):
        return client_key in LTI_CONSUMER_KEYS.values()


class FeedbackWrongAnswerModel(BaseModel):
    userId: str
    chatId: str
    aiMessageContent: str
    humanMessageContent: str
    feedback: str
    relevance: Optional[int] = None
    accuracy: Optional[int] = None
    format: Optional[int] = None
    sources: Optional[int] = None
    overall_satisfaction: Optional[int] = None

    
class GeneralFeedbackModel(BaseModel):
    userId: str
    feedback: str
    courseId: str


class AcademicAdvisorEmailModel(BaseModel):
    email: EmailStr
    uid: str


#----------------Initialisation for endpoints--------------------------------------------------------------------------

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

api_key_proxycurl = os.getenv("PROXYCURL_API_KEY")

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

# Configuration de Resend avec la clé API
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise ValueError("❌ ERREUR : RESEND_API_KEY n'est pas configurée dans .env")


ENVIRONMENT= os.getenv('ENVIRONMENT', 'dev')
LTI_SHARED_SECRET= os.getenv('LTI_SHARED_SECRET')

# Définis le chemin en fonction de l'environnement
firebase_credentials_paths = {
    "dev": "firestore_credentials/firebase_credentials_dev.json",
    "preprod": "firestore_credentials/firebase_credentials_preprod.json",
    "prod": "firestore_credentials/firebase_credentials_prod.json"
}

cred_path = firebase_credentials_paths.get(ENVIRONMENT)
if not cred_path:
    raise ValueError(f"❌ ERREUR : Chemin Firebase non défini pour l'environnement {ENVIRONMENT}")
cred = credentials.Certificate(cred_path)
# Check if the default app already exists before initializing
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()


# Définition précise des URL selon l'environnement
API_URLS = {
    "dev": "localhost:3001",
    "preprod": "my-lucy.com",
    "prod": "my-lucy.com"
}
apiUrlPrefix = API_URLS.get(ENVIRONMENT)
if not apiUrlPrefix:
    raise ValueError(f"❌ ERREUR : URL non définie pour l'environnement {ENVIRONMENT}")


# Mapping des consumer_keys par université
LTI_CONSUMER_KEYS = {
    "upenn": os.getenv("LTI_CONSUMER_KEY_UPENN"),
    "holyfamily": os.getenv("LTI_CONSUMER_KEY_HOLYFAMILY")
}


#----------------Definition function for endpoints----------------------------------------------------------------

# Fonction pour extraire le sous-domaine de l'université via OAuth consumer_key
def get_university_subdomain(oauth_consumer_key):
    for subdomain, key in LTI_CONSUMER_KEYS.items():
        if key == oauth_consumer_key:
            return subdomain
    return None



    def get_client_secret(self, client_key):
        return LTI_SHARED_SECRET

    @property
    def enforce_ssl(self):
        return False  # À passer à True en prod

validator = LTIRequestValidator()
endpoint = SignatureOnlyEndpoint(validator)


# Add necessary directories to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


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
async def classify_query(question: str, university: str) -> dict:
    """
    Classifies a student's question into predefined categories and generates a conversation title.
    Returns a dictionary with 'category' and 'conversation_title'.
    """
    logging.info(f"this is the university: {university}")


    is_kedge = university.lower() == "kedge"

    if is_kedge:
        categories_enum = ["Aides financières", "événements", "politiques", "logement", "cours", "discussions"]
        category_example = "l'une parmi : Aides financières, événements, politiques, logement, cours, discussions"
        system_content = (
            "Vous êtes un classificateur. Catégorisez la question de l'utilisateur dans l'une de ces catégories : "
            "Identifiez d'abord la langue de la question de l'utilisateur, puis catégorisez la question dans l'une de ces catégories : "
            "Aides financières, événements, politiques, logement, cours, ou discussions. "
            "Ne mettez discussions que lorsque cela n'a aucun rapport avec l'université exemple : salut, comment ça va, que peux-tu faire etc... lorsque l'étudiant ne demande pas d'informations mais veut juste te parler sinon choisissez une autre catégorie. "
            "Générez également un titre de conversation court de style clickbait. "
            "La catégorie et le titre de la conversation doivent être dans la langue de la question de l'utilisateur. Assurez-vous de traduire en conséquence avant de retourner la réponse. "
            "si la question de l'utilisateur est en anglais, la catégorie (Financial Aids, Events, Policies, Housing, Courses, Chitchat) et le titre de la conversation doivent être en anglais, si la question de l'utilisateur est en français, la catégorie (Aides financières, événements, politiques, logement, cours, discussions) et le titre de la conversation doivent être en français. "
            "{\n"
            f'  "category": "{category_example}",\n'
            '  "conversation_title": "un titre court de style clickbait"\n'
            "}\n\n"
        )
    else:
        categories_enum = ["Financial Aids", "Events", "Policies", "Housing", "Courses", "Chitchat"]
        category_example = "one of: Financial Aids, Events, Policies, Housing, Courses, Chitchat"
        system_content = (
            "You are a classifier. Categorize the user's question into one of these categories: "
            "First identify the language of the user question, then categorize the question into one of these categories: "
            "Financial Aids, Events, Policies, Housing, Courses, or Chitchat. "
            "Only put Chitchat only when it is not related at all with university example: hi, how are you, what can you do etc... when the student is not asking for info but just want to talks to you otherwise choose another category"
            "Also, generate a short conversation title using a clickbait style. "
            "Both category and conversation title should be in the language of the user question. Make sure to translate accordingly before returning the response. "
            "if the user question is in english, the category (Financial Aids, Events, Policies, Housing, Courses, Chitchat) and conversation title should be in english, if the user question is in french, the category (Aides financières, événements, politiques, logement, cours, discussions) and conversation title should be in french. "
            "{\n"
            f'  "category": "{category_example}",\n'
            '  "conversation_title": "a short clickbait-style title"\n'
            "}\n\n"
        )

    response_schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": categories_enum
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
                    "content": system_content
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
            max_tokens=50,
            temperature=1.7
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









# ────────────── Authentification and Onboarding Endpoints ──────────────------------------------------------------
@app.api_route("/send-email", methods=["OPTIONS"])
async def handle_send_email_preflight():
    return Response(status_code=200)

@app.api_route("/linkedin_scraping_sign_up", methods=["OPTIONS"])
async def handle_linkedin_scraping_sign_up_preflight():
    return Response(status_code=200)

@app.api_route("/instagram_scraping_onboarding", methods=["OPTIONS"])
async def handle_instagram_scraping_onboarding_preflight():
    return Response(status_code=200)

@app.api_route("/linkedin_scraping_onboarding", methods=["OPTIONS"])
async def handle_linkedin_scraping_onboarding_preflight():
    return Response(status_code=200)

@app.api_route("/lti/launch", methods=["OPTIONS"])
async def handle_lti_launch_preflight():
    return Response(status_code=200)

@app.api_route("/proxy-image", methods=["OPTIONS"])
async def handle_proxy_image_preflight():
    return Response(status_code=200)

@app.api_route("/send_message_socratic_langgraph", methods=["OPTIONS"])
async def handle_send_message_socratic_langgraph_preflight():
    return Response(status_code=200)

@app.api_route("/get_chat_history/{chat_id}", methods=["OPTIONS"])
async def handle_get_chat_history_preflight():
    return Response(status_code=200)

@app.api_route("/delete_chat_history/{chat_id}", methods=["OPTIONS"])
async def handle_delete_chat_history_preflight(chat_id: str):
    return Response(status_code=200)

@app.api_route("/first_lucy_message_onboarding", methods=["OPTIONS"])
async def handle_first_lucy_message_onboarding_preflight():
    return Response(status_code=200)

@app.api_route("/get_calendar_events", methods=["OPTIONS"])
async def handle_get_calendar_events_preflight():
    return Response(status_code=200)

@app.api_route("/save_feedback", methods=["OPTIONS"])
async def handle_save_feedback_preflight():
    return Response(status_code=200)

@app.api_route("/save_ai_message", methods=["OPTIONS"])
async def handle_save_ai_message_preflight():
    return Response(status_code=200)

@app.api_route("/student_profile", methods=["OPTIONS"])
async def handle_student_profile_preflight():
    return Response(status_code=200)

@app.api_route("/wrong_answer", methods=["OPTIONS"])
async def handle_wrong_answer_preflight():
    return Response(status_code=200)

@app.api_route("/feedback_answer", methods=["OPTIONS"])
async def handle_feedback_answer_preflight():
    return Response(status_code=200)

@app.api_route("/academic_advisor/email", methods=["OPTIONS"])
async def handle_academic_advisor_email_preflight():
    return Response(status_code=200)



@app.get("/health-check")
async def health_check():
    return {"status": "ok"}




@app.post("/wrong_answer")
async def submit_feedback_wrong_answer(feedback: FeedbackWrongAnswerModel):
    try:
      
        await store_feedback_async(
            uid=feedback.userId, 
            feedback=feedback.feedback,
            chat_id=feedback.chatId, 
            ai_message=feedback.aiMessageContent,
            human_message=feedback.humanMessageContent,
            
            relevance=feedback.relevance,
            accuracy=feedback.accuracy,
            format=feedback.format,
            sources=feedback.sources,
            overall_satisfaction=feedback.overall_satisfaction
            )
        

        return {"message": "Feedback on wrong answer received successfully"}
    
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logging.error(f"Error inserting message into feedback database: {error_code} - {error_message}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@app.post("/feedback_answer")
async def submit_feedback_answer(feedback: GeneralFeedbackModel):
    try:
        #logging.info(f"User: {feedback.userId}")
        #logging.info(f"Page {feedback.courseId}")
        #logging.info(f"Feedback: {feedback.feedback}")
        
        await store_feedback_async(feedback.userId,feedback.feedback,feedback.courseId)
        return {"message": "General feedback received successfully"}
    

    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logging.error(f"Error inserting message into feedback database: {error_code} - {error_message}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




@app.post("/academic_advisor/email")
async def submit_academic_advisor_email(data: AcademicAdvisorEmailModel):
    try:
        # Here, integrate the logic to process the academic advisor's email and uid
        logging.info(f"Academic advisor email received: {data.email}")
        logging.info(f"User ID received: {data.uid}")

        await store_academic_advisor_email_async(data.uid, data.email)
        return {"message": "Academic advisor email received successfully"}
    
    except ValidationError as e:
        logging.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=422, detail=e.errors())



@app.post("/send-email")
async def send_email(request: EmailRequest):
    try:
        logging.info(f"📤 Envoi de l'email à {request.to} via Resend...")

        response = resend.Emails.send({
            "from": "team@updates.my-lucy.com",
            "to": [request.to],
            "subject": request.subject,
            "html": request.html
        })

        logging.info(f"✅ Email envoyé avec succès : {response}")

        return {"success": True, "response": response}
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi de l'email : {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/linkedin_scraping_sign_up")
async def linkedin_scraping_endpoint(payload: LinkedInScrapingRequest):
    print("📥 Requête reçue pour /files/linkedin_scraping")
    print(f"• Prénom        : {payload.first_name}")
    print(f"• Nom           : {payload.last_name}")
    print(f"• Université    : {payload.university}")
    print(f"• ID utilisateur: {payload.user_id}")

    try:
        # Appel à la fonction d'enrichissement
        linkedin_found = enrich_person_data(
            first_name=payload.first_name,
            last_name=payload.last_name,
            school=payload.university,
            uid=payload.user_id
        )

        return {"linkedInFound": linkedin_found}
    except Exception as e:
        logging.error(f"Erreur dans linkedin_scraping_endpoint : {str(e)}")
        return {"linkedInFound": False}




@app.post("/instagram_scraping_onboarding")
async def scrape_linkedin(request: InstagramUsernameRequest):
    try:
        logging.info(f"Récupération du username instagram : {request.username}")

        # Scraper les informations LinkedIn
        instagram_student_info = scrape_instagram(request.username, request.user_id)

        if not instagram_student_info:
            raise HTTPException(status_code=500, detail="Impossible de récupérer les informations instagram")

        # Retourne les données récupérées sous forme de JSON
        return Response(content=json.dumps(instagram_student_info), media_type="application/json")
    except Exception as e:
        logging.error(f"🚨 Erreur lors du scraping instagram : {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/linkedin_scraping_onboarding")
async def scrape_linkedin(request: LinkedinLinkRequest):
    try:
        logging.info(f"Récupération de l'URL LinkedIn : {request.url}")

        # Scraper les informations LinkedIn
        linkedin_student_info = scrape_linkedin_profile(request.url, request.user_id)

        if not linkedin_student_info:
            raise HTTPException(status_code=500, detail="Impossible de récupérer les informations LinkedIn")

        # Retourne les données récupérées sous forme de JSON
        return Response(content=json.dumps(linkedin_student_info), media_type="application/json")
    except Exception as e:
        logging.error(f"🚨 Erreur lors du scraping LinkedIn : {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post('/lti/launch')
async def lti_launch(request: Request):
    try:
        params = await request.form()
        headers = request.headers

        logging.info(f"🚀 Requête LTI reçue avec paramètres: {params}")
        logging.info(f"🔑 Headers reçus : {headers}")

        oauth_consumer_key = params.get('oauth_consumer_key')
        email = params.get('lis_person_contact_email_primary')
        name = params.get('lis_person_name_full')
        roles = params.get('roles')
        canvas_user_id = params.get('user_id')

        logging.info(f"🔍 oauth_consumer_key: {oauth_consumer_key}")
        logging.info(f"📧 email: {email}")
        logging.info(f"👤 name: {name}")
        logging.info(f"🎭 roles: {roles}")
        logging.info(f"🆔 canvas_user_id: {canvas_user_id}")

        uri = str(request.url)
    #body = await request.body()
        # Reconstitution propre du body pour validation OAuth
        body_params = dict(params)
        body_encoded = "&".join([f"{key}={value}" for key, value in body_params.items()])
        logging.info(f"🌐 URI de la requête: {uri}")
        logging.info(f"📦 Corps de la requête : {body_encoded}")

        '''
        valid, _ = endpoint.validate_request(
            uri=uri,
            http_method=request.method,
            body=body.decode(),
            headers=headers
        )
        '''
        valid = True  # 🚧 TEMPORAIRE : OAuth désactivé en dev

        if not valid:
            logging.error("❌ Signature OAuth invalide")
            raise HTTPException(status_code=401, detail="Signature OAuth invalide")
        logging.info("✅ Validation OAuth réussie")

        university_subdomain = get_university_subdomain(oauth_consumer_key)
        if not university_subdomain:
            logging.error("❌ Université inconnue")
            raise HTTPException(status_code=400, detail="Université inconnue")
        logging.info(f"🎓 Sous-domaine université détecté : {university_subdomain}")

        new_user = False
        try:
            firebase_user = auth.get_user_by_email(email)
            uid = firebase_user.uid
            logging.info(f"👥 Utilisateur existant trouvé avec UID: {uid}")
        except auth.UserNotFoundError:
            firebase_user = auth.create_user(email=email, display_name=name)
            uid = firebase_user.uid
            new_user = True
            logging.info(f"🆕 Nouvel utilisateur créé avec UID : {uid}")

            firestore.client().collection('users').document(uid).set({
                'uid': uid,
                'email': email,
                'name': name,
                'canvas_roles': roles,
                'canvas_user_id': canvas_user_id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'university': university_subdomain,
                'onboardingComplete': False
            })
            logging.info("📦 Données nouvel utilisateur enregistrées dans Firestore")

        if not new_user:
            firestore.client().collection('users').document(uid).update({
                'roles': firestore.ArrayUnion([roles]),
                'canvas_user_id': canvas_user_id,
                'lastCanvasLogin': firestore.SERVER_TIMESTAMP
            })
            logging.info("🔄 Données utilisateur existant mises à jour dans Firestore")

        custom_token = auth.create_custom_token(uid).decode('utf-8')
        logging.info(f"🔑 Token personnalisé Firebase généré")

        if ENVIRONMENT == "dev":
            redirect_url = f"http://{university_subdomain}.{apiUrlPrefix}/auth/lti-login?token={custom_token}&newUser={'true' if new_user else 'false'}"
        elif ENVIRONMENT == "preprod":
            redirect_url = f"https://preprod.{university_subdomain}.{apiUrlPrefix}/auth/lti-login?token={custom_token}&newUser={'true' if new_user else 'false'}"
        else:
            redirect_url = f"https://{university_subdomain}.{apiUrlPrefix}/auth/lti-login?token={custom_token}&newUser={'true' if new_user else 'false'}"

        logging.info(f"🔀 Redirection vers : {redirect_url}")

        return RedirectResponse(redirect_url, status_code=302)
    
    except Exception as e:
        logging.exception(f"Erreur interne lors du traitement LTI: {e}")
        raise HTTPException(status_code=500, detail=str(e))




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/proxy-image",
          # Spécifier le type de réponse pour la documentation OpenAPI
          responses={
              200: {
                  "content": {"image/*": {}},
                  "description": "Image data streamed successfully.",
              },
              400: {"description": "Invalid request body or URL"},
              404: {"description": "Image not found at the provided URL"},
              500: {"description": "Internal server error or failed to fetch image"},
          })
async def proxy_image_download(payload: ImageUrlPayload):
    """
    Downloads an image from the provided URL and streams it back.
    Acts as a proxy to bypass CORS issues in the frontend.
    """
    image_url = str(payload.imageUrl) # Convertir HttpUrl en string pour httpx
    logger.info(f"Received request to proxy image from: {image_url}")
    # Utiliser un client httpx asynchrone
    async with httpx.AsyncClient() as client:
        try:
            # Faire la requête GET vers l'URL externe
            response = await client.get(image_url, follow_redirects=True, timeout=15.0) # Ajout timeout
            # Vérifier si la requête a réussi
            response.raise_for_status() # Lève une exception pour les codes 4xx/5xx
            # Vérifier le type de contenu (optionnel mais recommandé)
            content_type = response.headers.get("content-type")
            if not content_type or not content_type.startswith("image/"):
                 logger.warning(f"URL {image_url} did not return an image. Content-Type: {content_type}")
                 # On peut soit rejeter, soit tenter quand même
                 # raise HTTPException(status_code=400, detail=f"URL did not return an image. Content-Type: {content_type}")
                 # Pour l'instant, on essaie quand même de renvoyer, le front gèrera
            # Renvoyer le contenu de l'image directement
            # FastAPI gère intelligemment le streaming pour les grands fichiers
            # On récupère le contenu brut (bytes)
            image_bytes = await response.aread()
            logger.info(f"Successfully fetched image from {image_url}. Size: {len(image_bytes)} bytes. Content-Type: {content_type}")
            # Renvoyer une réponse avec les bytes et le bon Content-Type
            return Response(content=image_bytes, media_type=content_type)
        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP error fetching {image_url}: {e.response.status_code} - {e.response.text}")
             # Renvoyer l'erreur HTTP d'origine si possible, ou une erreur générique
             raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch image from source: Status {e.response.status_code}")
        except httpx.RequestError as e:
            # Erreurs réseau, timeout, etc.
            logger.error(f"Network error fetching {image_url}: {e}")
            raise HTTPException(status_code=500, detail=f"Network error while trying to fetch image: {e}")
        except Exception as e:
            # Autres erreurs inattendues
            logger.exception(f"Unexpected error processing proxy request for {image_url}") # Log l'exception complète
            raise HTTPException(status_code=500, detail="Internal server error processing image proxy request.")
        


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

    user = input_query.user #All user informations are now here
    is_onboarding_message = input_query.isOnboardingMessage #To know if Lucy already send an onboarding message to the user

    logging.info("this is the boolean value of is first message")
    logging.info(is_first_message)

    logging.info(f"Processing message from {username} at {university} for {input_message}")
    

    # Define the generator function
    @timing_decorator
    async def response_generator():
        try:
            if is_onboarding_message:
                logging.info("Onboarding message detected, calling onboarding_sentence generator.")
                try:
                    async for chunk in onboarding_sentence(user):
                        yield chunk # onboarding_sentence already adds the "|"
                        #await asyncio.sleep(0.05) 
                    
                    logging.info("Onboarding content streamed successfully.")
                    # Store the complete message after streaming (optional)
                    # Need to accumulate chunks if storing is required
                    # complete_onboarding_message = "".join(list_of_chunks_from_generator)
                    # await store_message_async(...) 
                        
                except Exception as onboard_error:
                    logging.error(f"Error during onboarding_sentence streaming: {onboard_error}", exc_info=True)
                    yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An error occurred during onboarding.'}})}<ERROR_END>\n"
                
            else:

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
                    classification_task = asyncio.create_task(classify_query(input_message, university))
                    print(f"first message task created")
                    print("awaiting task")
                    classification_title_result = await classification_task

                    # Ensure the result is always a dict
                    if isinstance(classification_title_result, dict):
                        classification_title_json = classification_title_result
                    else:
                        try:
                            classification_title_json = json.loads(classification_title_result)
                        except json.JSONDecodeError:
                            logging.warning(f"Classification result not valid JSON, using default category for result: {classification_title_result}")
                            classification_title_json = {
                                "category": "unknown",
                                "conversation_title": "Untitled Conversation"
                            }
                        else:
                            classification_title_json = classification_title_json
                    print(f"classification_title_json : {classification_title_json}")
                    wrapped_result = {"classification_title_result": classification_title_json}
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
                                yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An error occurred while finalizing your request. Please try again later.'}})}<ERROR_END>\n"
                                return


                    logging.info(f"Streaming run created and started for {input_message}")
                    
                except KeyError as e:
                    logging.error(f"KeyError during streaming run: {str(e)} for {input_message}", exc_info=True)
                    yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'A KeyError occurred while processing your request.'}})}<ERROR_END>\n"
                    return  # Stop execution after yielding the error

                except Exception as e:
                    logging.error(f"Error during streaming run: {str(e)} for {input_message}", exc_info=True)
                    yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': f'Sorry boss an error occured while generating your response, please try again {username}.'}})}<ERROR_END>\n"
                    return  # Stop execution after yielding the error

        except Exception as e:
            logging.error(f"Error during response generation: {str(e)} for {input_message}")
            yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': f'Oops! Sorry boss an unexpected error occurred, please try again {username}.'}})}<ERROR_END>\n"
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


@app.post("/first_lucy_message_onboarding")
async def onboarding_message(profile: StudentProfile, linkedin_data: dict = {}):
    try:
        onboarding_text = await onboarding_sentence(profile, linkedin_data)
        return {"message": onboarding_text}
    except Exception as e:
        logging.error(f"Erreur lors de la génération du message onboarding: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la génération du message onboarding.")


@app.post("/get_calendar_events")
async def get_calendar_events(profile: StudentProfile = Body(...)):
    try:
        print(f"profile: {profile}")
        #events = find_top_events_for_student(profile)

        #return JSONResponse(content={"events": events}, status_code=200)
        return None
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des événements du calendrier : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des événements")


@app.post("/save_feedback")
async def save_feedback_without_popup(request: Request):
    try:
        request_data = await request.json()
        message_id = request_data['message_id']
        chat_id = request_data['chat_id']
        is_positive = request_data['is_positive']
        user_id = request_data['user_id']
        ai_message = request_data['ai_message_content']
        human_message = request_data['humain_message_content']

        # Appel à la nouvelle fonction pour enregistrer le feedback
        await store_feedback_without_popup_async(message_id, chat_id, is_positive, user_id, ai_message, human_message)

        return {"message": "Feedback saved successfully"}

    except Exception as e:
        logging.error(f"Erreur lors de l'enregistrement du feedback : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement du feedback")



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
    step_metadata = ai_message.metadataOnboarding
    sources = ai_message.sources
    confidence_score = ai_message.confidence_score

    print("input_message de l'utilisateur:")
    print(input_message)
    print("output_message de l'IA:")
    print(output_message)

    word_count_task = await count_words(input_message)

    #chat_history = await get_chat_history(chat_id)
    #number_of_question_per_chat_id = await count_student_questions(chat_history)
    #number_of_question_per_chat_id = number_of_question_per_chat_id + 1

    try:
        message_id = await store_message_async(chat_id, username=username, course_id=course_id, message_body=output_message, step_metadata=step_metadata, sources=sources, confidence_score=confidence_score)
        print(f"Stored message with ID: {message_id}")

        #data à récupérer et faire la logic 
        feedback = 'no'
        ask_for_advisor = 'no'

        #Rajouter ici la fonction pour sauvegarder les informations dans la table analytics 
       #await store_analytics_async(chat_id=chat_id, course_id=course_id, uid=uid, input_embedding=input_embeddings, output_embedding=output_embeddings, feedback=feedback, ask_for_advisor=ask_for_advisor, interaction_position=number_of_question_per_chat_id, word_count=word_count_task, ai_message_id=message_id, input_message=input_message, output_message=output_message, university=university)

    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du message AI : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du message AI")




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



# ────────────── Lancement local ──────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 5001))
    logger.info("🚀  Lucy backend running on http://0.0.0.0:%s", port)

    uvicorn.run(
        "student_app.server_run:app",
        host="0.0.0.0",
        port=port,
        log_level="debug",
        #reload=True,        # retire reload en prod
    )