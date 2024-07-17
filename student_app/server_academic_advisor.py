
import sys
import os
import asyncio
import logging
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from functools import wraps
import time
# from student_app.database.dynamo_db.chat import get_chat_history, store_message_async
from student_app.model.input_query import InputQuery, InputQueryAI
from student_app.database.dynamo_db.new_instance_chat import delete_all_items_and_adding_first_message
from student_app.academic_advisor import academic_advisor_answer_generation
from student_app.LLM.academic_advisor_search_engine_answering_LLM_chain import LLM_chain_search_engine_and_answering
from student_app.LLM.llm_with_memory import CreateLLMWithDynamoDBMemory

from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

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

#chat_router = APIRouter(prefix='/chat', tags=['chat'])

# TRAITEMENT D'UN MESSAGE ÉLÈVE - Rajouter ici la fonction pour déterminer la route à choisir 
@app.post("/send_message_socratic_langgraph")
async def chat(request: Request, response: Response, input_query: InputQuery) -> StreamingResponse:
    chat_id = input_query.chat_id
    course_id = input_query.course_id  # Get course_id from input_query
    username = input_query.username
    input_message = input_query.message
    university = input_query.university #A rajouter pour avoir le bon search engine par la suite

    print(f"chat_id: {chat_id}, course_id: {course_id}, username: {username}, input_message: {input_message}")

    # Récupérez l'historique de chat
    # chat_history = await get_chat_history(chat_id)
    # print(chat_history)
    
    # Stockez le message de manière asynchrone
<<<<<<< HEAD
    asyncio.ensure_future(store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message))
    # Selection of the route from the router + first LLM generation for query reformulation for the Search Engine (with follow-up questions)
    search_engine_query, prompt_answering, student_profile, method, keywords = await academic_advisor_router_treatment(input_message, chat_history, university)
=======
    # asyncio.ensure_future(store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message))

    # Selection of the route from the router + first LLM generation for query reformulation for the Search Engine (with follow-up questions)
    search_engine_query, prompt_answering, student_profile, method, keywords = await academic_advisor_router_treatment(input_message,
                                                                                                                       chat_id,
                                                                                                                       username,
                                                                                                                       course_id)
>>>>>>> jules-dev-AA

    print(f"search_engine_query: {search_engine_query}, prompt_answering: {prompt_answering}, method: {method}, keywords: {keywords}")

    #Second LLM generation with the search engine + Answer generation and sources 
    return StreamingResponse(LLM_chain_search_engine_and_answering(input_message, 
                                                                   search_engine_query, 
                                                                   prompt_answering, 
                                                                   student_profile, 
                                                                   chat_id, 
                                                                   university, 
                                                                   method, 
                                                                   course_id, 
                                                                   username, 
                                                                   keywords), 
                                                                   media_type="text/event-stream")


    # Créez une réponse en streaming en passant l'historique de chat
    #return StreamingResponse(academic_advisor_answer_generation(input_message, chat_history), media_type="text/event-stream")

    #Rajouter ici en paramètre le prompt + la bonne instance de search engine
    #streaming_answer = LLM_chain_generation(input_message, chat_history)

    #return StreamingResponse(streaming_answer, media_type="text/event-stream")
    #Ancienne manière de récupérer le message
    #return StreamingResponse(LLM_chain_generation(input_message, chat_history), media_type="text/event-stream")

    # Il faudra appeler une autre fonction en fonction de si c'est l'academic advisor ou d'autres cours.
    # Logic suivante : if course_id == "academic_advisor" : return StreamingResponse(academic_advisor_answer_generation(input_query.message, chat_history), media_type="text/event-stream")
    # else : return StreamingResponse(socratic_answer_generation(input_query.message, chat_history, course_id), media_type="text/event-stream")
    # avec le course_id qui correspond au cours que l'élève a demandé.


# # RÉCUPÉRATION DE L'HISTORIQUE DE CHAT (pour les conversations plus tard)
# @app.get("/get_chat_history/{chat_id}")
# async def get_chat_history_route(chat_id: str):
#     return await get_chat_history(chat_id)



# # SUPPRIMER L'HISTORIQUE DE CHAT CHAQUE CHARGEMENT DE LA PAGE - TO BE DEPRECIATED
# @app.post("/delete_chat_history/{chat_id}")
# async def delete_chat_history_route(chat_id: str):
#     try:
#         await delete_all_items_and_adding_first_message(chat_id)
#         return {"message": "Chat history deleted successfully"}
#     except Exception as e:
#         logging.error(f"Erreur lors de la suppression de l'historique du chat : {str(e)}")
#         raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'historique du chat")
    

# # NOUVEL ENDPOINT POUR SAUVEGARDER LE MESSAGE AI
# @app.post("/save_ai_message")
# async def save_ai_message(ai_message: InputQueryAI):
#     chat_id = ai_message.chatSessionId
#     course_id = ai_message.courseId
#     username = ai_message.username
#     input_message = ai_message.message
#     type = ai_message.type #Pas utilisé pour l'instant, on va faire la selection quand on récupérera le username if !== "Lucy" alors on mets "human" else "ai"

#     try:
#         asyncio.ensure_future(store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message))

#         return {"message": "AI message saved successfully"}
#     except Exception as e:
#         logging.error(f"Erreur lors de la sauvegarde du message AI : {str(e)}")
#         raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du message AI")


def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)