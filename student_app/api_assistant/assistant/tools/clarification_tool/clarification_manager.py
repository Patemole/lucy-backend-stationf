from functools import wraps

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
def get_clarifying_question_output(arguments):
    question = arguments.get('question', '')
    answer_options = arguments.get('answer_options', [])
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
