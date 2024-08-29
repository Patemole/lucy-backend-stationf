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
                    "content": "Identify the most specific keyword from the user's query with no preamble, postamble or explanation or punctuation. Output only 1 word.",
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


async def llm_answer_with_groq_async(messages: List[Dict[str, str]], model: str):
        groq_client =  Groq(api_key=os.environ.get("GROQ_API_KEY"))
        try:
            stream_response = groq_client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.8,
                stream=True,
            )

            for chunk in stream_response:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content + "|"
                else:
                    yield "|"
                # print(chunk.choices[0].delta.content, end="")
                # yield chunk.choices[0].delta.content + "|"

        except Exception as e:
            print(e)
