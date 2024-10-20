# backend/threads/thread_manager.py

import time
import openai
from dotenv import load_dotenv
import os
from functools import wraps


# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

import time
from functools import wraps
import asyncio

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
def create_thread(client, chat_id, username, university):
    """
    Creates a new thread with a custom thread ID based on the provided chat_id, username, and university.

    Args:
        chat_id (str): The ID representing the conversation in your app.
        username (str): The username of the user.
        university (str): The university of the user.

    Returns:
        openai.Thread: The created thread instance.
    """
    thread = client.beta.threads.create(
        metadata={
            #"custom_thread_id": chat_id,
            "username": username,
            "university": university
        }
    )
    print(f"Thread created with ID: {thread.id} (linked to app chat ID: {chat_id})\n")
    return thread

@timing_decorator
def add_user_message(client, thread_id, user_query):
    """
    Adds a user message to the specified thread.

    Parameters:
    - thread_id (str): The ID of the thread.
    - user_query (str): The user's query.

    Returns:
        openai.Message: The created message instance.
    """
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_query
    )
    print(f"User message added to thread {thread_id}: {user_query}\n")
    return message

@timing_decorator
def add_message_to_thread(client, thread_id, role, content):
    """
    Adds a message (user/assistant) to the specified thread.

    Parameters:
    - thread_id (str): The ID of the thread.
    - role (str): The role of the message ('user' or 'assistant').
    - content (str): The message content.

    Returns:
        openai.Message: The created message instance.
    """
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )
    print(f"{role.capitalize()} message added to thread {thread_id}: {content}\n")
    return message

@timing_decorator
def create_and_poll_run(client, thread_id, assistant_id):
    """
    Creates a run for the assistant and polls its status until completion.

    Parameters:
    - thread_id (str): The ID of the thread.
    - assistant_id (str): The ID of the assistant.

    Returns:
        openai.Run: The completed run instance.
    """
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    print(f"Run created with ID: {run.id}")
    print(f"Initial Run status: {run.status}\n")
    return run

@timing_decorator
def retrieve_run(client, run_id, thread_id):
    """
    Retrieves the current status of a run.

    Parameters:
    - run_id (str): The ID of the run.
    - thread_id (str): The ID of the thread.

    Returns:
        openai.Run: The retrieved run instance.
    """
    return client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )

@timing_decorator
def retrieve_messages(client, thread_id):
    """
    Retrieves all messages in a thread.

    Parameters:
    - thread_id (str): The ID of the thread.

    Returns:
        list: A list of message instances.
    """
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages
