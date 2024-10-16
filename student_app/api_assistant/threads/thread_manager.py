# backend/threads/thread_manager.py

import time
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_thread(chat_id):
    """
    Creates a new thread with a custom thread ID based on the provided chat_id.

    Args:
        chat_id (str): The ID representing the conversation in your app.

    Returns:
        openai.Thread: The created thread instance.
    """
    thread = openai.beta.threads.create(
        metadata={"custom_thread_id": chat_id}
    )
    print(f"Thread created with ID: {thread.id} (linked to app chat ID: {chat_id})\n")
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
    return message

def add_message_to_thread(thread_id, role, content):
    """
    Adds a message (user/assistant) to the specified thread.

    Parameters:
    - thread_id (str): The ID of the thread.
    - role (str): The role of the message ('user' or 'assistant').
    - content (str): The message content.

    Returns:
        openai.Message: The created message instance.
    """
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )
    print(f"{role.capitalize()} message added to thread {thread_id}: {content}\n")
    return message

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
