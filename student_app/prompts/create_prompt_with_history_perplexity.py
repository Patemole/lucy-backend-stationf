from typing import List, Dict
import time
from functools import wraps



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
async def set_prompt_with_history(system_prompt: str, chat_history: List[Dict[str, str]], user_prompt: str) -> List[Dict[str, str]]:

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        *chat_history,
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    print("The list of messages for the prompt was correctly formated with history messages.")
    return messages

############################################# TESTING ###############################################
# # Example usage in an async context
# async def main():
#     # Example prompt with placeholders
#     prompt = "Hello, {name}!"
#     try:
#         formatted_prompt = await reformat_prompt(prompt, name="Alice")  # Await the function call
#         print(formatted_prompt)
#     except ValueError as e:
#         print(e)

# # To run the async main function
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

# # Output
# Prompt was correctly reformated
# reformat_prompt took 4.506111145019531e-05 seconds
# Hello, Alice!

############################################# TESTING ###############################################
