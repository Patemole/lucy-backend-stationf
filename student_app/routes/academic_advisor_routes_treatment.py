import time
from functools import wraps
from student_app.routes.academic_advisor_routes import rl

from student_app.LLM.academic_advisor_search_engine_answering_LLM_chain import  LLM_chain_search_engine_and_answering
import student_app.prompts.academic_advisor_search_engine_and_answering_prompts

from student_app.LLM.academic_advisor_reformulation_LLM_chain import LLM_chain_reformulation
#from airs.prompts.academic_advisor_reformulations_prompts import 



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

    #TODO modify here for inputting the right student profile 
    student_profile = "Mathieu a junior in the engineering school majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"

    print("Routing in progress...")
    print("\n")

    router_answer = rl(input_message)
    print("The route chosen is:")
    print(router_answer)
    print("\n")

    if router_answer.name == "politics":
        prompt_answering = student_app.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_politics
        #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
        search_engine_query = input_message #Car il n'y a pas de reformulation ici         keywords = ""
        return search_engine_query, prompt_answering, student_profile
        

    elif router_answer.name == "chitchat":
         prompt_answering = student_app.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_chitchat
         search_engine_query = input_message #Car il n'y a pas de reformulation ici
         keywords = ""
         return search_engine_query, prompt_answering, student_profile
         
     

     #if not politics or chitchat then it is general AA questions 
    #else:
    elif router_answer.name == None:
         prompt_answering = student_app.prompts.academic_advisor_search_engine_and_answering_prompts.general_prompt
         print("Route is General AA")
         print("\n")
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         reformulated_input = LLM_chain_reformulation(content=input_message, 
                                                 chat_id=chat_id, 
                                                 username=username,
                                                 course_id=course_id)
         print("The reformulated input is: ", reformulated_input)
         search_engine_query = reformulated_input
         #search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords



    '''

    if router_answer.name == "politics":
        print("\n")
        print("La route choisi est la politique")
        print("\n")
        prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_politics
        #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
        search_engine_query = input_message #Car il n'y a pas de reformulation ici 
        method = "nothing"
        keywords = ""
        return search_engine_query, prompt_answering, student_profile, method, keywords
        

    elif router_answer.name == "chitchat":
         print("\n")
         print("La route choisi est le chitchat")
         print("\n")
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_chitchat
         search_engine_query =  LLM_chain_reformulation(input_message, chat_history)
         #search_engine_query = input_message #Car il n'y a pas de reformulation ici
         method = "nothing"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
         
     
     elif router_answer.name == None:
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_chitchat
         print("\n")
         print("La route choisi est la None")
         print("\n")
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query =  LLM_chain_reformulation(input_message, chat_history)
         #search_engine_query = input_message #for testing before going further
         method = "nothing"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
    
    
    if router_answer.name == "registration_tips":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_registration_tips
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
         

    if router_answer == "general_directives":
        print("\n")
        print("La route choisi est general directives")
        print("\n")
        prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_general_directives
        #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
        search_engine_query = input_message #for testing before going further
        method = "search_engine"
        keywords = ""
        return search_engine_query, prompt_answering, student_profile, method, keywords
       

    if router_answer.name == "class_suggestions":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_class_suggestions
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
        

    if router_answer.name == "major_selection":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_major_selection
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
        

    if router_answer.name == "career":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_career
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
         

    if router_answer.name == "contact_advisor":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_contact_advisor
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
         

    if router_answer.name == "single_course":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_single_course
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "RAG"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords
        

    if router_answer.name == "challenges":
         prompt_answering = airs.prompts.academic_advisor_search_engine_and_answering_prompts.prompt_challenges
         #search_engine_query =  LLM_chain_reformulation(input_message, chat_history, student_profile)
         search_engine_query = input_message #for testing before going further
         method = "search_engine"
         keywords = ""
         return search_engine_query, prompt_answering, student_profile, method, keywords

    

    '''
         
