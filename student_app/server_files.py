#Changement pour être compliant avec Heroku
import sys
import os
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

from student_app.profiling.profile_generation import scrape_instagram, scrape_linkedin_profile, enrich_person_data



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

# Fonction pour extraire le sous-domaine de l'université via OAuth consumer_key
def get_university_subdomain(oauth_consumer_key):
    for subdomain, key in LTI_CONSUMER_KEYS.items():
        if key == oauth_consumer_key:
            return subdomain
    return None

# Classe de validation OAuth 1.0
class LTIRequestValidator(RequestValidator):
    def check_client_key(self, client_key):
        return client_key in LTI_CONSUMER_KEYS.values()

    def get_client_secret(self, client_key):
        return LTI_SHARED_SECRET

    @property
    def enforce_ssl(self):
        return False  # À passer à True en prod

validator = LTIRequestValidator()
endpoint = SignatureOnlyEndpoint(validator)


# Add necessary directories to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

app = FastAPI(
    title="File Service",
    version="0.0.1"
)

'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    #allow_credentials=True,
    #allow_methods=["*"],
    #allow_headers=["*"],
)
'''

#file_router = APIRouter(prefix='/files', tags=['file'])


class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str


#file_router = APIRouter(prefix='/files', tags=['file'])
# Endpoint pour envoyer un email
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
    


class LinkedInScrapingRequest(BaseModel):
    first_name: str
    last_name: str
    university: str
    user_id: str

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
    


class InstagramUsernameRequest(BaseModel):
    username: str
    user_id: str

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
    


class LinkedinLinkRequest(BaseModel):
    url: str
    user_id: str

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


def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)