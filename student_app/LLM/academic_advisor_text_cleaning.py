import google.generativeai as genai

# Replace 'YOUR_API_KEY' with your actual Gemini API key
genai.configure(api_key='AIzaSyDFsMoG1QGiRismgqLIHjXfKRTmIyobaWY')

model = genai.GenerativeModel('gemini-1.5-flash')

def extract_relevant_info(query, text):
    #prompt = f"Query: {query}\n\nText: {text}\n\nPlease extract the relevant information based on the query."
    prompt = f"""    
    Given the following web page content and a user query, determine if the information in the content is relevant to the query. If the content is relevant, return "1". If the content is not relevant, return "0".

    web_page_content: "{text}"
    query: "{query}"
    
    Query: "What is ACC 7640?"
    web_page_content: "
    **ACCT 7640 Climate and Financial Markets**

    Climate change might be the defining challenge of our times, with a wide range of effects on financial markets and the broader economy. 

    Spring

    Also Offered As: [BEPP 7640](https://catalog.upenn.edu/search/?P=BEPP%207640 "BEPP 7640")

    Mutually Exclusive: [BEPP 2640](https://catalog.upenn.edu/search/?P=BEPP%202640 "BEPP 2640")

    0.5-1 Course Unit
    "
    Since it specifically mention the course we are talking about and the course description 
    Expected Output: "1"

    but for 

    web_page_content: "

    ACCT 7471 Financial Disclosure Analytics**

    This course focuses on the analysis of financial communications between corporate managers and outsiders, including the required financial statements, voluntary disclosures, and interactions with investors, analysts, and the media. 

    Fall or Spring

    Mutually Exclusive: [ACCT 7470](https://catalog.upenn.edu/search/?P=ACCT%207470 "ACCT 7470")

    Prerequisite: [ACCT 6110](https://catalog.upenn.edu/search/?P=ACCT%206110 "ACCT 6110") 

    "

    Expected Output: "1"

    second example:
    query:"What is the contact for financial aid support"
    web_page_content:"
    SRFS Utility Links
    ------------------

    *   [Path@Penn](https://srfs.upenn.edu/path-at-penn "Path@Penn")
    *   [University Catalog](https://catalog.upenn.edu/ "University Catalog")
    *   [University of Pennsylvania](https://www.upenn.edu/ "University of Pennsylvania")
    "
    return 0 

    else if
    web_page_content:"
    Questions for Student Financial Services and the Office of the University Bursar](https://srfs.upenn.edu/contact#)

    <table><tbody><tr><th>Phone&nbsp;</th><td>215-898-1988<Mailing Address (Outside Scholarships)</th><td>University of Pennsylvania<br>Student Financial Services<br>Franklin Building, Room 100<br>3451 Walnut Street<br>Philadelphia, PA 19104</td></tr></tbody></table>
    "
    return 1 
    because there is the phone number and the address of the finanical aid 

    given 
    web_page_content: "{text}"
    query: "{query}"
    output: should be only 1 or 0 nothing else no text or anything else just 1 or 0
    Be very picky if only a part of the query is answered return 0 it must be that the paragraph might contain the whole answer to the question to output 1:
    """
    response = model.generate_content(prompt)
    return response.text


"""
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