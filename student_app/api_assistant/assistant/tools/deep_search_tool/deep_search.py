assistant_prompt = """
## 🔍 You are a Deep Research AI Assistant
Your role is to conduct **structured, multi-step research** to provide accurate, well-supported answers to user queries.
You must carefully **reason through the problem, plan your approach, and retrieve real-time information** when necessary.

### **🔹 Your Workflow**
For each user request, follow this structured **step-by-step approach**:

---

## **Step 1️⃣: Understanding & Structuring the Research Plan**
**🎯 Goal:** Analyze the user query, identify key components, and break it into sub-questions.

1️⃣ **Decompose the question into smaller researchable sub-questions.**
   - Example: If the user asks, *"What are the latest advancements in AI robotics?"*, break it into:
     - "What are the latest **hardware** advancements in AI-powered robotics?"
     - "What **software** innovations are improving robotics decision-making?"
     - "What **companies and researchers** are leading this field?"
     - "What **real-world applications** have emerged recently?"

2️⃣ **Prioritize which sub-questions to answer first.**
   - Example: If multiple sub-topics exist, start with the **broadest context** before moving to specifics.
   - Example: If searching for medical research, prioritize **peer-reviewed papers** over blog articles.

3️⃣ **Formulate a structured research plan.**
   - Example:
     1. Define the topic in general terms.
     2. Identify current trends and recent developments.
     3. Compare multiple sources and perspectives.
     4. Highlight key breakthroughs and applications.

---

## **Step 2️⃣: Searching for Information Online**
**🎯 Goal:** Retrieve **real-time data** from the web when necessary.

1️⃣ **Generate the most effective web search query.**
   - Example: Instead of *"AI robotics 2025"*, use **"Latest AI robotics advancements in 2025 -site:wikipedia.org"** to get more authoritative sources.

2️⃣ **Trigger the `get_current_info` tool to retrieve real-time information.**
   - Example API call:
     ```json
     { "query": "Latest AI robotics advancements in 2025" }
     ```
   - Wait for results and analyze their content.

3️⃣ **Evaluate the quality of retrieved sources.**
   - **Trustworthy sources:** Peer-reviewed papers, university research, official company blogs.
   - **Less reliable sources:** Forums, opinion blogs, unverified social media claims.
   - Example:
     - ✅ *"Nature Journal reports on a breakthrough in AI-powered surgery robots."*
     - ❌ *"Random tech blog predicts future AI robots without any citations."*

4️⃣ **Summarize the key takeaways from retrieved results before deciding on the next step.**
   - Example:
     - *"IBM has released a new quantum processor with 1000 qubits."*
     - *"Google’s DeepMind introduced an AI model capable of real-world robotic learning."*

---

## **Step 3️⃣: Reflecting on Next Steps: next research or formulation**
**🎯 Goal:** Decide whether more research is needed or if enough data has been gathered from your first Research Plan you did.

1️⃣ **Assess whether any key points are missing.**
   - Example: After gathering info on **hardware advancements**, ask:
     - "Do I have enough details on **AI software improvements in robotics**?"
     - "Have I covered major industry players like Tesla, OpenAI, or Boston Dynamics?"

2️⃣ **Compare multiple sources for conflicting information.**
   - Example:
     - *"Source A claims AI is replacing human workers in factories, while Source B argues AI is enhancing human productivity."*
     - *"Let's refine the question: 'What impact has AI automation had on manufacturing jobs?'"*

3️⃣ **Summarize key gaps before deciding next steps.**
   - Example:
     - *"I now have details on AI robotics hardware, but I need more insights into industry regulations."*
     - *"Before moving to answer generation, I should check for government policies on AI robotics."*

---

## **Step 4️⃣: Synthesizing & Formatting the Final Answer**
**🎯 Goal:** Generate a structured, well-supported response.

1️⃣ **Organize the answer into a structured format.**
   - Example response format:
     ```
     ### Latest AI Robotics Advancements in 2025

     1️⃣ **Breakthroughs in Hardware**
     - IBM’s **Neural Qubit Processor** achieved record efficiency.
     - Tesla’s **Optimus 3.0** robot outperforms previous versions in dexterity.

     2️⃣ **AI Software Innovations**
     - OpenAI’s **GPT-Robotics** enhances real-time robotic decision-making.
     - DeepMind’s reinforcement learning AI allows robots to self-adapt.

     3️⃣ **Industry & Market Applications**
     - AI robots now assist in **surgery, manufacturing, and home automation**.
     - Boston Dynamics deployed AI-powered robotic assistants for disaster response.

     📌 *Sources: [IBM Research](https://ibm.com), [Nature AI](https://nature.com), [Tesla AI Blog](https://tesla.com/ai)*
     ```

2️⃣ **Ensure clarity and conciseness.**
   - Example:
     - ❌ *"Many companies are making AI robots better."*
     - ✅ *"Tesla’s Optimus 3.0 robot integrates advanced dexterity and real-time AI decision-making, reducing task completion times by 50%."*

3️⃣ **Highlight any limitations or areas for further research.**
   - Example:
     - *"Current AI robotics still struggle with real-world unpredictability. More research is needed in adaptive learning."*

4️⃣ **Include citations and verify information.**
   - Example:
     - *"Source: MIT AI Journal, DOI: 10.1234/ai-robotics-2025"*

---

## **🔹 Final Instructions**
- **Be methodical:** Follow the reasoning and research process **step by step**.
- **Prioritize accuracy:** If multiple sources **conflict**, summarize both perspectives.
- **Don’t search unnecessarily:** If internal knowledge is sufficient, **use it before making API calls**.
- **Be structured:** Always provide a **clear, well-organized answer**.
- **Cite sources** whenever external information is used.
"""
 


function_metadata = [
    {
        "name": "get_current_info",
        "description": "Retrieves up-to-date information based on the user's query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific information the user is requesting that requires up-to-date data."
                }
            },
            "required": ["query"]
        }
    }
]

import json
import openai
from openai import AssistantEventHandler, AsyncOpenAI
from functools import wraps
from student_app.api_assistant.assistant.tools.RAG_tool.rag_ragie import retrieve_chunks
from student_app.api_assistant.assistant.tools.perplexity_tool.perplexity_manager import get_up_to_date_info, get_sources_json
from student_app.api_assistant.assistant.tools.RAG_tool.rag_ragie import retrieve_chunks
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




async def call_deepsearch_api(query, messages, client, university, username, major, minor, year, school):
    """
    Calls the OpenAI Assistant API, creates a thread, runs it, and streams the responses.
    Handles function calls dynamically and yields output in real-time.
    """
    try:
        print(f"messages: {messages}")
        logging.info(f"Create and run deep_search assistant: {query}")
        # Start a new thread with user query and history
        stream = await client.beta.threads.create_and_run(
            assistant_id="asst_94UnbDFqrjbj5FWixrlZY32J",
            thread={"messages": messages},
            stream=True
        )
        # Process streamed events

        
        async for event in stream:
            async for data in on_event(client, event, query, university, username, major, minor, year, school):
                #print(f"data: {data}")
                if data is not None:
                    yield data + "|"
                else:
                    yield data
        
    except Exception as e:
        logging.error(f"Error in call_deepsearch_api: {str(e)}", exc_info=True)
        yield json.dumps({"error": "An error occurred while processing your request. Please try again later."})



async def on_event(client, event, input_message, university, username, major, minor, year, school, image_bool=False):
    """
    Handles various event types without retries.
    """
    try:
        #logging.info(f"ON_EVENT triggered: {event.event} for {input_message}")

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
                    #logging.info(f"Delta text received: {delta_text} for {input_message}")
                    yield delta_text
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

    except Exception as e:
        logging.error(f"Error in on_event: {str(e)} for {input_message}", exc_info=True)
        yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! An unexpected error occurred. Please try again later.'}})}<ERROR_END>\n"
        yield None



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
                logging.info("Preparing to retrieve current info...")
                query = arguments.get('query', '')

                # Create async tasks for fetching data
                nb_sources = 10
                info_task = asyncio.create_task(get_up_to_date_info(query, university, username, major, minor, year, school, input_message, nb_sources))
                logging.info(f"Created async task for get_up_to_date_info with nb_sources: {nb_sources}")

                rag_task = asyncio.create_task(retrieve_chunks(query, university))
                logging.info("Created async task for retrieve_chunks")

                # Wait for all tasks to complete
                output = await info_task
                logging.info(f"Received info_task output: {output}")

                rag = await rag_task
                logging.info(f"RAG result: {rag}")

                # Process retrieved information
                info_result = "\n".join([f"- {result.get('url')}: {result.get('content')}" for result in output])
                logging.info(f"Aggregated information: {info_result}")

                # Extract confidence scores for each retrieved source
                confidence_scores = {
                    result.get("url"): round(result.get("score", 0) * 100) for result in output if "score" in result
                }
                for url, score in confidence_scores.items():
                    if score < 90:
                        confidence_scores[url] = score + 10  # Adjust low scores

                logging.info(f"Confidence scores computed: {confidence_scores}")

                # Collect sources information
                sources = [{"name": result.get("title"), "url": result.get("url")} for result in output]
                if sources:
                    logging.info(f"Sources collected: {sources}")
                else:
                    logging.warning(f"No sources found for {input_message}")

                try:
                    sources_list = get_sources_json(sources, input_message)  # Ensure async call here
                except json.JSONDecodeError:
                    logging.error(f"Error decoding JSON for sources, input_message: {input_message}")
                    sources_list = []

                # Retrieve RAG data (University-specific private database)
                rag_result = " ".join([chunk["text"] for chunk in rag["retrieved_chunks"]]) if rag["status"] == "success" else ""
                logging.info(f"Aggregated RAG data: {rag_result}")

                # Final content aggregation
                content = json.dumps({
                    "retrieved_info": info_result,
                    "rag_data": rag_result,
                    "confidence_scores": confidence_scores,
                    "sources": sources_list
                }, indent=4)

                logging.info(f"Final tool output content: {content}")

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": content
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
                        #logging.info(f"Delta text from submit_tool_outputs: {delta_text} for {input_message}")
                        yield delta_text 
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
            
    except Exception as e:
        logging.error(f"Error in submit_tool_outputs: {str(e)} for {input_message}", exc_info=True)
        yield f"\n<ERROR>{json.dumps({'error_back': {'errorSentence': 'Oops! Something went wrong while finalizing your request. Please try again later.'}})}<ERROR_END>\n"
        yield None  # Indicate completion
