import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from functools import wraps

# from student_app.database.dynamo_db.chat import get_chat_history, store_message_async
from student_app.model.input_query import InputQuery, InputQueryAI
from student_app.database.dynamo_db.new_instance_chat import delete_all_items_and_adding_first_message
from student_app.academic_advisor import academic_advisor_answer_generation
from student_app.LLM.academic_advisor_perplexity_API_request import LLM_pplx_stream_with_history

from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment
from student_app.prompts.academic_advisor_perplexity_search_prompts import system
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

    #TODO: put student profile as param of the function and get it from firebase
    student_profile = "Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"
    prompt_answering = system

    print(f"prompt_answering: {prompt_answering}")
    #Second LLM generation with the search engine + Answer generation and sources 
    return StreamingResponse(LLM_chain_perplexity(input_message,
                                                  prompt_answering, 
                                                  student_profile, 
                                                  chat_id, 
                                                  university, 
                                                  course_id,
                                                  username,), 
                                                  media_type="text/event-stream")



def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)