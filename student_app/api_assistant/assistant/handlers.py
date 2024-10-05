# handler.py

import json
import openai
from openai import AssistantEventHandler
from .tools.filter_tool.filter_manager import apply_filters
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info
from .tools.prerequisites_tool.prerequisites_manager import get_prerequisites

class CustomAssistantEventHandler(AssistantEventHandler):
    def __init__(self, thread_id, df, response_queue, client, university):
        super().__init__()
        self.thread_id = thread_id
        self.df = df
        self.response_queue = response_queue
        self.filtered_data = None
        self.tool_calls = []
        self.run = None  # Will be set after the stream starts
        self.client = client
        self.university=university

    def on_event(self, event):
        if event.event == 'thread.run.requires_action':
            print("Handling required action event...")
            run_id = event.data.id
            self.handle_requires_action(event.data, run_id)
        elif event.event == 'thread.message.delta':
            delta_text = event.data.delta.content[0].text.value
            print(delta_text, end="", flush=True)
            # Push delta text to the response queue so the generator can yield it
            self.response_queue.put(delta_text + "|")
        elif event.event == 'thread.run.completed':
            print("\nRun completed.")
            # Signal that the run is completed by pushing `None` to the queue
            self.response_queue.put(None)


    def handle_requires_action(self, data, run_id):
        print("Run requires action: Processing tool calls...")  # Debug statement
        # Process all collected tool calls
        tool_outputs = []
        for tool_call in data.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            print(f"Processing tool: {function_name}") 

            try:
                # Extract the arguments for the function call
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                print(f"Failed to parse arguments for {function_name}")
                arguments = {}
            """
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
            """

            if function_name == "get_current_info":
                # Process get_current_info
                query = arguments.get('query', '')
                output = get_up_to_date_info(query, self.university)
                print(f"Current info for query '{query}': {output}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            elif function_name == "ask_clarifying_question":
                print(f"Processing clarifying question for query '{arguments.get('query', '')}'")
                #TODO make sure we get the JSON from the function call
                tool_output = get_clarifying_question_output(query)  # Replace this with the actual output retrieval logic
                self.response_queue.put(json.dumps({"answer_TAK_data": tool_output}))  # Directly return the output
                return

            
            else:
                # Function not implemented
                output = "Function not implemented."
                print(f"Function not implemented: {function_name}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            """
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
            """

        # Submit all tool outputs at once
        self.submit_tool_outputs(tool_outputs, run_id)
        print("Submitted all tool outputs.")  # Debug statement

        #self.tool_calls = []

        # **Restart the stream to continue receiving assistant's response**
        #self.run = run  # Update the run instance if necessary
        #self.run.stream_response()

    def submit_tool_outputs(self, tool_outputs, run_id):
        print("Submitting tool outputs...")

        # Create a new instance of the event handler
        new_event_handler = CustomAssistantEventHandler(
            thread_id=self.thread_id,
            df=self.df,
            response_queue=self.response_queue,
            client=self.client,  # Pass in the client object
            university=self.university
        )

        # Use stream=True to get streaming events
        with self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            stream=True  # Ensure streaming is enabled
        ) as stream:
            for event in stream:
                # Check the event type and handle accordingly
                if event.event == "thread.message.delta":
                    # Process delta content
                    for block in event.data.delta.content:
                        if block.type == "text" and hasattr(block.text, "value"):
                            delta_text = block.text.value
                            
                            # Before sending the first piece of tool output, add new lines to separate it.
                            if self.tool_calls:  # Ensure this isn't the first time (i.e., it's a tool follow-up).
                                self.response_queue.put("\n\n\n")  # Add line breaks before tool output.

                            print(delta_text, end="", flush=True)
                            # Push delta text to the response queue
                            self.response_queue.put(delta_text + "|")
                        else:
                            print("No text content found in delta block:", block)
                elif event.event == "thread.run.step.completed":
                    print("Step completed")
                elif event.event == "thread.run.completed":
                    print("Run completed")
                elif event.event == "thread.message.completed":
                    print("Message completed")
                    # Optionally, signal to the frontend that the message is done
                    self.response_queue.put(None)  # Indicating no more content
                else:
                    # Handle other types of events (e.g., step created, in progress)
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