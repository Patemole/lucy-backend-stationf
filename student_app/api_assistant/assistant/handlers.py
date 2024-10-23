import json
import openai
from openai import AssistantEventHandler, AsyncOpenAI
from .tools.filter_tool.filter_manager import apply_filters
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info, get_sources_json
from .tools.clarification_tool.clarification_manager import get_clarifying_question_output
from .tools.perplexity_tool.image_search import google_image_search
from functools import wraps
import time
import asyncio

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
async def on_event(client, event, query, image_bool, university, username, major, minor, year, school):
    print(f"ON_EVENT: {event.event}")
    if event.event == 'thread.run.requires_action':
        print("Handling required action event...")
        run_id = event.data.id
        thread_id = event.data.thread_id
        # Use async generator
        async for data in handle_requires_action(client, event.data, run_id, thread_id, query, image_bool, university, username, major, minor, year, school):
            yield data

    elif event.event == 'thread.message.delta':
        delta_text = event.data.delta.content[0].text.value
        print(delta_text, end="", flush=True)
        # Yield delta text directly
        yield delta_text + "|"

    elif event.event == 'thread.run.completed':
        print("\nRun completed.")
        yield None  # Indicate completion

@timing_decorator
async def handle_requires_action(client, data, run_id, thread_id, query, image_bool, university, username, major, minor, year, school):
    print("Run requires action: Processing tool calls...")  
    tool_outputs = []
    for tool_call in data.required_action.submit_tool_outputs.tool_calls:
        function_name = tool_call.function.name
        print(f"Processing tool: {function_name}") 

        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            print(f"Failed to parse arguments for {function_name}")
            arguments = {}

        if function_name == "get_current_info":
            query = arguments.get('query', '')
            sources = arguments.get('sources', [])
            image_bool = arguments.get('image_bool', False)

            text_search = []
            for i, source in enumerate(sources, 1):
                source_name = source.get('name', '')
                text_search.append({f"Sentence{i}": f"_**[LUCY is searching in {source_name}]**_"})

            yield f"\n<ANSWER_WAITING>{json.dumps({'answer_waiting': text_search})}<ANSWER_WAITING_END>\n" 

            try:
                sources_list = await get_sources_json(sources)  # Ensure async call here
            except json.JSONDecodeError:
                print("Error decoding JSON. Invalid data received.")
                sources_list = []

            for source in sources_list:
                print(f"\n<JSON_DOCUMENT_START>{json.dumps(source)}<JSON_DOCUMENT_END>\n")
                yield f"\n<JSON_DOCUMENT_START>{json.dumps(source)}<JSON_DOCUMENT_END>\n"
        

            if image_bool:
                image_url = await google_image_search(query)  # Await for async search
                yield f"\n<IMAGE_DATA>{json.dumps({'image_data': image_url})}<IMAGE_DATA_END>\n"

            output = await get_up_to_date_info(query, image_bool, university, username, major, minor, year, school)
            print(f"Current info for query '{query}': {output}") 

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": output
            })

        elif function_name == "ask_clarifying_question":
            print(f"Processing clarifying question with arguments: {arguments}")
            tool_output = await get_clarifying_question_output(arguments)  # Await the clarifying question output
            print(tool_output)
            yield f"\n<ANSWER_TAK>{json.dumps({'answer_TAK_data': tool_output})}<ANSWER_TAK_END>\n" 
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(tool_output)
            })
            
        else:
            output = "Function not implemented."
            print(f"Function not implemented: {function_name}")  
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": output
            })

    print("Submitted all tool outputs.") 
    async for data in submit_tool_outputs(client, tool_outputs, run_id, thread_id, query, image_bool, university, username, major, minor, year, school):
        yield data

@timing_decorator
async def submit_tool_outputs(client, tool_outputs, run_id, thread_id, query, image_bool, university, username, major, minor, year, school):
    print("Submitting tool outputs...")

    separation_added = False

    stream = await client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=tool_outputs,
        stream=True
    )
    async for event in stream:  # Use async for here to iterate over the stream
        if event.event == "thread.message.delta":
            for block in event.data.delta.content:
                if block.type == "text" and hasattr(block.text, "value"):
                    delta_text = block.text.value

                    if not separation_added:
                        yield "\n\n\n\n"  
                        separation_added = True

                    print(delta_text, end="", flush=True)
                    yield delta_text + "|"
                else:
                    print("No text content found in delta block:", block)
        elif event.event == 'thread.run.requires_action':
            print("Handling required action event during submit_tool_outputs...")
            async for data in handle_requires_action(client, event.data, run_id, query, image_bool, university, username, major, minor, year, school):
                yield data
        elif event.event == "thread.run.step.completed":
            print("Step completed")
        elif event.event == "thread.run.completed":
            print("Run completed")
        elif event.event == "thread.message.completed":
            print("Message completed")
            yield None  
        else:
            print("Unhandled event:", event)


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