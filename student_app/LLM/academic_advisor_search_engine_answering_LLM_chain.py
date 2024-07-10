
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
#from langchain_core.output_parsers import StrOutputParser

from pinecone import Pinecone
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
import langchain_pinecone
import langchain
from langchain.schema import Document
from typing import List

# Load environment variables from .env file
load_dotenv()

# Environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY_ACADEMIC_ADVISOR")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_POOL_THREADS = 4

MODEL_NAME = "llama3-70b-8192"
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
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Fonction chronométrée pour invoquer Google Search API
@timeit
def timed_invoke_google(query):
    #return tool_google.run(query)
    return tool_google.results(query, 5)

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



# Fonction principale renommée
@time_first_chunk
def LLM_chain_search_engine_and_answering(content, search_engine_query, prompt_answering, student_profile, chat_history, university, method, course_id, keywords):

    set_google_cse_id(university)



    if method == "search_engine":

        # GOOGLE SEARCH API 
        global tool_google
        tool_google = GoogleSearchAPIWrapper()

        print("\n")
        print("\n")
        print("Search enginge query is : \n")
        print(search_engine_query)
        print("\n")
        print("\n")

        # Utiliser la variable content et combined_urls dans l'appel à timed_invoke_google
        answer_search_engine = timed_invoke_google({f"{search_engine_query}"})

        print("\n")
        print("\n")
        print("Answer from the search engine: \n")
        print(answer_search_engine)
        print("\n")
        print("\n")
    


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
            ]
        )

        chain = prompt_search_engine | GROQ_LLM 

        '''
        with_message_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="messages",
        )

        config = {"configurable": {"session_id": "abc1"}}
        '''

        #for r in with_message_history.stream(
        for r in chain.stream(
            {"messages": [HumanMessage(content=content)],"university": university, "search_engine": answer_search_engine,"student_profile": student_profile, "chat_history": chat_history}
            #config=config,
        ):
            #print(r.content, end="|")
            yield r.content + "|"



    #Pour les routes cherchant des informations dans un document en particulier
    elif method == "RAG":


        rag_info = query_pinecone(search_engine_query, course_id, keywords)
        

        print("\n")
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
            {"messages": [HumanMessage(content=content)],"university": university, "search_engine": rag_info,"student_profile": student_profile, "chat_history": chat_history}
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
            {"messages": [HumanMessage(content=search_engine_query)],"university": university, "student_profile": student_profile, "chat_history": chat_history}
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