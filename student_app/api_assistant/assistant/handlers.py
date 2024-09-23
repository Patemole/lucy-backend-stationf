# backend/assistant/handlers.py

import json
import openai
from assistant.tools.filter_tool.filter_manager import apply_filters

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
                # Or simply set output to a confirmation message
                # output = "Filtered data generated."

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

    # Return both the updated run and the filtered data
    return run, filtered_data
