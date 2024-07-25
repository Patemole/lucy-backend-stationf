
# Importations et initialisations
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
import os
import time
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.chat_message_histories import ChatMessageHistory
from functools import wraps
import time
import concurrent.futures

#from langchain_core.output_parsers import StrOutputParser
from datetime import datetime

from pinecone import Pinecone
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
import langchain_pinecone
import langchain
from langchain.schema import Document
from typing import List
from student_app.scraping.scraping import fetch_content_with_jinai
from student_app.LLM.academic_advisor_text_cleaning import extract_relevant_info
#TODO uncomment if reformulation on
from student_app.LLM.academic_advisor_reformulation_LLM_chain import LLM_chain_reformulation

# Import AWS memory 
from database.dynamo_db.chat import AWSDynamoDBChatMessageHistory, TABLE_NAME, table
from langchain_core.runnables import ConfigurableFieldSpec




# Load environment variables from .env file
load_dotenv()

# Environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY_ACADEMIC_ADVISOR")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_POOL_THREADS = 4

MODEL_NAME = "llama3-8b-8192"
#MODEL_NAME = "mixtral-8x7b-32768"


# Pinecone API Client
class PineconeApiClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PineconeApiClient, cls).__new__(cls)
            pinecone = Pinecone(api_key=PINECONE_API_KEY, environment="gcp-starter")
            cls.index = pinecone.Index("pinecone-test1", pool_threads=PINECONE_POOL_THREADS)
            text_embeddings = OpenAIApiClient().text_embeddings
            cls.vectorstore = langchain_pinecone.Pinecone(cls.index, text_embeddings, "text")
        return cls._instance
    

# OpenAI API Client
class OpenAIApiClient:
    _instance = None

    def __init__(self):
        self.text_embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        self.open_ai_client = OpenAI(api_key=OPENAI_API_KEY)

    def get_langchain_open_ai_api_client(self):
        return langchain.OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    


def query_pinecone(user_input, class_id, keywords):
    query = generate_enhanced_query(user_input, keywords)
    if class_id:
        #filter = {"class_id": class_id}
        filter = {"course_id": class_id}
        retrieved_docs: List[Document] = PineconeApiClient().vectorstore.similarity_search(query=query, k=5, filter=filter)
    else:
        retrieved_docs: List[Document] = PineconeApiClient().vectorstore.similarity_search(query=query, k=5)
    print(f"retrieved_docs: {retrieved_docs}")
    return retrieved_docs


def generate_enhanced_query(user_input, keywords):
    combined_query = user_input + " " + " ".join(keywords)
    return combined_query


# Fonction pour mesurer le temps de génération du premier chunk
def time_first_chunk(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        first_chunk_time = time.time()
        for chunk in result:
            print(f"First chunk generation time: {first_chunk_time - start_time} seconds")
            yield chunk
        end_time = time.time()
        print(f"Total generation time: {end_time - start_time} seconds")
    return wrapper

# Fonction pour mesurer le temps d'exécution
def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        return result
    return wrapper

# Fonction pour récupérer l'historique de session
# def get_session_history(session_id: str) -> AWSDynamoDBChatMessageHistory:
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]

# Create the history for the memory
def get_dynamoDB_history(chat_id: str, username: str, course_id: str) -> AWSDynamoDBChatMessageHistory:
    return AWSDynamoDBChatMessageHistory(
        table=table,
        chat_id=chat_id,
        # timestamp=datetime.now().isoformat(),
        course_id=course_id,
        username=username,
        table_name=TABLE_NAME,
        session_id=chat_id,
                primary_key_name="chat_id",
                key={
                    "chat_id": chat_id,
                    "timestamp": datetime.now().isoformat()
                    },
    )


# Fonction chronométrée pour invoquer Google Search API
@timeit
def timed_invoke_google(query):
    #return tool_google.run(query)
    #TODO test for different number of websites returned
    return tool_google.results(query, 3)

@timeit
def set_google_cse_id(university):

    if university == "upenn":
        GOOGLE_CSE_ID_UPENN = os.getenv("GOOGLE_CSE_ID_UPENN")
        os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID_UPENN

    elif university == "harvard":
        GOOGLE_CSE_ID_HARVARD = os.getenv("GOOGLE_CSE_ID_HARVARD")
        os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID_HARVARD

    elif university == "cornell":
        GOOGLE_CSE_ID_CORNELL = os.getenv("GOOGLE_CSE_ID_CORNELL")
        os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID_CORNELL

    elif university == "mit":
        GOOGLE_CSE_ID_MIT = os.getenv("GOOGLE_CSE_ID_MIT")
        os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID_MIT

    elif university == "columbia":
        GOOGLE_CSE_ID_COLUMBIA = os.getenv("GOOGLE_CSE_ID_COLUMBIA")
        os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID_COLUMBIA
    else:
        raise ValueError(f"University '{university}' is not recognized. Please provide a valid university name.")


global store
store = {}

#fonction to fetch content from the web calling scraping method from scraping.py
def process_search_results(answer_search_engine):
    urls = [result['link'] for result in answer_search_engine]
    all_content = ""
    for url in urls:
        content = fetch_content_with_jinai(url)
        all_content += f"\nContent from {url}:\n{content}\n"
    return all_content


def chunk_text_by_words_with_overlap(text, max_words, overlap_words):
    # Split the text into lines first
    lines = text.split('\n')
    
    # Initialize variables
    chunks = []
    current_chunk = []
    current_word_count = 0

    for line in lines:
        # Split each line into words
        words = line.split()
        line_word_count = len(words)

        while words:
            # Determine the number of words to take in this iteration
            take_words = min(max_words - current_word_count, len(words))

            # Add the words to the current chunk
            current_chunk.extend(words[:take_words])
            current_word_count += take_words
            words = words[take_words:]

            # If the current chunk has reached max_words, finalize it
            if current_word_count >= max_words:
                chunks.append(' '.join(current_chunk).strip())
                # Prepare the next chunk with overlap
                current_chunk = current_chunk[-overlap_words:] if overlap_words < max_words else current_chunk
                current_word_count = len(current_chunk)

    # Add the last chunk if any
    if current_chunk:
        chunks.append(' '.join(current_chunk).strip())

    return chunks



def extract_relevant_info_parallel(query, chunks):
    relevant_chunks = []

    def process_chunk(chunk, index):
        result = extract_relevant_info(query, chunk)
        return (index, chunk, result)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, chunk, i) for i, chunk in enumerate(chunks)]
        for future in concurrent.futures.as_completed(futures):
            index, chunk, result = future.result()
            if "1" in result: # Check if the result is "1"
                relevant_chunks.append((index, chunk))

    return relevant_chunks



# Fonction principale renommée
@time_first_chunk
def LLM_chain_search_engine_and_answering(content, 
                                          search_engine_query, 
                                          prompt_answering, 
                                          student_profile, 
                                          chat_id, 
                                          university, 
                                          method, 
                                          course_id, 
                                          username,
                                          keywords):

    set_google_cse_id(university)


    if method == "search_engine":

        # GOOGLE SEARCH API 
        global tool_google
        tool_google = GoogleSearchAPIWrapper()


        print("Content = student query is : \n")
        print(content)
        print("\n")

        print("Search enginge query after reformulation is : \n")
        print(search_engine_query)
        print("\n")

        """
        #TODO erase if it works other way
        #new_query = LLM_chain_reformulation(search_engine_query)

        print("\n")
        print("\n")
        print("New query is : \n")
        print(new_query)
        print("\n")
        print("\n")
        """
        
        # Utiliser la variable content et combined_urls dans l'appel à timed_invoke_google
        answer_search_engine = timed_invoke_google({f"{search_engine_query}"})
        
        
        print("Answer from the search engine: \n")
        print(answer_search_engine)
        print("\n")
        
        """
        #get the content from the search engine for each pages that the search engine returned
        search_results_jinai = process_search_results(answer_search_engine)

        print("\n")
        print("\n")
        print("Answer from jinai: \n")
        print(search_results_jinai)
        print("\n")
        print("\n")

        max_words_per_chunk = 100  # You can adjust the number of words as needed
        overlap_words  = 10  # You can adjust the number of words as needed
        chunks = chunk_text_by_words_with_overlap(search_results_jinai, max_words_per_chunk, overlap_words)

        print("\n")
        print("\n")
        print("chunks: \n")
        #for i, chunk in enumerate(chunks):
        #    print(f"Chunk {i+1}:\n{chunk}\n")
        print("\n")
        print("\n")

        # Process the search results with Gemini model to get the cleaned text
        #TODO: test with search_engine_query or new_query or both concatenated
        relevant_chunks = extract_relevant_info_parallel(search_engine_query, chunks)

        # Concatenate relevant chunks with the desired format
        separator = "\n---\n"  # Define a separator to indicate different chunks
        concatenated_relevant_chunks = ""

        for i, (index, chunk) in enumerate(relevant_chunks):
            concatenated_relevant_chunks += f"Chunk {index + 1}:\n{chunk}\n{separator}"

        print("\n")
        print("\n")
        print("Relevant chunks concatenated are the following: \n")
        print(concatenated_relevant_chunks)
        print("\n")
        print("\n")
        """

        GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)

        # Stockage intermédiaire pour les différentes sessions
        

        #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
        prompt_search_engine = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    prompt_answering,
                ),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "user","{input}"
                )
            ]
        )

        chain = prompt_search_engine | GROQ_LLM 

        chain_with_memory = RunnableWithMessageHistory(
            chain,
            get_dynamoDB_history,
            input_messages_key="input",
            history_messages_key="messages",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="chat_id",
                    annotation=str,
                    name="Chat ID",
                ),
                ConfigurableFieldSpec(
                    id="username",
                    annotation=str,
                    name="Username",
                ),
                ConfigurableFieldSpec(
                    id="course_id",
                    annotation=str,
                    name="Course ID",
                ),
            ],
        )

        '''
        with_message_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="messages",
        )

        config = {"configurable": {"session_id": "abc1"}}
        

        #for r in with_message_history.stream(
        for r in chain.stream(
            {"messages": [HumanMessage(content=content)],"university": university, "search_engine": answer_search_engine ,"student_profile": student_profile, "chat_history": chat_history}
            #config=config,
        ):
            #print(r.content, end="|")
            yield r.content + "|"
        '''
        config = {"configurable": {"chat_id": chat_id, "username":username, "course_id": course_id}}

        for r in chain_with_memory.stream({'input': content,
                                           "university": university,
                                           "search_engine": answer_search_engine,
                                           "student_profile": student_profile}, 
                                          config=config):
            #print(r.content, end="|")
            yield r.content + "|"



    #Pour les routes cherchant des informations dans un document en particulier
    elif method == "RAG":


        rag_info = query_pinecone(search_engine_query, course_id, keywords)
        

        
        print(rag_info)
        print("\n")
    

        GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


        #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
        prompt_search_engine = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    prompt_answering,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt_search_engine | GROQ_LLM


        '''
        with_message_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="messages",
        )

        config = {"configurable": {"session_id": "abc9"}}
        '''

        #for r in with_message_history.stream(
        for r in chain.stream(
            {"messages": [HumanMessage(content=content)],"university": university, "search_engine": rag_info,"student_profile": student_profile}
            #config=config,
        ):
            #print(r.content, end="|")
            yield r.content + "|"
        
        print(prompt_search_engine)




    #Pour les routes chitchat & politics (for now)
    elif method == "nothing":

        GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


        #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
        prompt_search_engine = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    prompt_answering,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt_search_engine | GROQ_LLM


        '''
        with_message_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="messages",
        )

        print("\n")
        print(with_message_history)
        print("\n")

        config = {"configurable": {"session_id": "abc10"}}
        '''

        #for r in with_message_history.stream(
        for r in chain.stream(
            {"messages": [HumanMessage(content=search_engine_query)],"university": university, "student_profile": student_profile}
            #config=config,
        ):
            #print(r.content, end="|")
            yield r.content + "|"

        print(prompt_search_engine)











'''
# Fonction principale renommée
@time_first_chunk
def LLM_chain_search_engine_and_answering(content, search_engine_query, prompt_answering, student_profile, chat_history, university, method):

    set_google_cse_id(university)


    # GOOGLE SEARCH API 
    global tool_google
    tool_google = GoogleSearchAPIWrapper()

    #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
    
    urls = [
        #"https://almanac.upenn.edu/penn-academic-calendar",
        # "https://www.college.upenn.edu/declaring-major", # ajoutez d'autres URLs si nécessaire
    ]
    

    #student_profile2 = "Hugo, junior in the engineering school majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"

    #university = "Harvard University"
 
    # Combiner les URLs en une seule chaîne avec un " - " entre chaque URL
    combined_urls = " - ".join(urls)

    # Utiliser la variable content et combined_urls dans l'appel à timed_invoke_google
    answer_search_engine = timed_invoke_google({f"{search_engine_query} - {combined_urls}"})
    #answer_search_engine = timed_invoke_google({f"{content} - {combined_urls} - {student_profile}"})

    print("\n")
    print(answer_search_engine)
    print("\n")

    GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)

    # Stockage intermédiaire pour les différentes sessions
    global store
    store = {}

    #LES URLS SERONT ENVOYÉS DANS LES PARAMÈTRES DE LA FONCTION
    prompt_search_engine = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt_answering,
                #"Your name is Lucy, and you are an Academic Advisor helping students to help them about general directives at {university}. Based on the student profil: {student_profile} and the informations provided here : {search_engine} answer the question of the student. You need to be friendly",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt_search_engine | GROQ_LLM

    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="messages",
    )

    config = {"configurable": {"session_id": "abc11"}}


    for r in with_message_history.stream(
        {"messages": [HumanMessage(content=content)],"university": university, "search_engine": answer_search_engine,"student_profile": student_profile},
        config=config,
    ):
        #print(r.content, end="|")
        yield r.content + "|"
'''