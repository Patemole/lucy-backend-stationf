import praw
from datetime import datetime
import os
from dotenv import load_dotenv
import openai # Added for OpenAI integration
import json # Added for parsing JSON output
import logging # Added for logging
import asyncio # Added for async
from typing import AsyncGenerator # Added for type hint

# Basic logging configuration (can be overridden by importing application)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get logger for this module

# Load environment variables
load_dotenv()

# Async OpenAI Client Initialization
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Missing OpenAI API key in environment variables (OPENAI_API_KEY)")
async_client = openai.AsyncOpenAI(api_key=openai_api_key)

# Reddit API configuration (Reads credentials ONLY from environment variables)
reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
reddit_user_agent = os.getenv('REDDIT_USER_AGENT')

if not all([reddit_client_id, reddit_client_secret, reddit_user_agent]):
    raise ValueError("Missing Reddit API credentials in environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)")

reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)

def _format_comments(comments, depth=0, output_lines=None):
    """Helper function to recursively format comments and replies into a list of strings."""
    if output_lines is None:
        output_lines = []
    
    for comment in comments:
        indent = '    ' * depth
        created = datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
        author = comment.author.name if comment.author else '[deleted]'
        
        output_lines.append(f"{indent}- Comment by {author} | Score: {comment.score} | Created: {created}")
        # Handle potential None or empty body
        comment_body = comment.body if comment.body else "[No comment body]"
        # Indent each line of the comment body
        indented_body = '\n'.join([f"{indent}  {line}" for line in comment_body.strip().split('\n')])
        output_lines.append(f"{indented_body}\n")
        
        # Recursively format replies if they exist and are not MoreComments objects
        if hasattr(comment, 'replies') and comment.replies:
            # Ensure replies are loaded and not MoreComments before recursion
            comment.replies.replace_more(limit=0) # Load direct replies, avoid further MoreComments expansion here
            _format_comments(comment.replies, depth + 1, output_lines)
    return output_lines

def search_reddit_upenn(query: str, limit: int = 5, sort: str = 'relevance') -> str:
    """
    Searches the r/UPenn subreddit for a given query and returns a formatted string
    with the search results, including posts and their comments/replies.

    Args:
        query: The search term.
        limit: The maximum number of posts to return. Defaults to 5.
        sort: The sorting method for search results (e.g., 'relevance', 'hot', 'top', 'new'). Defaults to 'relevance'.

    Returns:
        A formatted string containing the search results, or an error message.
    """
    output_lines = []
    try:
        subreddit = reddit.subreddit('UPenn')
        output_lines.append(f"Searching r/UPenn for: '{query}' (Sort: {sort}, Limit: {limit})\n")

        results = subreddit.search(query, limit=limit, sort=sort)
        post_count = 0

        for post in results:
            post_count += 1
            post_created = datetime.utcfromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            post_author = post.author.name if post.author else '[deleted]'
            
            output_lines.append(f"\n{'='*80}")
            output_lines.append(f"Result {post_count}")
            output_lines.append(f"Title: {post.title}")
            output_lines.append(f"URL: https://www.reddit.com{post.permalink}")
            output_lines.append(f"Author: {post_author}")
            output_lines.append(f"Score: {post.score}")
            output_lines.append(f"Number of Comments: {post.num_comments}")
            output_lines.append(f"Created: {post_created}")
            # Handle potential None or empty selftext
            selftext = post.selftext if post.selftext else '[No Content]'
            output_lines.append(f"\nContent:\n{selftext}\n")

            # Load all comments including nested replies
            try:
                post.comments.replace_more(limit=None) # Load all replies recursively
                comments_list = post.comments.list()
                
                # Filter comments if there are more than 25
                if len(comments_list) > 25:
                    logger.info(f"Post '{post.title}' has {len(comments_list)} comments. Filtering top 25 by score.")
                    # Sort comments by score, descending. Handles potential None scores gracefully.
                    # We need to filter out MoreComments objects if any remain somehow
                    comments_list = [c for c in comments_list if hasattr(c, 'score')] 
                    comments_list.sort(key=lambda comment: comment.score if hasattr(comment, 'score') else -1, reverse=True)
                    comments_to_format = comments_list[:25]
                else:
                    # Use all comments if 25 or fewer
                    comments_to_format = comments_list

                output_lines.append("Answers/Comments (with replies):")
                if comments_to_format:
                    # Pass the potentially filtered list to the formatting function
                    _format_comments(comments_to_format, output_lines=output_lines) 
                    if len(comments_list) > 25:
                         output_lines.append("  [... Additional lower-scoring comments truncated ...]")
                else:
                    output_lines.append("  [No comments found for this post.]")
            except Exception as comment_error:
                 output_lines.append(f"  [Error loading or processing comments: {comment_error}]") # Added processing to error message
        
        if post_count == 0:
             output_lines.append("\nNo posts found matching the query.")

    except Exception as e:
        return f"Error during Reddit search: {e}"

    return '\n'.join(output_lines)

# Refactored function to perform search and yield summaries asynchronously
async def get_reddit_summary_for_query(query: str, search_limit: int = 3, sort_method: str = 'relevance') -> AsyncGenerator[str, None]:
    """
    Searches r/UPenn, summarizes results using GPT-4o, and yields structured data
    formatted as <REDDIT>JSON</REDDIT_END> strings asynchronously.

    Args:
        query: The search term.
        search_limit: Max Reddit posts to fetch. Defaults to 3.
        sort_method: Reddit search sort method. Defaults to 'relevance'.

    Yields:
        Strings in the format <REDDIT>JSON_OBJECT</REDDIT_END> where JSON_OBJECT
        contains 'comment', 'score', 'author', and 'link'.
    """
    
    logger.info(f"Performing Reddit search for query: '{query}'")
    reddit_search_output = "" # Initialize
    try:
        # Run the synchronous PRAW search in a separate thread
        reddit_search_output = await asyncio.to_thread(
            search_reddit_upenn, query, limit=search_limit, sort=sort_method
        )
        if reddit_search_output.startswith("Error"):
            logger.error(f"Reddit search failed: {reddit_search_output}")
            reddit_search_output = "" 
    except Exception as search_exc:
        logger.error(f"Exception during Reddit search thread: {search_exc}", exc_info=True)
        reddit_search_output = "" 

    logger.info(f"Reddit search output length: {len(reddit_search_output)} chars")

    # Define the JSON schema requesting the FULL details from OpenAI
    output_schema = {
        "type": "object",
        "properties": {
            "summaries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "The summarized comment or invented answer in a young, student tone. Do not include any other text or formatting."},
                        "author": {"type": "string", "description": "The Reddit username (or empty string for invented)."},
                        "score": {"type": "integer", "description": "The comment score (or 0)."},
                        "link": {"type": "string", "description": "The Reddit POST URL (or 'N/A')."}
                    },
                    "required": ["summary", "author", "score", "link"], 
                    "additionalProperties": False
                }
            }
        },
        "required": ["summaries"],
        "additionalProperties": False
    }
    
    # System prompt requesting the FULL details
    system_prompt = f"""
You are an expert summarizer tasked with extracting key insights from Reddit search results for the query: '{query}'.
The input is formatted text from r/UPenn posts and comments.

Input Format Explanation:
- Posts start with '====================' and 'Result X'.
- Post details include Title, URL, Author, Score, etc.
- Comments are indented under 'Answers/Comments (with replies):'.
- Comment headers show author, score, and date.

Your Task:
1. **Analyze Input**: Review the provided Reddit search output.
2. **Identify Relevance**: Find the most relevant and highly-upvoted comments related to the query: '{query}'.
3. **Summarize**: Summarize the core message of 1-3 key comments concisely, using a very young, relatable, informal student tone.
4. **Handle Empty/Irrelevant Input**: IF the provided 'reddit_search_output' is empty, contains no useful comments, shows 'No posts found', or is generally irrelevant to the original query '{query}', THEN invent ONE single, plausible **student testimony or comment** related to the topic of '{query}'. This invented comment should **not** sound like a direct answer, but more like a student sharing their own experience, anecdote, or something they heard from friends (e.g., 'My friend actually tried that...', 'Honestly my experience with [topic] was more like...'). Use the young, relatable student tone. In this invented case, create a plausible **first name** for the author (e.g., "Alex", "Chloe"), invent a plausible **score** (e.g., a small positive integer like 3, 5, or 8), and use "N/A" for the link.
5. **Extract Details (If Relevant Input)**: For summaries based on actual comments, extract the original comment's author, score, and the URL of the POST it belongs to.
6. **Format Output**: Output ONLY a JSON object conforming precisely to the provided schema. The main key must be "summaries", containing a list of objects. Each object MUST have keys: "summary", "author", "score", and "link".

Example of a SINGLE item in the expected OpenAI output summaries list (based on real data):
{{
  "summary": "Basically everyone says Huntsman is packed, try Fisher Fine Arts instead lol",
  "author": "student_redditor_1",
  "score": 18,
  "link": "https://www.reddit.com/r/UPenn/comments/qxxxxx/favorite_underrated_study_spots/"
}}

Example of a SINGLE item (invented student comment for empty input, related to query 'best study spot'):
{{
  "summary": "Idk about *best*, but my roommate basically lived in VP last semester and didn't completely lose it, so maybe it's okay? lol", # More anecdotal, less direct answer
  "author": "Maria", # Invented first name
  "score": 4,       # Invented plausible score between 1 and 10
  "link": "N/A"
}}

Ensure the output is a single, valid JSON object with the specified structure. Aim for brevity, 1-3 summaries max.
"""

    logger.info("Calling OpenAI asynchronously for summarization...")
    try:
        # Use await with the async client
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reddit_search_output} 
            ],
            temperature=0.7,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "reddit_summaries",
                    "strict": True,
                    "schema": output_schema
                }
            }
        )
        
        summary_json_string = response.choices[0].message.content
        summary_data = json.loads(summary_json_string)
        
        if isinstance(summary_data, dict) and "summaries" in summary_data and isinstance(summary_data["summaries"], list):
            validated_full_summaries = []
            for item in summary_data["summaries"]:
                if isinstance(item, dict) and all(key in item for key in ["summary", "author", "score", "link"]):
                     validated_full_summaries.append(item)
                else:
                    logger.warning(f"Skipping invalid item from OpenAI (missing required keys): {item}")
            
            logger.info(f"OpenAI processing successful, yielding {len(validated_full_summaries)} summaries.")
            # Yield each summary in the desired format
            for full_summary in validated_full_summaries:
                

                output_dict_nested = {
                    "reddit": {  # <-- Ajout de la clé "reddit" ici
                        "comment": full_summary["summary"],
                        "score": full_summary["score"],
                        "author": full_summary["author"],
                        "link": full_summary["link"]
                    }
                }
                # Format the string to be yielded
                # Le JSON contiendra maintenant {"reddit": {"comment": ...}}
                yield_string = f"\n<REDDIT>{json.dumps(output_dict_nested)}<REDDIT_END>\n"
                logger.info(f"Yielding Reddit summary (alternative): {yield_string.strip()}")
                yield yield_string
                
                '''
                # Create the final dictionary with the desired keys
                output_dict = {
                    "comment": full_summary["summary"], # Map summary to comment
                    "score": full_summary["score"],
                    "author": full_summary["author"],
                    "link": full_summary["link"]
                }
                # Format the string to be yielded
                yield_string = f"\n<REDDIT>{json.dumps(output_dict)}<REDDIT_END>\n"
                # Ajout du log avant le yield
                logger.info(f"Yielding Reddit summary: {yield_string.strip()}") # Log the string being yielded
                # Yield the formatted string
                yield yield_string
                '''
                await asyncio.sleep(0.05) # Small sleep to allow other tasks if needed
        else:
             logger.error(f"Unexpected JSON structure received from OpenAI: {summary_data}")
             # Stop yielding

    except json.JSONDecodeError as json_err:
        logger.error(f"Error decoding JSON response from OpenAI: {json_err}")
        logger.error(f"Received raw JSON: {summary_json_string}")
        # Stop yielding
    except Exception as e:
        logger.error(f"Error during OpenAI processing: {e}", exc_info=True)
        # Stop yielding
    