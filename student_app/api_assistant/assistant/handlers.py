import json
import openai
from openai import AssistantEventHandler, AsyncOpenAI
from .tools.filter_tool.filter_manager import apply_filters
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info, get_sources_json
from .tools.clarification_tool.clarification_manager import get_clarifying_question_output
from .tools.perplexity_tool.image_search import google_image_search
from .tools.perplexity_tool.sources_urls import google_source_search
from .tools.perplexity_tool.student_feedbacks_manager import get_top_comment
from .tools.perplexity_tool.youtube_search_manager import get_youtube_videos
from .tools.perplexity_tool.instagram_search_manager import transform_instagram_data
from .tools.perplexity_tool.instagram_reels_manager import transform_instagram_reels_data
from .tools.perplexity_tool.linkedin_profile_search_manager import transform_linkedin_profiles_data
from functools import wraps
from .tools.RAG_tool.rag_ragie import retrieve_chunks
import time
import asyncio
import logging

# Logging configuration (to be added if it's not already in the main app)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("file_server.log")  # Save logs to a file
    ]
)

def timing_decorator(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@timing_decorator
async def on_event(client, event, input_message, image_bool, university, username, major, minor, year, school):
    """
    Handles various event types without retries.
    """
    try:
        logging.info(f"ON_EVENT triggered: {event.event} for {input_message}")

        # Handle 'requires_action' event
        if event.event == 'thread.run.requires_action':
            logging.info(f"Handling required action event... for {input_message}")
            run_id = event.data.id
            thread_id = event.data.thread_id
            async for data in handle_requires_action(client, event.data, run_id, thread_id, input_message, image_bool, university, username, major, minor, year, school):
                yield data

        # Handle 'delta' event
        elif event.event == 'thread.message.delta':
            for block in event.data.delta.content:
                if block.type == "text" and hasattr(block.text, "value"):
                    delta_text = block.text.value
                    logging.info(f"Delta text received: {delta_text} for {input_message}")
                    yield delta_text + "|"
                else:
                    logging.warning(f"No text content found or unsupported block type: {block.type} for {input_message}")

        # Handle 'completed' event
        elif event.event == 'thread.run.completed':
            logging.info(f"Run completed for {input_message}")
            yield None  # Indicate completion

        # Handle 'failed' event
        elif event.event == 'thread.run.failed':
            logging.error(f"ON_EVENT Run FAILED for event: {event} for {input_message}")
            yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An error occurred while processing your request. Please resend your message'}})}<ERROR_END>\n"
            yield None  # Indicate completion

        # Handle queued and in-progress events
        elif event.event == 'thread.run.queued':
            logging.info(f"ON_EVENT Run QUEUED for event for {input_message}")
        elif event.event == 'thread.run.in_progress':
            logging.info(f"ON_EVENT Run IN_PROGRESS for event: for {input_message}")
        else:
            logging.warning(f"Unhandled event: {event.event} for {input_message}")

    except Exception as e:
        logging.error(f"Error in on_event: {str(e)} for {input_message}", exc_info=True)
        yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An unexpected error occurred. Please try again later.'}})}<ERROR_END>\n"
        yield None


@timing_decorator
async def handle_requires_action(client, data, run_id, thread_id, input_message, image_bool, university, username, major, minor, year, school):
    try:
        logging.info(f"Run requires action: Processing tool calls... for {input_message}")
        tool_outputs = []
        query=input_message
        for tool_call in data.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            logging.info(f"Processing tool: {function_name} for {input_message}")

            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse arguments for {function_name}")
                arguments = {}

            if function_name == "get_current_info":
                reasoning_steps = arguments.get('reasoning_steps', '')
                structured_reasoning = [{"step": i + 1, "description": step} for i, step in enumerate(reasoning_steps)]
                yield f"\n<REASONING_STEPS>{json.dumps({'reasoning_steps': structured_reasoning})}<REASONING_STEPS_END>\n"             
                logging.info(f"reasoning_steps yield {structured_reasoning} for {input_message}")

                query = arguments.get('query', '')
                #sources = arguments.get('sources', [])
                image_bool = arguments.get('image_bool', False)
                model = arguments.get('model', 'small')
                rag_hypothetical_answer = arguments.get('rag_hypothetical_answer', '')
                if model not in ['small', 'large']:
                    model = 'small'
                
                #Yielding the reosoning steps
                rag_task = ""

                info_task = asyncio.create_task(get_up_to_date_info(query, image_bool, model, university, username, major, minor, year, school, input_message))
                rag_task = asyncio.create_task(retrieve_chunks(query, university))

                output = await info_task
                #output = await get_up_to_date_info(query, image_bool, model, university, username, major, minor, year, school, input_message)
                info_result = ";".join([f"{result.get('url')}:{result.get('content')}" for result in output])
                logging.info(f"Current info for query {query} : {info_result} for '{input_message}'")

                #confidence_score = arguments.get('confidence_score')
                #await asyncio.sleep(0.2)
                confidence_score = output[0].get("score") if output else None
                confidence_score = round(confidence_score * 100) if confidence_score is not None else None
                logging.info(f"confidence_score is {confidence_score} for {input_message}")                
                # Convert confidence_score to string and yield it in the desired format
                if confidence_score is not None:  # Ensure the score exists
                    structured_confidence = {"confidenceScore": str(confidence_score)}
                    yield f"\n<CONFIDENCE>{json.dumps({'accuracy_score': structured_confidence})}<CONFIDENCE_END>\n"
                    logging.info(f"confidence_score yield {structured_confidence} for {input_message}")

                logging.info(f"Getting the sources for {input_message}")
                #sources = await google_source_search(google_search_query, university, input_message)
                sources = [{"name": result.get("title"), "url": result.get("url")} for result in output]
                if sources:
                    logging.info(f"Sources received {sources} for {input_message}")
                else:
                    logging.warning(f"No sources for {input_message}")

                """
                text_search = []
                print(f"Sources for search sentences: {sources}")
                for i, source in enumerate(sources, 1):
                    source_name = source.get('name', '')
                    text_search.append({f"Sentence{i}": f"_**[LUCY is searching in {source_name}]**_"})

                logging.info(f"Yielding lucy searching sentence {text_search} for {input_message}")
                yield f"\n<ANSWER_WAITING>{json.dumps({'answer_waiting': text_search})}<ANSWER_WAITING_END>\n"
                """

                try:
                    sources_list = get_sources_json(sources, input_message)  # Ensure async call here
                except json.JSONDecodeError:
                    logging.error(f"Error decoding JSON. Invalid data received. for {input_message}")
                    sources_list = []

                await asyncio.sleep(0.2)
                for source in sources_list:
                    logging.info(f"Sending Source to client: {source} for {input_message}")
                    yield f"\n<JSON_DOCUMENT_START>{json.dumps(source)}<JSON_DOCUMENT_END>\n"

                image_bool = False  # TODO: Change this when we have images
                if image_bool:
                    image_url = await google_image_search(query, input_message)  # Await for async search
                    logging.info(f"Image URL found: {image_url} for {input_message}")
                    yield f"\n<IMAGE_DATA>{json.dumps({'image_data': image_url})}<IMAGE_DATA_END>\n"


                
                await asyncio.sleep(0.2)
                youtube_bool = arguments.get('youtube_bool', False)
                logging.info(f"youtube_bool is {youtube_bool}")



                if youtube_bool:
                    youtube_query = google_search_query + " " + university 
                    logging.info(f"Youtube video search with keywords: {youtube_query} for {input_message}")

                    # Call the updated function to fetch videos and shorts
                    result_youtube_data = await get_youtube_videos(youtube_query, input_message)
                    logging.info(f"Youtube search successful for {result_youtube_data} for {input_message}")

                    # Process videos and yield in the normal format
                    if result_youtube_data["videos"]:
                        logging.info(f"Yielding YouTube videos for {input_message}")
                        yield f"\n<YOUTUBE>{json.dumps({'youtube': result_youtube_data['videos']})}<YOUTUBE_END>\n"

                    # Process Shorts and yield in the Instagram-like format
                    if result_youtube_data["shorts"]:
                        logging.info(f"Yielding YouTube Shorts as Instagram reels for {input_message}")
                        yield f"\n<INSTA>{json.dumps({'insta': result_youtube_data['shorts']})}<INSTA_END>\n"

                    # Call the updated function to fetch videos and shorts
                    result_youtube_data = await get_youtube_videos(youtube_query, input_message)
                    logging.info(f"Youtube search successful for {result_youtube_data} for {input_message}")

                    # Process videos and yield in the normal format
                    if result_youtube_data["videos"]:
                        logging.info(f"Yielding YouTube videos for {input_message}")
                        yield f"\n<YOUTUBE>{json.dumps({'youtube': result_youtube_data['videos']})}<YOUTUBE_END>\n"

                    # Process Shorts and yield in the Instagram-like format
                    if result_youtube_data["shorts"]:
                        logging.info(f"Yielding YouTube Shorts as Instagram reels for {input_message}")
                        yield f"\n<INSTA>{json.dumps({'insta': result_youtube_data['shorts']})}<INSTA_END>\n"

                """
                #TODO look for async or not
                await asyncio.sleep(0.3)
                keywords_reddit_search = arguments.get('keywords_search', '')
                logging.info(f"Reddit student feedbacks with keywords: {keywords_reddit_search} for {input_message}")
                reddit_comment_list = await get_top_comment(university, keywords_reddit_search, input_message)
                logging.info(f"Reddit student feedbacks succesfull for {reddit_comment_list} for {input_message}")
                yield f"\n<REDDIT>{json.dumps({'reddit': reddit_comment_list})}<REDDIT_END>\n"
                
                #TODO change the assistant to make a instagram query
                await asyncio.sleep(0.2)
                instagram_reels_query = ""
                logging.info(f"Instagram reels search with keywords: {instagram_reels_query} for {input_message}")
                #TODO see if useful to make it async
                result_instagram_reels_list = transform_instagram_reels_data(instagram_reels_query, input_message)
                logging.info(f"Instagram reels search succesfull for {result_instagram_reels_list} for {input_message}")
                yield f"\n<INSTA>{json.dumps({'insta': result_instagram_reels_list})}<INSTA_END>\n"
            
                await asyncio.sleep(0.2)
                linkedin_query = ""
                logging.info(f"Linkedin profile search with keywords: {linkedin_query} for {input_message}")
                #TODO see if useful to make it async
                result_linkedin_profile_list = transform_linkedin_profiles_data(linkedin_query, input_message)
                logging.info(f"Linkedin profile search succesfull for {result_linkedin_profile_list} for {input_message}")
                yield f"\n<LINKEDIN>{json.dumps({'linkedin': result_linkedin_profile_list})}<LINKEDIN_END>\n"
               
                
                await asyncio.sleep(0.2)
                instagram_query = ""
                logging.info(f"Instagram search with keywords: {instagram_query} for {input_message}")
                #TODO see if useful to make it async
                result_instagram_profile_list = transform_instagram_data(instagram_query, input_message)
                logging.info(f"Instagram profile search succesfull for {result_instagram_profile_list} for {input_message}")
                yield f"\n<INSTA_CLUB>{json.dumps({'insta_club': result_instagram_profile_list})}<INSTA_CLUB_END>\n"
                """
                
                rag = await rag_task
                #rag = retrieve_chunks(query, university)
                if rag["status"] == "success":
                    rag_result = " ".join([chunk["text"] for chunk in rag["retrieved_chunks"]])
                    logging.info(f"RAG info for query {query} : {rag} for '{input_message}'")
                else:
                    rag_result = ""

                content = f"Web information from university websites: {info_result}\n Content from university private and verified database {rag_result}"



                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": content
                })

            elif function_name == "ask_clarifying_question":
                logging.info(f"Processing clarifying question with arguments: {arguments} for {input_message}")
                tool_output = get_clarifying_question_output(arguments, input_message)
                logging.info(f"Clarifying question output: {tool_output} for {input_message}")
                yield f"\n<ANSWER_TAK>{json.dumps({'answer_TAK_data': tool_output})}<ANSWER_TAK_END>\n"
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(tool_output)
                })
            
            elif function_name == "redirection_to_agent":
                logging.info(f"Processing redirection to agent: {arguments} for {input_message}")
                query = arguments.get('query', '')
                query = "Give me the most specific contacts information (person, email, location, phone number) for the query:" + query
                logging.info(f"Yielding answer waiting for redirection to agent for {input_message}")
                reasoning_steps = arguments.get('reasoning_steps', '')
                structured_reasoning = [{"step": i + 1, "description": step} for i, step in enumerate(reasoning_steps)]
                yield f"\n<REASONING_STEPS>{json.dumps({'reasoning_steps': structured_reasoning})}<REASONING_STEPS_END>\n"             
                logging.info(f"reasoning_steps yield {structured_reasoning} for {input_message}")
                #yield f"\n<ANSWER_WAITING>{json.dumps({'answer_waiting': 'Searching the right contact info to connect to an agent'})}<ANSWER_WAITING_END>\n"

                output = await get_up_to_date_info(
                    query, 
                    image_bool=False, 
                    model="small", 
                    university=university, 
                    username=username, 
                    major=major, 
                    minor=minor, 
                    year=year, 
                    school=school,
                    input_message=input_message,
                    domains=domains
                )
                logging.info(f"Getting right contact info for '{input_message}': {output}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            else:
                logging.warning(f"Function not implemented: {function_name} for {input_message}")
                output = "Function not implemented."
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

        logging.info(f"Submitted all tool outputs. for {input_message}")
        async for data in submit_tool_outputs(client, tool_outputs, run_id, thread_id, query, image_bool, university, username, major, minor, year, school, input_message):
            yield data
    except Exception as e:
        logging.error(f"Error in handle_requires_action: {str(e)} for {input_message}", exc_info=True)
        yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! Looks like we are experiencing high traffic right now. Please try again later.'}})}<ERROR_END>\n"
        yield None


@timing_decorator
async def submit_tool_outputs(client, tool_outputs, run_id, thread_id, query, image_bool, university, username, major, minor, year, school, input_message):
    """
    Submits tool outputs and handles the response.
    """
    try:
        logging.info(f"Submitting tool outputs... for {input_message}")
        stream = await client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            stream=True
        )

        async for event in stream:
            if event.event == "thread.message.delta":
                for block in event.data.delta.content:
                    if block.type == "text" and hasattr(block.text, "value"):
                        delta_text = block.text.value
                        logging.info(f"Delta text from submit_tool_outputs: {delta_text} for {input_message}")
                        yield delta_text + "|"
                    else:
                        logging.warning(f"No text content found in delta block for {input_message}")

            elif event.event == 'thread.run.requires_action':
                logging.info(f"Handling required action event during submit_tool_outputs for {input_message}")
                async for data in handle_requires_action(client, event.data, run_id, thread_id, input_message, image_bool, university, username, major, minor, year, school):
                    yield data

            elif event.event == "thread.run.step.completed":
                logging.info(f"Step completed for {input_message}")
            elif event.event == "thread.run.completed":
                logging.info(f"Run completed for {input_message}")
                yield None  # Indicate completion
                return  # Exit function after successful completion
            elif event.event == "thread.message.completed":
                logging.info(f"Message completed for {input_message}")
                yield None
            elif event.event == 'thread.run.failed':
                logging.error(f"ON_EVENT Run FAILED for event: {event} for {input_message}")
                yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An error occurred while finalizing your request. Please try again later.'}})}<ERROR_END>\n"
                yield None  # Indicate completion
            else:
                logging.warning(f"Unhandled event in submit_tool_outputs: {event.event} for {input_message}")

    except Exception as e:
        logging.error(f"Error in submit_tool_outputs: {str(e)} for {input_message}", exc_info=True)
        yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! Something went wrong while finalizing your request. Please try again later.'}})}<ERROR_END>\n"
        yield None  # Indicate completion


    """
@timing_decorator
async def on_event(client, event, input_message, image_bool, university, username, major, minor, year, school):
    try:
        logging.info(f"ON_EVENT triggered: {event.event} for {input_message}")
        if event.event == 'thread.run.requires_action':
            logging.info(f"Handling required action event... for {input_message}")
            run_id = event.data.id
            thread_id = event.data.thread_id
            async for data in handle_requires_action(client, event.data, run_id, thread_id, input_message, image_bool, university, username, major, minor, year, school):
                yield data

        elif event.event == 'thread.message.delta':
            for block in event.data.delta.content:
                if block.type == "text" and hasattr(block.text, "value"):
                    delta_text = block.text.value
                    logging.info(f"Delta text received: {delta_text} for {input_message}")
                    yield delta_text + "|"
                else:
                    logging.warning(f"No text content found or unsupported block type: {block.type} for {input_message}")

        elif event.event == 'thread.run.completed':
            logging.info(f"Run completed. for {input_message}")
            yield None  # Indicate completion
        elif event.event == 'thread.run.failed':
            logging.error(f"ON_EVENT Run FAILED for event :{event} for {input_message}")
            yield "Oops! We’re experiencing a high volume of activity right now. Please try resending your message in a few moments."
        elif event.event == 'thread.run.queued ':
            logging.info(f"ON_EVENT Run QUEUED for event :{event} for {input_message}")
        elif event.event == 'thread.run.in_progress ':
            logging.warning(f"ON_EVENT Run IN_PROGRESS for event :{event} for {input_message}")
        else:
            logging.warning(f"Unhandled event: {event.event} for {input_message}")
    except Exception as e:
        logging.error(f"Error in on_event handler: {str(e)} for {input_message}", exc_info=True)
        raise
    """

    """
@timing_decorator
async def submit_tool_outputs(client, tool_outputs, run_id, thread_id, query, image_bool, university, username, major, minor, year, school, input_message):
    try:
        logging.info(f"Submitting tool outputs... for {input_message}")
        separation_added = False

        stream = await client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            stream=True
        )
        async for event in stream:
            if event.event == "thread.message.delta":
                for block in event.data.delta.content:
                    if block.type == "text" and hasattr(block.text, "value"):
                        delta_text = block.text.value

                        if not separation_added:
                            yield "\n\n\n\n"
                            separation_added = True

                        logging.info(f"Delta text from submit_tool_outputs: {delta_text} for {input_message}")
                        yield delta_text + "|"
                    else:
                        logging.warning(f"No text content found in delta block: for {input_message}", block)

            elif event.event == 'thread.run.requires_action':
                logging.info(f"Handling required action event during submit_tool_outputs... for {input_message}")
                async for data in handle_requires_action(client, event.data, run_id, input_message, image_bool, university, username, major, minor, year, school):
                    yield data

            elif event.event == "thread.run.step.completed":
                logging.info(f"Step completed. for {input_message}")
            elif event.event == "thread.run.completed":
                logging.info(f"Run completed. for {input_message}")
            elif event.event == "thread.message.completed":
                logging.info(f"Message completed. for {input_message}")
                yield None
            elif event.event == 'thread.run.failed':
                logging.error(f"SUBMIT_TOOL_OUTPUTS Run FAILED for event :{event} for {input_message}")
                yield "Oops! We’re experiencing a high volume of activity right now. Please try resending your message in a few moments."
            elif event.event == 'thread.run.queued ':
                logging.info(f"SUBMIT_TOOL_OUTPUTS Run QUEUED for event :{event} for {input_message}")
            elif event.event == 'thread.run.in_progress ':
                logging.info(f"SUBMIT_TOOL_OUTPUTS Run IN_PROGRESS for event :{event} for {input_message}")
            else:
                logging.warning(f"Unhandled event: {event.event} for {input_message}")
    except Exception as e:
        logging.error(f"Error in submit_tool_outputs: {str(e)} for {input_message}", exc_info=True)
        raise
    """



    """
    def submit_tool_outputs(self, tool_outputs, run_id):
        print("Submitting tool outputs...")
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            event_handler=self
        ) as stream:
            for delta in stream.text_deltas:
                print(delta, end="", flush=True)


    def __init__(self, thread_id, df, response_queue):
        super().__init__()
        self.thread_id = thread_id
        self.df = df
        self.response_queue = response_queue
        self.filtered_data = None
        self.tool_calls = []
        self.run = None  # Will be set after the stream starts

    def on_text_delta(self, delta_text, snapshot_text):
        # Extract the text value from delta_text
        text_value = delta_text.value
        if text_value:
            #print(f"Assistant says: {text_value}")  # Debug statement
            self.response_queue.put(text_value + "|")

    def on_tool_call_created(self, tool_call):
        # Collect the tool call for later processing
        self.tool_calls.append(tool_call)
        print(f"Tool called: {tool_call.function.name}")  # Debug statement

    def on_run_requires_action(self, run):
        print("Run requires action: Processing tool calls...")  # Debug statement
        # Process all collected tool calls
        tool_outputs = []
        for tool_call in self.tool_calls:
            function_name = tool_call.function.name
            print(f"Processing tool: {function_name}")  # Debug statement
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
                print(f"Invalid JSON arguments for tool: {function_name}")  # Debug statement

            if function_name == "get_filters":
                # Process get_filters
                df_filtered = apply_filters(arguments, self.df)
                if df_filtered.empty:
                    output = "No courses match your query."
                    self.filtered_data = []
                    print("No courses matched the filters.")  # Debug statement
                else:
                    self.filtered_data = df_filtered.to_dict(orient='records')
                    output = json.dumps(self.filtered_data)
                    print(f"Filtered courses: {self.filtered_data}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            elif function_name == "get_current_info":
                # Process get_current_info
                query = arguments.get('query', '')
                output = get_up_to_date_info(query)
                print(f"Current info for query '{query}': {output}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            elif function_name == "get_prerequisites":
                # Process get_prerequisites
                course_code = arguments.get('course_code', '').strip().upper()
                prerequisites = get_prerequisites(course_code, self.df)
                if prerequisites is not None:
                    output = f"The prerequisites for {course_code} are: {prerequisites}"
                else:
                    output = f"No prerequisites found for {course_code}."
                print(f"Prerequisites for {course_code}: {prerequisites}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            else:
                # Function not implemented
                output = "Function not implemented."
                print(f"Function not implemented: {function_name}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

        # Submit all tool outputs at once
        run.submit_tool_outputs(tool_outputs)
        print("Submitted all tool outputs.")  # Debug statement

        #self.tool_calls = []

        # **Restart the stream to continue receiving assistant's response**
        #self.run = run  # Update the run instance if necessary
        #self.run.stream_response()

    def on_run_completed(self, run):
        # Signal that the run is completed
        print("Run completed.")  # Debug statement
        self.response_queue.put(None)
"""

"""
import json
import openai
from .tools.filter_tool.filter_manager import apply_filters
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info
from .tools.prerequisites_tool.prerequisites_manager import get_prerequisites

def handle_requires_action(run, thread_id, assistant_id, df):
    tool_outputs = []
    filtered_data = None  # Initialize filtered_data

    for tool in run.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "get_filters":
            try:
                arguments = json.loads(tool.function.arguments)
            except json.JSONDecodeError:
                continue

            # Apply the filters to the DataFrame
            df_filtered = apply_filters(arguments, df)

            if df_filtered.empty:
                output = "No courses match your query."
                filtered_data = []  # Return an empty list
            else:
                # Convert the filtered DataFrame to a list of dictionaries
                filtered_data = df_filtered.to_dict(orient='records')
                # Optionally, you can serialize it to JSON
                output = json.dumps(filtered_data)

            # Append the tool output
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": output
            })

        else:
            # Handle other functions by passing outputs back to the assistant
            try:
                arguments = json.loads(tool.function.arguments)
            except json.JSONDecodeError:
                continue

            if tool.function.name == "get_current_info":
                query = arguments.get('query', '')
                # Call the Perplexity API to get up-to-date information
                output = get_up_to_date_info(query)
            elif tool.function.name == "get_prerequisites":
                course_code = arguments.get('course_code', '').strip().upper()
                prerequisites = get_prerequisites(course_code, df)
                if prerequisites is not None:
                    output = f"The prerequisites for {course_code} are: {prerequisites}"
                else:
                    output = f"No prerequisites found for {course_code}."
            else:
                output = "Function not implemented."

            # Append the tool output
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": output
            })

    if tool_outputs:
        try:
            # Use submit_tool_outputs instead of submit_tool_outputs_and_poll
            run = openai.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        except Exception as e:
            pass

    # Return the updated run and filtered data
    return run, filtered_data, None, None
"""