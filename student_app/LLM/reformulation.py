import os
import requests
import json
import logging
from dotenv import load_dotenv
from typing import List, Dict



def LLM_pplx_call_with_history(messages: List[Dict[str, str]], model="llama-3.1-70b-instruct"):
    # Load API key from .env
    load_dotenv()
    PPLX_API_KEY = os.getenv("PPLX_API_KEY")

    # Perplexity API endpoint
    url = "https://api.perplexity.ai/chat/completions"

    # Validate the messages input
    if isinstance(messages, list) and all(isinstance(message, dict) for message in messages):
        print(f"Messages: \n\n {messages} \n\n")

        # Add system prompt with detailed instructions to guide the model's behavior
        system_message = {
            "role": "system",
            "content": """
            Query Reformulation
Context:
You are an intelligent assistant designed to help users in conversations by ensuring that their queries are clear and standalone. Below is a conversation between a user and a chatbot. Your task is to analyze the last query from the user and perform one of the following actions based on the context:

Reformulate: If the user's last query refers to earlier parts and only if it refers to earlier part of the conversation or uses ambiguous terms (e.g., pronouns like "it" or phrases like "that"), rewrite the query to make it a complete, standalone question without requiring previous context.
Clarify: If the user's last query is vague or unclear and cannot be meaningfully reformulated, ask for clarification in a polite, concise manner.
Keep Unchanged: If the user's last query is already standalone and does not depend on previous messages, return the query unchanged.
Guidelines:

Be as clear and concise as possible when reformulating the query.
If clarification is needed, ask a direct question that will help resolve the ambiguity.
Prioritize user understanding and the smooth flow of the conversation.
Conversation History:

User (4 messages ago): {Message - 4}
Chatbot (3 messages ago): {Message - 3}
User (2 messages ago): {Message - 2}
Chatbot (1 message ago): {Message - 1}
User (Last Query): {Last Query}
Your Task:
Please choose one of the following actions:

Reformulate the user's last query into a standalone question if it relies on prior messages.
Ask for clarification if the query is too vague to reformulate meaningfully.
Leave the query unchanged if it is already a standalone question that doesn't depend on previous context.

Reformulation questions:
Example 1:
Conversation History:

User: "What is CS110 about?"
Assistant: "CS110 is an introductory computer science course."
Last User Query: "Who is the teacher?"

Output: "reformulation: Who is the teacher of cis110?"


Example 3:
Conversation History:

Assistant: "I can explain how the process of photosynthesis works during the summer season when there is plenty of sunlight."
User: "Okay, but what happens when it's winter?"
Last User Query: "What happens when it's winter?"

Output: "reformulation: How does the process of photosynthesis change during the winter season when there is less sunlight available?"

Example 4:
"conversation_history": [
    {"role": "user", "content": "Can you explain how to apply for financial aid at the university?"},
    {"role": "assistant", "content": "To apply for financial aid, you need to submit the FAFSA and the CSS Profile. Make sure to include the university's code on both forms. Additionally, some students may be required to submit tax returns and other documentation to the financial aid office."},
    {"role": "user", "content": "What are the deadlines for the financial aid application?"},
    {"role": "assistant", "content": "The deadlines for financial aid applications are usually in early March for continuing students and early November for early decision applicants. It's important to check the university's financial aid website for the exact dates."},
],
"query": "What about the scholarship process?"

Output: "reformulation: Can you explain the process of applying for scholarship?"



More information needed questions
Example 4:
Conversation History:

User: "Give me the email of Anne duchene."
Assistant: "Anne duchene email is aduchene@upenn.edu."
Last User Query: "When is this"

Output: "reformulation: I need more information from the context to reformulate the question."

Example 5:
Conversation History:

User: "Tell me about the office hours for Dr. Johnson."
Assistant: "Dr. Johnson's office hours are on Mondays and Wednesdays from 2 PM to 4 PM."
Last User Query: "is it hard ?"

Output: "reformulation: I need more information from the context to reformulate the question."

Example 6:
conversation_history = [
    {"role": "user", "content": "Should i take hist3060"},
    {"role": "assistant", "content": "Yes it is good and a requirement for your major"},
    {"role": "user", "content": "What about hist5000"},
    {"role": "assistant", "content": "Yes it is good"}
]

query = "what about the third one"
Output: "reformulation: Need more information to reformulate this query, no information about the third course or a list in the context"

Example 6:
conversation_history = [
    {"role": "user", "content": "Where is the gym"},
    {"role": "assistant", "content": "NExt to the swimming pool"},
    {"role": "user", "content": "What is my schedule this monday"},
    {"role": "assistant", "content": "you have two lectures and one assignement to finish"}
]

query = "Should i take an appointment?"
Output: "reformulation: Need more information to reformulate this query, no information about a necessary meeting"


independant questions: 
Example 7:
conversation_history = [
    {"role": "user", "content": "Where is the gym"},
    {"role": "assistant", "content": "NExt to the swimming pool"},
    {"role": "user", "content": "What is my schedule this monday"},
    {"role": "assistant", "content": "you have two lectures and one assignement to finish"}
]

query = "What are the office hours of Dr. Sam?"
Output: "reformulation: When are the office of Dr. Sam this semester"


Example 8:
conversation_history = [
    {"role": "user", "content": "Who is my academic advisor and what is his email?"},
    {"role": "assistant", "content": "Your academic advisor is M. Sampath you can join him at samp@upenn.edu"}
]

query = "How can i register for classes?"
Output: "reformulation: What is the process to follow to register for classes"


Instructions for the Query Augmentation Assistant:
Use the structure and logic from the examples to:

Reformulate the last query by including relevant details from the previous exchanges.
Make the query self-contained and understandable without any prior context.
Ensure that the reformulated query is clear, specific, and ready for submission to a search engine or other systems.
If the last query lacks sufficient information from the context to clearly identify what he is refering to, respond by stating that you are missing information.  

Output Format:
Make sure to only output the reformulated question in this format: "reformulation: ..." no other formatting will be accepted
there should be no greetings, no explanation, no comment nothing more, before nothing after.
Please provide the appropriate output based on your analysis, either by reformulating the question, asking for clarification, or leaving the query unchanged.
"""      }

        # Prepend the system message to the conversation history
        messages.insert(0, system_message)

        # Payload for the API request
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.0,  # Adjust temperature if needed
            "stream": False,  # Disable streaming
        }

        # Headers for the API request
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {PPLX_API_KEY}"
        }

        try:
            # Make a POST request to the Perplexity API without streaming
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            # Process the response
            data = response.json()
            result = data['choices'][0]['message']['content']
            print(f'the reformulation is: {result}')
            return result

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
    else:
        raise ValueError("Invalid input. Messages must be a list of dictionaries.")

# Example usage

# Example conversation history
conversation_history = [
    {"role": "user", "content": "Give me info about CIS110."},
    {"role": "assistant", "content": "CIS110 is an introductory computer science course."}
]

# Example query
query = "What about the second one?"

# Add the query to the conversation history
conversation_history.append({"role": "user", "content": query})

# Run the function and get the final response
LLM_pplx_call_with_history(conversation_history)
