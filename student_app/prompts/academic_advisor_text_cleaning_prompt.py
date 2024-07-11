prompt_reformulation_for_web_search = '''
You are an expert text cleaner. Your task is to extract and clean plain text from the given HTML text content extracted directly from a web page: TEXT. The cleaned text should contain only the meaningful text information coming from TEXT without any HTML tags, URLs, indentation, dropdown menus, or any other non-text content. Please ensure the final output is plain, well-structured text. Here is the HTML content:
Direct Output: Return  the relevant sections immediately. Do not include any additional messages such as greetings, introductions, or conclusions.

TEXT: {text}

Output the cleaned text below:

'''

prompt_reformulation_for_web_search2 = '''
Task: Extract the sections of a long text: TEXT (e.g., from an HTML URL) that can help answer a specific query. The query: QUERY is the user question and i need you to filter all information fro, the long htlm text that can help answer the query.

Process:

Identify Relevant Sections: look in the text: TEXT For section that contains information that might help answer the query: QUERY. Use logical criteria to assess relevance, such as keyword matching and context analysis. or if any information could be an info to answer the question do not cut any section and you can be conservative in your selection of relevant sections. the more the better
Extract Exact Text: If a section is relevant, extract the exact text without any modification to preserve all original details. and keep some context for a full understanding of the information
Direct Output: Return  the relevant sections immediately. Do not include any additional messages such as greetings, introductions, or conclusions.

QUERY: {query}
TEXT: {text}
'''