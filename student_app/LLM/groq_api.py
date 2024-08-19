from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv
import os

load_dotenv()


def get_keywords(query: str) -> str:
        groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Extract only 1 keyword from the user's query with no preamble or punctuation.",
                },
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model="llama3-8b-8192",
        )

        keywords = chat_completion.choices[0].message.content

        return keywords


async def llm_answer_with_groq_async(messages: List[Dict[str, str]]):
        groq_client =  Groq(api_key=os.environ.get("GROQ_API_KEY"))
        stream_response = groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            temperature=0.4,
            stream=True,
        )

        for chunk in stream_response:
            # print(chunk.choices[0].delta.content, end="")
            yield chunk.choices[0].delta.content + "|"
