# backend/assistant/assistant_manager.py

import openai
from backend.config import Config
from backend.assistant.tools.filter_tool.filters import define_filter_tool
# Import additional tools as you add them
# from backend.assistant.tools.another_tool.another_tool import define_another_tool

def initialize_assistant():
    """
    Initializes and creates the AI assistant with defined tools.

    Returns:
        openai.Assistant: The created assistant instance.
    """
    openai.api_key = Config.OPENAI_API_KEY

    # Define tools
    tools = [
        define_filter_tool(),  # Add additional tools here
    ]

    # Create the assistant
    assistant = openai.beta.assistants.create(
        name=Config.ASSISTANT_NAME,
        instructions=(
            "You are an assistant that helps students choose their classes by filtering a course database based on their queries. "
            "Use the provided filters to search the database and return only the courses that match the criteria. "
            "Do not generate or fabricate any course information. If no courses match the query, inform the user accordingly."
        ),
        model=Config.ASSISTANT_MODEL,
        tools=tools
    )

    return assistant

# Example usage:
# assistant = initialize_assistant()
