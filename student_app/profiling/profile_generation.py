# Importations et initialisations
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os
from student_app.prompts.academic_advisor_profil_generation_prompts import system

prompt_answering = system

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

MODEL_NAME = "llama3-70b-8192"


# Fonction principale renommée
def LLM_profile_generation(username: str, academic_advisor: str, year: str, university: str, faculty: str, major: str, minor: str):

    print("\n")
    print("\n")
    print(f"Profiling of the user")
    print(f"username: {username}, year: {year}, university: {university}, School: {faculty}, major: {major}, minor: {minor}, academic_advisor: {academic_advisor}")

    try:
        student_profile = f"My name is {username}. I am enrolled at {university} in the {faculty} school. I am majoring in {major} and minoring in {minor}. Currently in my {year} year, I am guided by academic advisor: {academic_advisor}."
        return student_profile
    except Exception as e:
        print(e)

"""
# Fonction principale renommée
def LLM_profile_generation(prompt_answering: str, username: str, academic_advisor: str, year: str, university: str, faculty: str, major: str, minor: str):

    print("\n")
    print("\n")
    print(f"Profiling of the user")
    print(f"username: {username}, year: {year}, university: {university}, School: {faculty}, major: {major}, minor: {minor}, academic_advisor: {academic_advisor}")

    try:
        GROQ_LLM = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)


        standalone_system_prompt = prompt_answering
        profile_generation_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", standalone_system_prompt),
                ("human", "{username}, {year}, {university}, {faculty}, {major}, {minor}, {academic_advisor}"),
            ]
        )

        profiling_generation = profile_generation_prompt | GROQ_LLM 

        config = {"configurable": {"username":username}}
        response = profiling_generation.invoke({"username": username, "university": university, "faculty": faculty, "major": major, "minor": minor, "year": year, "academic_advisor": academic_advisor}, config=config)

        return response.content
    except Exception as e:
        print(e)
"""