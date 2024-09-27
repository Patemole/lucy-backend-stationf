# backend/threads/thread_manager.py

import time
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_new_thread():
    """
    Creates a new thread.

    Returns:
        openai.Thread: The created thread instance.
    """
    thread = openai.beta.threads.create()
    print(f"Thread created with ID: {thread.id}\n")
    return thread



def add_user_message(thread_id, user_query):
    """
    Adds a user message to the specified thread.

    Parameters:
    - thread_id (str): The ID of the thread.
    - user_query (str): The user's query.

    Returns:
        openai.Message: The created message instance.
    """
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_query
    )
    print(f"User message added to thread {thread_id}: {user_query}\n")
    



#Allow to add dynamoDB messages to the thread
def add_multiple_messages(thread_id, messages):

    for message in messages:
        # Assurer que chaque message a un rôle et un contenu
        role = message.get("role", "user")  # Défaut à "user" si le rôle n'est pas fourni
        content = message.get("content", "")
        
        # Print the message and the role being added
        print(f"Adding message to thread {thread_id}:")
        print(f"Role: {role}, Content: {content}")
        
        # Ajouter le message au thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )

    print(f"Messages added to the thread: {thread_id}\n")

    
   


def create_and_poll_run(thread_id, assistant_id):
    """
    Creates a run for the assistant and polls its status until completion.

    Parameters:
    - thread_id (str): The ID of the thread.
    - assistant_id (str): The ID of the assistant.

    Returns:
        openai.Run: The completed run instance.
    """
    run = openai.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    print(f"Run created with ID: {run.id}")
    print(f"Initial Run status: {run.status}\n")
    return run



def retrieve_run(run_id, thread_id):
    """
    Retrieves the current status of a run.

    Parameters:
    - run_id (str): The ID of the run.
    - thread_id (str): The ID of the thread.

    Returns:
        openai.Run: The retrieved run instance.
    """
    return openai.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )

def retrieve_messages(thread_id):
    """
    Retrieves all messages in a thread.

    Parameters:
    - thread_id (str): The ID of the thread.

    Returns:
        list: A list of message instances.
    """
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    return messages
