# backend/assistant/handlers.py

import json
import openai
from .tools.filter_tool.filter_manager import apply_filters
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info
from .tools.prerequisites_tool.prerequisites_manager import get_prerequisites


def handle_requires_action(run, thread_id, assistant_id, df):
    tool_outputs = []
    filtered_data = None  # Initialize filtered_data
    current_info = None   # Initialize current_info
    prerequisites_info = None  # Initialize prerequisites_info

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
                current_info = get_up_to_date_info(query)

                # The output is the information retrieved
                output = current_info

            elif tool.function.name == "get_prerequisites":
                course_code = arguments.get('course_code', '').strip().upper()

                # Search the DataFrame for the course code
                prerequisites = get_prerequisites(course_code, df)

                if prerequisites is not None:
                    output = f"The prerequisites for {course_code} are: {prerequisites}"
                else:
                    output = f"No prerequisites found for {course_code}."
            else:
                # Handle other functions if any
                output = "Function not implemented."

            # Append the tool output
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": output
            })

    if tool_outputs:
        try:
            run = openai.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        except Exception as e:
            pass

    # Return the updated run, filtered data, and current info
    return run, filtered_data
