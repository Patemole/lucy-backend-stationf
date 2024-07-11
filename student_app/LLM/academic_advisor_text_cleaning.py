import google.generativeai as genai

# Replace 'YOUR_API_KEY' with your actual Gemini API key
genai.configure(api_key='AIzaSyDFsMoG1QGiRismgqLIHjXfKRTmIyobaWY')

model = genai.GenerativeModel('gemini-1.5-flash')

def extract_relevant_info(query, text):
    #prompt = f"Query: {query}\n\nText: {text}\n\nPlease extract the relevant information based on the query."
    prompt = f"""
        Task: Extract and clean relevant information from a long text (e.g., from an HTML URL) that can help answer a specific query.

        Process:

        Segment the Text: Break the text into manageable sections for evaluation.
        Identify Relevant Sections: For each section, determine if it contains information that might help answer the query. Use logical criteria to assess relevance, such as keyword matching and context analysis.
        Extract Exact Text: If a section is relevant, extract the exact text without any modification to preserve all original details.
        Clean the Extracted Text:
        Convert all text to lowercase.
        Remove any weird characters, URLs, or other non-informative content to ensure the text is human-readable and machine-processable.
        Direct Output: Return the cleaned, relevant sections immediately. Do not include any additional messages such as greetings, introductions, or conclusions.
        Example:
        Query: {query}\n\n
        Text: {text}\n\n
    """
    response = model.generate_content(prompt)
    return response.text
