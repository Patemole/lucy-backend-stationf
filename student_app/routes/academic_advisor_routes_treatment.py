import time
from functools import wraps
from student_app.routes.academic_advisor_routes import rl
import student_app.prompts.academic_advisor_perplexity_search_prompts as prompts



# Définir le décorateur
def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print("For the route treatment")
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    return wrapper

#Il faut rajouter un "search_engine", un "RAG" ou "nothing" en plus dans les paramètres a renvoyer pour savoir quoi utiliser ensuite dans la fonction qui asnwer 
@timing_decorator
async def academic_advisor_router_treatment(input_message, 
                                            chat_id, 
                                            username,
                                            course_id,
                                            chat_history = None,):

    print("Routing in progress...")
    print("\n")

    router_answer = rl(input_message)
    print("The route chosen is:")
    print(router_answer)
    print("\n")

    if router_answer.name == "politics":
        prompt_answering = prompts.system_politics
        question_type = "politics"
        

    elif router_answer.name == "chitchat":
         prompt_answering = prompts.system_chitchat
         question_type = "chitchat"
         
    elif router_answer.name == "problem":
        prompt_answering = prompts.system_problem
        question_type = "problem"
        
    elif router_answer.name == "major_selection":
         prompt_answering = prompts.system_major_selection
         question_type = "major_selection"
     
     #if not politics or chitchat then it is general AA questions 
    #else:
    elif router_answer.name == None:
         prompt_answering = "normal"
         question_type = "normal"
    return prompt_answering, question_type
