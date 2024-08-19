class RunLlm:

    def __init__(self, llm_architecture: str = "perplexity" or "exa"):
        self.llm = llm_architecture

    async def run_llm(self,
                      input_message: str,
                      student_profile: str,
                      university: str,
                      chat_id: str,
                      username: str,
                      course_id: str):
        
        ### Perplexity ### 
        if self.llm == "perplexity":

            import logging
            import datetime

            from fastapi.responses import StreamingResponse

            from student_app.database.dynamo_db.chat import store_message_async

            from student_app.LLM.academic_advisor_perplexity_API_request import LLM_pplx_stream_with_history
            from student_app.database.dynamo_db.chat import store_message_async, get_messages_from_history
            from student_app.prompts.create_prompt_with_history_perplexity import reformat_prompt, reformat_messages ,set_prompt_with_history
            from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

            from student_app.profiling.profile_generation import LLM_profile_generation
            from student_app.prompts.academic_advisor_prompts import system_normal_search, system_normal_search_V2, system_fusion, system_chitchat, system_profile
            from student_app.prompts.academic_advisor_predefined_messages import predefined_messages_prompt, predefined_messages_prompt_V2
            from student_app.prompts.academic_advisor_user_prompts import user_with_profil
            from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

            prompt_answering, question_type, model = await academic_advisor_router_treatment(input_message=input_message, llm_api=self.llm)
            
            # student_profile = "Mathieu an undergraduate junior in the engineering school at UPENN majoring in computer science and have a minor in maths and data science, interned at mckinsey as data scientist and like entrepreneurship"
            print(f"Student profil from firestore : {student_profile}")

            domain = f"site:{university}.edu"

            try:
                messages = await get_messages_from_history(chat_id=chat_id, n=6)
            except Exception as e:
                logging.error(f"Error while retrieving 'n' messages from chat history items: {str(e)}")

            predefined_messages = []

            if question_type == "normal":
                try:
                    import datetime 
                    date = datetime.date.today()

                    system_prompt = await reformat_prompt(prompt=prompt_answering, university=university, date=date, domain=domain, student_profile=student_profile)
                except Exception as e:
                    logging.error(f"Error while reformating system prompt: {str(e)}")

                try:
                    predefined_messages = await reformat_messages(messages=predefined_messages_prompt_V2, university="university of pennsylvania", student_profile=student_profile)
                except Exception as e:
                    logging.error(f"Error while reformating the predefined messages: {str(e)}")

                try:
                    user_prompt = await reformat_prompt(prompt=user_with_profil, input=input_message, domain=domain)
                except Exception as e:
                    logging.error(f"Error while reformating user prompt: {str(e)}")

            elif question_type == "chitchat":
                try:
                    system_prompt = await reformat_prompt(prompt=prompt_answering, university=university, student_profile=student_profile)
                except Exception as e:
                    logging.error(f"Error while reformating system prompt: {str(e)}")
                user_prompt = input_message

            try:
                prompt = await set_prompt_with_history(system_prompt=system_prompt, user_prompt=user_prompt, chat_history=messages, predefined_messages=predefined_messages)
            except:
                logging.error(f"Error while setting prompt with history: {str(e)}")

            # Async storage of the input
            try:
                await store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message)
            except Exception as e:
                logging.error(f"Error while storing the input message: {str(e)}")

            # Stream the response
            # def event_stream():
            #     for content in LLM_pplx_stream_with_history(PPLX_API_KEY=PPLX_API_KEY, messages=prompt):
            #         # print(content, end='', flush=True)
            #         yield content + "|"

            # Stream response from Perplexity LLM with history 
            try:
                return StreamingResponse(LLM_pplx_stream_with_history(messages=prompt, model=model), media_type="text/event-stream")
                # return StreamingResponse(event_stream(), media_type="text/event-stream")
            except Exception as e:
                logging.error(f"Error while streaming response from Perplexity LLM with history: {str(e)}") 
        

        ### EXA ###
        if self.llm == "exa":

            import logging
            import datetime

            from fastapi.responses import StreamingResponse

            from student_app.database.dynamo_db.chat import store_message_async

            from student_app.database.dynamo_db.chat import store_message_async, get_messages_from_history
            from student_app.prompts.create_prompt_with_history_perplexity import reformat_prompt, reformat_messages ,set_prompt_with_history
            from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment

            from student_app.prompts.academic_advisor_predefined_messages import predefined_messages_prompt, predefined_messages_prompt_V2
            from student_app.prompts.academic_advisor_user_prompts import user_with_profil
            from student_app.routes.academic_advisor_routes_treatment import academic_advisor_router_treatment
            
            from student_app.LLM.groq_api import llm_answer_with_groq_async

            prompt_answering, question_type, model = await academic_advisor_router_treatment(input_message=input_message, llm_api=self.llm)

            domain = f"{university}.edu"

            try:
                messages = await get_messages_from_history(chat_id=chat_id, n=6)
            except Exception as e:
                logging.error(f"Error while retrieving 'n' messages from chat history items: {str(e)}")

            predefined_messages = []

            if question_type == "normal":
                try:
                    from student_app.LLM.groq_api import get_keywords
                    keyword = get_keywords(input_message)
                    print(keyword)
                except Exception as e:
                    logging.error(f"Error while getting the keyword with groq: {str(e)}")

                try:
                    from third_party_api_clients.exa.exa_api import exa_api_url_and_summary
                    exa_search_results = await exa_api_url_and_summary(query=input_message, keyword=keyword, domain=domain)
                except Exception as e:
                    logging.error(f"Error while searching the web with EXA API: {str(e)}")

                try:
                    import datetime 
                    date = datetime.date.today()

                    system_prompt = await reformat_prompt(prompt=prompt_answering, university=university, date=date, domain=domain, student_profile=student_profile, search_results=exa_search_results)
                except Exception as e:
                    logging.error(f"Error while reformating system prompt: {str(e)}")

                try:
                    predefined_messages = await reformat_messages(messages=predefined_messages_prompt_V2, university="university of pennsylvania", student_profile=student_profile)
                except Exception as e:
                    logging.error(f"Error while reformating the predefined messages: {str(e)}")

                try:
                    from student_app.prompts.academic_advisor_user_prompts import user_exa
                    user_prompt = await reformat_prompt(prompt=user_exa, input=input_message)
                except Exception as e:
                    logging.error(f"Error while reformating user prompt: {str(e)}")

            elif question_type == "chitchat":
                try:
                    system_prompt = await reformat_prompt(prompt=prompt_answering, university=university, student_profile=student_profile)
                except Exception as e:
                    logging.error(f"Error while reformating system prompt: {str(e)}")
                user_prompt = input_message

            try:
                prompt = await set_prompt_with_history(system_prompt=system_prompt, user_prompt=user_prompt, chat_history=messages, predefined_messages=predefined_messages)
            except:
                logging.error(f"Error while setting prompt with history: {str(e)}")

            # Async storage of the input
            try:
                await store_message_async(chat_id, username=username, course_id=course_id, message_body=input_message)
            except Exception as e:
                logging.error(f"Error while storing the input message: {str(e)}")

            # Stream response from Perplexity LLM with history 
            try:
                return StreamingResponse(llm_answer_with_groq_async(messages=prompt, model=model), media_type="text/event-stream")
            except Exception as e:
                logging.error(f"Error while streaming response from Groq LLM with history: {str(e)}") 



