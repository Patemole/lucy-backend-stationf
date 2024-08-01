from typing import List, Dict, Optional
import time
from functools import wraps
from student_app.prompts.perplexity_prompt_checker import pplx_messages_format_validation



# Définir le décorateur
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper


@timing_decorator
async def reformat_prompt(prompt: str, **kwargs) -> str:
    try:
        print("Prompt was correctly reformated")
        return prompt.format(**kwargs)
    except KeyError as e:
        missing_key = str(e).strip("'")
        raise ValueError(f"Missing required placeholder: {missing_key}")


@timing_decorator
async def reformat_messages(messages: List[Dict[str, str]], **kwargs) -> List[Dict[str, str]]:
    reformatted_messages = []
    for message in messages:
        try:
            reformatted_content = message['content'].format(**kwargs)
            reformatted_messages.append({
                "role": message['role'],
                "content": reformatted_content
            })
            print("Message was correctly reformatted")
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(f"Missing required placeholder: {missing_key}")
    return reformatted_messages


@timing_decorator
async def set_prompt_with_history(system_prompt: str, 
                                  chat_history: List[Dict[str, str]], 
                                  user_prompt: str, 
                                  predefined_messages: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    
    if predefined_messages is None:
        predefined_messages = []

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        *predefined_messages,
        *chat_history,
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    print("Checking the formatting ...")
    pplx_messages_format_validation(messages)
    print("The list of messages for the prompt was correctly formated with history messages.")
    return messages

# ############################################ TESTING ###############################################
# # Example usage in an async context
# async def main():
#     # Example prompt with placeholders
#     prompt = "Hello, {name}!"
#     try:
#         formatted_prompt = await reformat_prompt(prompt, name="Alice")  # Await the function call
#         print(formatted_prompt)
#     except ValueError as e:
#         print(e)

#     # Example set prompt with history
#     chat_history = [
#         {
#             "role": "user",
#             "content": "What's up?"
#         },
#         {
#             "role": "assistant",
#             "content": "It's a beautiful day! How are you ?"
#         }
#     ]

#     system_prompt = "You are a helpful assistant."

#     predefined_messages = [
#         {
#             "role": "user",
#             "content": "Hello!"
#         },
#         {
#             "role": "user",
#             "content": "Hi there!"
#         }
#     ]
#     try:
#         final_prompt = await set_prompt_with_history(system_prompt=system_prompt, 
#                                                      chat_history=chat_history, 
#                                                      user_prompt=formatted_prompt, 
#                                                      predefined_messages=predefined_messages)
#         print(final_prompt)
#     except Exception as e:
#         print(e)

# # To run the async main function
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

# # # Output
# # Prompt was correctly reformated
# # reformat_prompt took 4.506111145019531e-05 seconds
# # Hello, Alice!
# # [
# # {'role': 'system', 'content': 'You are a helpful assistant.'}, 
# # {'role': 'user', 'content': 'Hello!'}, 
# # {'role': 'assistant', 'content': 'Hi there!'}, 
# # {'role': 'user', 'content': "What's up?"}, 
# # {'role': 'assistant', 'content': "It's a beautiful day! How are you ?"}, 
# # {'role': 'user', 'content': 'Hello, Alice!'}]

# ############################################ TESTING ###############################################
