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
        "do you support war ?",
        "nazi",
        "israel",
        "palestine",
        "trump",
        "biden",
        "obama",
        "democrat",
        "republican",
        "war",
        "election",
        "racism",
        "sexism",
        "homophobia",
        "transphobia",
        "fascism",
        "communism",
        "socialism",
        "terrorism",
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
        "what is your name",
        "How are you?",
        "What is your favorite color?",
        "What is your favorite food?",
        "What is your favorite movie?",
        "are we friends?",
        "what is your favorite song?",
        "do you love me?",
        "let's be friends",
    ],
)


# we place both of our decisions together into single list
routes = [politics, chitchat]


rl = RouteLayer(encoder=encoder, routes=routes)