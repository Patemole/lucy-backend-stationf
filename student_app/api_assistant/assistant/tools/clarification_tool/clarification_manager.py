from functools import wraps

import time
from functools import wraps
import asyncio
import logging

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("file_server.log")  # Save logs to a file
    ]
)

@timing_decorator
def get_clarifying_question_output(arguments, input_message):
    question = arguments.get('question', '')
    answer_options = arguments.get('answer_options', [])
    logging.info(f"get_clarifying_question_output for '{input_message}'")
    tool_output = [{
        "document_id": "4",
        "question": question,
        "answer_options": answer_options,
        "other_specification": {
            "label": "If other, please specify",
            "placeholder": "e.g., None"
        }
    }]
    return tool_output
