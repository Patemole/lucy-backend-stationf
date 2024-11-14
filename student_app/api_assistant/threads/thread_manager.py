# backend/threads/thread_manager.py

import time
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os
from functools import wraps


# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

import time
from functools import wraps
import asyncio

import logging

# Logging configuration (to be added if it's not already in the main app)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("file_server.log")  # Save logs to a file
    ]
)

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


@timing_decorator
async def create_thread(client, chat_id, username, university, input_message):
    """
    Creates a new thread with a custom thread ID based on the provided chat_id, username, and university.
    """
    try:
        logging.info(f"Attempting to create a new thread for chat_id: {chat_id}, username: {username}, university: {university} for {input_message}")
        thread = await client.beta.threads.create(
            metadata={
                "username": username,
                "university": university
            }
        )
        logging.info(f"Thread created with ID: {thread.id} for chat ID: {chat_id} for {input_message}")
        return thread
    except Exception as e:
        logging.error(f"Error creating thread for chat_id {chat_id}: {str(e)} for {input_message}")
        raise

@timing_decorator
async def add_user_message(client, thread_id, user_query):
    """
    Adds a user message to the specified thread.
    """
    if not user_query.strip():  # Check if user_query is empty or whitespace
        logging.warning(f"Attempted to add an empty user message to thread {thread_id} for {user_query}. Skipping.")
        return None  # Return None to indicate no action taken

    try:
        logging.info(f"Adding user message to thread {thread_id} for {user_query}")
        message = await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_query
        )
        logging.info(f"User message added to thread {thread_id}: for {user_query}")
        return message
    except Exception as e:
        logging.error(f"Error adding user message to thread in add_user_message {thread_id}: {str(e)} for {user_query}")
        raise

@timing_decorator
async def add_message_to_thread(client, thread_id, role, content, input_message):
    """
    Adds a message (user/assistant) to the specified thread.
    """
    if not content.strip():  # Check if content is empty or whitespace
        logging.warning(f"Attempted to add an empty {role} message to thread {thread_id} for {input_message}. Skipping.")
        return None  # Return None to indicate no action taken

    try:
        logging.info(f"Adding {role} message to thread {thread_id} for {input_message}")
        message = await client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        logging.info(f"{role.capitalize()} message added to thread {thread_id}: {content} for {input_message}")
        return message
    except Exception as e:
        logging.error(f"Error adding {role} message to thread in add_message_to_thread {thread_id}: {str(e)} for {input_message}")
        raise

@timing_decorator
async def create_and_poll_run(client, thread_id, assistant_id, input_message):
    """
    Creates a run for the assistant and polls its status until completion.
    """
    try:
        logging.info(f"Creating and polling run for thread {thread_id}, assistant {assistant_id} for {input_message}")
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        logging.info(f"Run created with ID: {run.id}, Initial status: {run.status} for {input_message}")
        return run
    except Exception as e:
        logging.error(f"Error creating and polling run for thread {thread_id}: {str(e)} for {input_message}")
        raise

@timing_decorator
async def retrieve_run(client, run_id, thread_id, input_message):
    """
    Retrieves the current status of a run.
    """
    try:
        logging.info(f"Retrieving run with ID {run_id} for thread {thread_id} for {input_message}")
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        logging.info(f"Retrieved run with status: {run.status} for {input_message}")
        return run
    except Exception as e:
        logging.error(f"Error retrieving run {run_id} for thread {thread_id}: {str(e)} for {input_message}")
        raise

@timing_decorator
async def retrieve_messages(client, thread_id, input_message):
    """
    Retrieves all messages in a thread.
    """
    try:
        logging.info(f"Retrieving messages for thread {thread_id} for {input_message}")
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        logging.info(f"Retrieved {len(messages)} messages for thread {thread_id} for {input_message}")
        return messages
    except Exception as e:
        logging.error(f"Error retrieving messages for thread {thread_id}: {str(e)} for {input_message}")
        raise
