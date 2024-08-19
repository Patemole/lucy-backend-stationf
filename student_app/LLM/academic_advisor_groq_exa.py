import asyncio
from dotenv import load_dotenv
from exa_py import Exa
from groq import Groq
import os

load_dotenv()

class LucyExaGroqV3:
    def __init__(self, domain: list[str]):
        self.domain = domain

    def _exa_client(self):
        return Exa(api_key=os.environ.get("EXA_API_KEY_1"))

    def _groq_client(self):
        return Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def _system_prompt(self):
        return """
        You are Lucy, a helpful search academic advisor from {university} that help out students.
        Your task is to deliver a concise and accurate response (but no more than 100 words) for a given question solely based on the provided web Search Results: {search_results}
        Your answer must be precise, of high-quality, up to date: {date}, and written by an expert using an unbiased and informative and reassurant tone. 

        If the search results are empty, unclear or unhelpful, ALWAYS SUGGEST to send contact (via email) the user's Academic Advisor.
        If ANY information is missing in the search results, ALWAYS SUGGEST to send contact (via email) the user's Academic Advisor.
        NEVER mention if an information is missing in the search results.

        Use the following student profile to personalize the output: {student_profile},
        Only use the profile if relevant to the request.

        Format your response as follows: 
        Use markdown to format paragraphs, lists, tables, and quotes whenever possible.
        [Provide a concise, friendly and advising answer to the student's query, using only information from {university}'s website. Use these references to support your answers. Use bullet points and bold titles for clarity when appropriate.]
        **Sources**:
        [List all the urls as hyperlink Titles that support your answer. Format as a numbered list.]
        **Related Questions**:
        [Suggest 3 potential follow-up questions the student might have, based on your response. Present as an unordered list of bullet points.]
        """

    def _get_keywords(self, query: str):
        groq_client = self._groq_client()
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
            model="llama3-70b-8192",
        )

        keywords = chat_completion.choices[0].message.content

        print(keywords)
        print(type(keywords))
        return keywords

    def _exa_api(self, query: str, keyword:str):
        exa_client = self._exa_client()

        result = exa_client.search_and_contents(
            query,
            type="auto",
            num_results=10,
            text={
                "include_html_tags": True
            },
            include_domains=self.domain,
            highlights=True,
            summary={
                "query": "Summarize the entire content in a comprehensive and informative manner using bullet points. Include all key points, details, and data presented on the website such as links, dates or numbers."
            },
            include_text=[keyword],
        )

        url_and_summary = [{
            "url": search.url,
            "summary": search.summary 
        }
        for search in result.results]

        # print(url_and_summary)
        return url_and_summary

    def _format_system_prompt(self, query: str):
        import datetime
        date = datetime.date.today()

        keyword = self._get_keywords(query)

        exa_search_results = self._exa_api(query, keyword)

        student_profile = "Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"

        formatted_system_prompt = self._system_prompt().format(university='upenn', date=date, domain=self.domain, student_profile=student_profile, search_results=exa_search_results)
        return formatted_system_prompt

    def lucy_answer(self, query: str):
        groq_client = self._groq_client()
        stream_response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": self._format_system_prompt(query),
                },
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model="llama3-70b-8192",
            temperature=0.4,
            stream=True,
        )

        for chunk in stream_response:
            # print(chunk.choices[0].delta.content, end="")
            yield chunk.choices[0].delta.content + "|"