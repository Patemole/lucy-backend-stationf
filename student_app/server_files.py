
#Changement pour être compliant avec Heroku
import sys
import os
import asyncio
import logging
from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File, Form
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


def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)