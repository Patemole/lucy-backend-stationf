
#Changement pour être compliant avec Heroku
import sys
import os
import asyncio
import logging
from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File, Form, Response, Request
from FastAPI.responses import RedirectResponse, JSONResponse
import requests
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
import json

# Charger les variables d'environnement
load_dotenv()


# Charger les variables d'environnement
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_AUTH_URL = os.getenv("AZURE_AUTH_URL")
AZURE_TOKEN_URL = os.getenv("AZURE_TOKEN_URL")
REDIRECT_URI = "https://my-lucy.com/sso/oidc/callback"  # 🔥 L'URL où Azure AD renverra l'utilisateur après login


# Configuration de Resend avec la clé API
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise ValueError("❌ ERREUR : RESEND_API_KEY n'est pas configurée dans .env")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            "from": "onboarding@resend.dev",
            "to": [request.to],
            "subject": request.subject,
            "html": request.html
        })

        logging.info(f"✅ Email envoyé avec succès : {response}")

        return {"success": True, "response": response}
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi de l'email : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    





#-------------------------------SSO--------------------------------------------#


CERTIFICATE_PATH = os.path.join(os.path.dirname(__file__), "../certs/cert.pem")

# 🔥 Lire le certificat et le formatter correctement pour le XML
def get_certificate():
    with open(CERTIFICATE_PATH, "r") as cert_file:
        cert_content = cert_file.read()
    # 🔥 Supprimer les balises "BEGIN CERTIFICATE" et "END CERTIFICATE"
    cert_content = cert_content.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "")
    # 🔥 Nettoyer les espaces et sauts de ligne
    cert_content = cert_content.strip().replace("\n", "")
    return cert_content

SAML_METADATA_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://my-lucy.com/sso/metadata">
    <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <KeyDescriptor use="signing">
            <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
                <X509Data>
                    <X509Certificate>
                        {get_certificate()}
                    </X509Certificate>
                </X509Data>
            </KeyInfo>
        </KeyDescriptor>
        <AssertionConsumerService 
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="https://my-lucy.com/sso/callback"
            index="0" />
    </SPSSODescriptor>
</EntityDescriptor>
"""

#CONFIGURATION ENDPOINT FOR SAML
@app.get("/sso/metadata", response_class=Response)
async def get_saml_metadata():
    return Response(content=SAML_METADATA_TEMPLATE, media_type="application/xml")


#RECUPERATION DE LA CONFIGURATION SSO
SSO_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "sso_configs")

def load_sso_config(university):
    config_file = os.path.join(SSO_CONFIG_PATH, f"{university}.json")
    if not os.path.exists(config_file):
        return None
    with open(config_file, "r") as file:
        return json.load(file)
    
    
#------------REDIRECTION TO THE SSO PROVIDER--------------#

@app.post("/sso/authenticate")
async def sso_authenticate(request: Request):
    data = await request.json()
    university = data.get("university")

    if not university:
        return JSONResponse(content={"error": "University is required"}, status_code=400)

    # 🔥 Charger la configuration de l'école
    sso_config = load_sso_config(university)
    if not sso_config:
        return JSONResponse(content={"error": "No SSO configuration found for this university"}, status_code=404)

    # 🔥 Vérifie si l'école utilise SAML
    if "ssoLoginUrl" in sso_config:
        return RedirectResponse(sso_config["ssoLoginUrl"])

    # 🔥 Vérifie si l'école utilise OpenID Connect
    if "auth_url" in sso_config:
        return RedirectResponse(sso_config["auth_url"])

    return JSONResponse(content={"error": "No valid SSO method found for this university"}, status_code=400)


#--------------------CALLBACK------------------------#

# 🔥 CALLBACK OIDCD ENDPOINT AFTER AUTHENTIFICATION 
@app.get("/sso/oidc/callback")
async def oidc_callback(code: str):
    token_data = {
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    # 🔥 Récupérer le token OAuth depuis Azure AD
    token_response = requests.post(AZURE_TOKEN_URL, data=token_data)
    token_json = token_response.json()

    if "id_token" not in token_json:
        return JSONResponse(content={"error": "Authentication failed"}, status_code=401)

    id_token = token_json["id_token"]

    # 🔥 Renvoyer le token au frontend pour gestion de la session
    return JSONResponse(content={"id_token": id_token})


def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)