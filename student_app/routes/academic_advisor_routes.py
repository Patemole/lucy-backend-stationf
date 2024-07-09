from semantic_router import Route
from semantic_router.encoders import OpenAIEncoder
from semantic_router.layer import RouteLayer
from dotenv import load_dotenv
import os

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
encoder = OpenAIEncoder()


# we could use this as a guide for our chatbot to avoid political conversations
politics = Route(
    name="politics",
    utterances=[
        "isn't politics the best thing ever",
        "why don't you tell me about your political opinions",
        "don't you just love the president" "don't you just hate the president",
        "they're going to destroy this country!",
        "they will save the country!",
    ],
)

#Classique conversation with Lucy
chitchat = Route(
    name="chitchat",
    utterances=[
        "how's the weather today?",
        "how are things going?",
        "lovely weather today",
        "the weather is horrendous",
        "let's go to the chippy",
    ],
)


#Conversation for registration help
registration_tips  = Route(
    name="registration_tips",
    utterances=[
        "How can I add a class in path at penn?",
        "What are the steps to drop from a course in path at penn?",
        "How can i ask for a permission to join a course?",
    ],
)

#Conversation for general deadlines
general_deadlines  = Route(
    name="general_directives",
    utterances=[
        "When is the last day to drop a course?",
        "When is advance registration?",
        "When is the spring break?",
        "How do I register for classes?",
        "What is the deadline to drop a course for the fall 2024?",
        "How do I get a copy of my transcript?",
        "Where can I find the academic calendar?",
        "How do I change my major?",
        "When is the deadline to declare a major?",
        "How do I request a leave of absence?",
        "How do I ask for a permission request for CIS5370 on Path@Penn?",
        "What are the graduation requirements for my program?",
        "How do I update my personal information on my student record?",
        "Where can I find the final exam schedule?",
        "When is the deadline to ask for an internal transfer (e.g., from the College to Wharton)?",
        "How can I apply for an internal transfer (e.g., from the Engineering School to Wharton)?",
        "What is the school's policy on using AI?",
        "How do I request a letter of recommendation?",
        "Where can I find information on student health insurance?",
        "How do I apply for a student ID card?",
    ],
)


#Conversation for class suggestions to go to several documents 
class_suggestions  = Route(
    name="class_suggestions",
    utterances=[
        "Where can I find the list of technical electives I can take?",
        "What classes can I take next semester?",
        "Can you give me a list of technical electives I can take next semester?",
        "How many credits do I need to graduate?",
        "What electives do I need to graduate?",
    
    ],
)

#Conversation for major selection
major_selection  = Route(
    name="major_selection",
    utterances=[
        "which major can i choose from?",
        "Given that i like computers what studies woudl you recommend me to do?",
    ],
)

#Conversation for career selection to go several documents
career  = Route(
    name="career",
    utterances=[
        "Can I get the list of all majors available to me in the College of Arts and Sciences?",
        "When is the deadline for declaring my major?",
        "Can I get a selection of majors given my preferences?",
        "Can I ask questions about career planning given my interests and major?",
        "If I want to be a data scientist, what major should I take?",
        "What is the difference between a CS BAS and BSE major?",
        "What career opportunities are available for Psychology majors?",
        "How do I decide between majoring in Biology or Chemistry?",
        "What are the benefits of majoring in Data Science?",
        "How do I schedule an appointment with a career advisor?",
        "What internships are available for business students?",
        "What are the highest paying majors?",
        "How do I get involved in undergraduate research?",
        "What minors can I take as a major in Computer Science?",
        "Where can I find alumni success stories?",

    ],
)


#Conversation for contacting the advisor
contact_advisor  = Route(
    name="contact_advisor",
    utterances=[
        "Who is my academic advisor?",
        "How can I contact my advisor?",
        "Can i ask this question to my advisor?",
    ],
)

#On va chercher dans un document spécifique 
single_course = Route(
    name="single_course",
    utterances=[
        "Can you give me more informations about this course?",
        "What is the grading of this course?",
        "What is the description of this course?",
        "What are the prerequisites for this course?",
        "What is the name of the intructor for this course?",
        "Can you provide the syllabus for CIS1100?",
        "What is ESE3060 about?",
    ],
)


#On va chercher dans un document spécifique 
challenges = Route(
    name="challenges",
    utterances=[
        "I am struggling with my cs class can you help me?",
        "I am afraid of failing the econ class what can i do?",
        "I am stress about my work and my classes",
    ],
)


# we place both of our decisions together into single list
routes = [politics, chitchat, career, registration_tips, general_deadlines, class_suggestions, single_course, challenges, major_selection, contact_advisor]


rl = RouteLayer(encoder=encoder, routes=routes)