# backend/assistant/handlers.py

import json
from backend.assistant.tools.filter_tool.filters import apply_filters
from backend.assistant.tools.filter_tool.data_loader import load_course_data
from backend.assistant.tools.search_tool.search import search_courses
# Import additional tools as you add them
# from backend.assistant.tools.another_tool.another_tool import another_function

def handle_requires_action(run, thread_id, assistant_id, df):
    """
    Handles the 'requires_action' status by processing tool calls and submitting outputs.

    Parameters:
    - run: The current run instance.
    - thread_id (str): The ID of the thread.
    - assistant_id (str): The ID of the assistant.
    - df (pd.DataFrame): The course data DataFrame.

    Returns:
    - run: The updated run instance after submitting tool outputs.
    """
    print("Handling requires_action status...")
    tool_outputs = []

    # Loop through each tool in the required action section
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        print(f"Processing tool call: {tool.function.name}")
        if tool.function.name == "get_filters":
            try:
                arguments = json.loads(tool.function.arguments)
                print("Function call arguments received:")
                print(json.dumps(arguments, indent=2))
            except json.JSONDecodeError:
                print("Failed to parse function call arguments.")
                continue

            # Apply the filters to df_expanded
            df_filtered_json = apply_filters(arguments, df)

            # Prepare the output for the assistant
            if not df_filtered_json:
                output = "No courses match your query."
            else:
                output = df_filtered_json  # Directly return JSON

            # Append the tool output
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": output
            })
        
        elif tool.function.name == "search_courses":
            try:
                arguments = json.loads(tool.function.arguments)
                keywords = arguments.get('keywords', [])
                print("Function call arguments received:")
                print(json.dumps(arguments, indent=2))
            except json.JSONDecodeError:
                print("Failed to parse function call arguments.")
                continue

            # Apply the search
            search_result_json = search_courses(keywords, df)

            # Prepare the output for the assistant
            if not search_result_json:
                output = "No courses match your search criteria."
            else:
                output = search_result_json  # Directly return JSON

            # Append the tool output
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": output
            })

        # Add more elif blocks for additional tools
        # elif tool.function.name == "another_function":
        #     ...

    # Submit all tool_outputs at once after collecting them in a list
    if tool_outputs:
        print("Submitting tool outputs...")
        try:
            run = openai.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.\n")
        except Exception as e:
            print("Failed to submit tool outputs:", e, "\n")
    else:
        print("No tool outputs to submit.\n")

    return run
