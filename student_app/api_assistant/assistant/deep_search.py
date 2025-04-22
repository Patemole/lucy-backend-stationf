# student_app/api_assistant/assistant/deep_search.py

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, AsyncGenerator
import openai # Use the main openai library
from openai import AsyncOpenAI # Specifically import AsyncOpenAI

# Assuming these functions are correctly located and importable
# Adjust paths if necessary
from .tools.perplexity_tool.perplexity_manager import get_up_to_date_info
from .tools.RAG_tool.zeroentropy import search_top_pages

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Tool Schema Definition ---

GET_CURRENT_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_info",
        "description": "Retrieves up-to-date information based on a specific query about the university. Use this iteratively to gather facts needed to answer a complex question.",
        "strict": True, # Assuming strict mode is desired
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A precise, targeted question to fetch specific information (e.g., 'UPenn Computer Science major requirements', 'UPenn course description for CIS 121', 'UPenn academic calendar fall 2025'). Break down complex user requests into multiple, sequential queries for this tool."
                },
                # Removed number_of_sources, youtube_bool, reddit_bool, reasoning_steps
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}

# --- Tool Execution Logic ---

async def execute_tool(name: str, arguments: Dict[str, Any], university: str) -> str:
    """
    Route tool name to the corresponding coroutine and return its result as a JSON string.
    Handles only 'get_current_info' for this agent.
    """
    if name == "get_current_info":
        query = arguments.get("query", "")
        if not query:
            logger.warning("Query parameter missing for get_current_info tool call.")
            return json.dumps({"error": "Query parameter missing for get_current_info"})

        logger.info(f"Executing get_current_info tool with query: {query}")
        try:
            # Assuming these functions take query and university
            # Using default nb_sources=5, adjust if needed or make it configurable
            # Passing empty dicts for user profile info as placeholders, adjust if needed
            info_task = get_up_to_date_info(query, university, username="", major="", minor="", year="", school="", input_message="", nb_sources=5)
            rag_task = search_top_pages(query, university)

            info_results, rag_results = await asyncio.gather(info_task, rag_task)

            # Format results consistently - simple example
            # Truncate content to avoid overly long tool results
            info_str = "; ".join([f"{res.get('title', 'Source')}: {res.get('content', '')[:300]}..." for res in info_results])
            rag_str = " ".join([chunk["text"][:300]+"..." for chunk in rag_results.get("retrieved_chunks", [])]) if rag_results.get("status") == "success" else ""

            combined_content = f"Web Info: [{info_str}] --- RAG DB: [{rag_str}]"
            if not combined_content.strip() or combined_content == "Web Info: [] --- RAG DB: []":
                 combined_content = "No specific information found for that query."

            logger.info("Tool execution finished.")
            # Return a JSON string as expected by the API
            return json.dumps({"retrieved_information": combined_content})
        except Exception as e:
            logger.exception(f"Error executing get_current_info tool: {e}")
            return json.dumps({"error": f"Failed to execute get_current_info: {str(e)}"})

    logger.warning("Tool %s not implemented in deep_search agent", name)
    return json.dumps({"error": f"Tool {name} is not available in this context"})

# --- Main Agent Logic ---

async def run_deep_search_agent(
    client: AsyncOpenAI, # Explicitly type hint the client
    university: str,
    username: str,
    major: str,
    minor: str,
    year: str,
    school: str,
    history_items: List[Dict[str, str]],
    input_message: str,
) -> AsyncGenerator[str, None]: # Use AsyncGenerator for yield
    """
    Runs the deep search agent, iteratively calling get_current_info.
    Yields streamed response chunks (ending with '|').
    """

    logger.info("➡️ Starting deep search agent for message: %s", input_message)

    # 1. Build initial prompt and messages
    system_prompt = f"""
You are a specialized academic research assistant for {university}.
Your primary goal is to answer complex student questions accurately by breaking them down and gathering information step-by-step.
You have access to one tool: `get_current_info`.

User Profile:
- Name: {username}
- School: {school}
- Year: {year}
- Major(s): {major}
- Minor(s): {minor}

Instructions:
1.  Analyze the student's request ({input_message}).
2.  If the request is complex (e.g., requires knowing requirements AND course details), identify the *first* specific piece of information needed.
3.  Call the `get_current_info` tool with a *specific* query to retrieve that first piece of information. Use the student's profile (major, year, school) to make your query relevant if possible.
4.  Review the tool's response. If more information is needed to fully answer the original request, identify the *next* specific piece required.
5.  Call `get_current_info` again with a new specific query based on the previous results and the overall goal.
6.  Repeat steps 4-5 until you have gathered ALL necessary information.
7.  Once all information is gathered, synthesize it into a final, comprehensive answer for the student. Clearly state the answer based *only* on the information gathered.
8.  Do NOT answer until you have used the tool to gather all necessary facts. If the tool returns an error or insufficient info after trying, state that you couldn't find the specific details needed.
Focus solely on information gathering and synthesis using the tool. Do not engage in chit-chat.
"""

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]

    # Append history (ensure roles are 'user' or 'assistant')
    for item in history_items:
        role = "assistant" if item.get("username", "").lower() == "lucy" else "user"
        # Ensure content is string
        content = item.get("body", "")
        if not isinstance(content, str):
            content = json.dumps(content) # Serialize if not string
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": input_message})

    # 2. Continuous agent loop
    iteration_count = 0
    max_iterations = 6 # Safety break for iterations

    while iteration_count < max_iterations:
        iteration_count += 1
        logger.info(f"Deep search iteration {iteration_count}")

        try:
            stream = await client.chat.completions.create(
                model="o3", # Using gpt-4o
                reasoning={"effort": "low"},
                messages=messages,
                tools=[GET_CURRENT_INFO_TOOL], # Only provide this tool
                tool_choice="auto",
                stream=True,
            )

            # Buffers for the current turn
            assistant_msg_content = ""
            current_tool_calls: List[Dict[str, Any]] = [] # Store complete tool calls for this turn

            # Process stream chunks
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta: continue

                # Stream partial text content
                if delta.content:
                    assistant_msg_content += delta.content
                    yield delta.content + "|" # Add separator for streaming

                # Accumulate tool call details
                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        idx = tc_chunk.index
                        # Ensure list is long enough and initialize entry if needed
                        while len(current_tool_calls) <= idx:
                             current_tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})

                        # Update attributes from chunk
                        if tc_chunk.id:
                            current_tool_calls[idx]["id"] = tc_chunk.id
                        if tc_chunk.function:
                            if tc_chunk.function.name:
                                current_tool_calls[idx]["function"]["name"] = tc_chunk.function.name
                            if tc_chunk.function.arguments:
                                current_tool_calls[idx]["function"]["arguments"] += tc_chunk.function.arguments

            # --- Turn processing finished ---

            # Append the complete assistant message (content + tool calls) to history
            if assistant_msg_content or current_tool_calls:
                 # Filter out potentially incomplete tool calls (where ID or name might be missing)
                 valid_tool_calls = [tc for tc in current_tool_calls if tc.get("id") and tc.get("function", {}).get("name")]
                 
                 full_assistant_msg = {"role": "assistant", "content": assistant_msg_content or None} # Use None if no content
                 if valid_tool_calls:
                     full_assistant_msg["tool_calls"] = valid_tool_calls
                 
                 messages.append(full_assistant_msg)
                 logger.info(f"Appended assistant message to history (Content: {bool(assistant_msg_content)}, Tools: {len(valid_tool_calls)})")

            # If no *valid* tool calls were made, the agent is finished or errored
            if not valid_tool_calls:
                logger.info("Deep search finished: No valid tool calls requested by assistant in this turn.")
                break # Exit the while loop

            # 3. Execute requested tool calls concurrently
            async def _run_tool_call(tool_call):
                tool_name = tool_call["function"]["name"]
                tool_id = tool_call["id"]
                logger.info(f"Preparing tool call {tool_id}: {tool_name}")
                try:
                    # Arguments should be fully formed now
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode arguments for tool {tool_id} ({tool_name}): {tool_call['function']['arguments']} - Error: {e}")
                    return { "role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": json.dumps({"error": f"Invalid arguments JSON provided: {e}"}) }

                # Execute the tool
                tool_result_content = await execute_tool(tool_name, arguments, university)
                return { "role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": tool_result_content } # Content is already JSON string

            # Run all tool calls concurrently
            tool_results = await asyncio.gather(*[_run_tool_call(tc) for tc in valid_tool_calls])
            messages.extend(tool_results)
            logger.info(f"Appended {len(tool_results)} tool results to history.")
            # Loop continues, assistant sees tool results

        except Exception as e:
            logger.exception(f"🚨 An error occurred during deep search iteration {iteration_count}: {e}")
            yield f"\n<ERROR>{json.dumps({'error_message': f'An error occurred during the search: {str(e)}'})}<ERROR_END>\n" # Yield structured error
            break # Exit loop on error

    if iteration_count >= max_iterations:
         logger.warning("Deep search reached max iterations (%d), exiting loop.", max_iterations)
         # Maybe yield a message indicating this?
         yield "\n<INFO>The search took longer than expected. I'll provide the best answer based on the information gathered so far.</INFO>\n"
         # Consider one final call without tools to force synthesis? Or just end here.

    # Send final separator if needed and not already sent by last text chunk
    # yield "|"
    logger.info("🏁 Deep search agent finished.")
