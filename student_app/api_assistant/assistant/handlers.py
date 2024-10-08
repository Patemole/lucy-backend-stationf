# handler.py

import json
import openai
from openai import AssistantEventHandler
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info
from .tools.clarification_tool.clarification_manager import get_clarifying_question_output


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

                text_search = [
                    {
                        "Sentence1": "_**[LUCY is processing the search…]**_",
                        "Sentence2": "Navigating through 6 different sources...",
                        "Sentence3": "One last effort..."
                    }
                ]

                self.response_queue.put(json.dumps({"answer_waiting": text_search}))

                output = get_up_to_date_info(query, self.university)
                print(f"Current info for query '{query}': {output}")  # Debug statement
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            elif function_name == "ask_clarifying_question":
                print(f"Processing clarifying question with arguments: {arguments}")
                # Generate the tool output using the helper function
                tool_output = get_clarifying_question_output(arguments)
                print(tool_output)
                # Put the output into the response queue
                self.response_queue.put(json.dumps({"answer_TAK_data": tool_output}))  # Directly return the output
                # Append the tool output to keep the run active
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(tool_output)  # Ensure it's a string
                })
                
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

        separation_added = False


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

                            if not separation_added:
                                self.response_queue.put("\n\n\n\n")  # Add two line breaks
                                separation_added = True

                            
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