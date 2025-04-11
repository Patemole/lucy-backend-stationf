import praw
from datetime import datetime
import os
from dotenv import load_dotenv
import openai # Added for OpenAI integration
import json # Added for parsing JSON output
import logging # Added for logging

# Basic logging configuration (can be overridden by importing application)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get logger for this module

# Load environment variables
load_dotenv()

# OpenAI Client Initialization
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Missing OpenAI API key in environment variables (OPENAI_API_KEY)")
client = openai.OpenAI(api_key=openai_api_key)

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
                comments = post.comments.list()
                output_lines.append("Answers/Comments (with replies):")
                if comments:
                    _format_comments(comments, output_lines=output_lines) # Pass list to append to
                else:
                    output_lines.append("  [No comments found for this post.]")
            except Exception as comment_error:
                output_lines.append(f"  [Error loading comments: {comment_error}]")
        
        if post_count == 0:
             output_lines.append("\nNo posts found matching the query.")

    except Exception as e:
        return f"Error during Reddit search: {e}"

    return '\n'.join(output_lines)

# Refactored function to perform search and summarization
def get_reddit_summary_for_query(query: str, search_limit: int = 3, sort_method: str = 'relevance') -> list[dict]:
    """
    Searches r/UPenn for a query, then summarizes the results using GPT-4o,
    returning structured data. Handles empty/irrelevant search results.

    Args:
        query: The search term.
        search_limit: Max number of posts to fetch from Reddit. Defaults to 3.
        sort_method: Reddit search sort method. Defaults to 'relevance'.

    Returns:
        A list of dictionaries, each containing at least a 'summary'.
        Returns an empty list if the process fails.
    """
    
    # Step 1: Perform the Reddit search internally
    logger.info(f"Performing Reddit search for query: '{query}'")
    reddit_search_output = search_reddit_upenn(query, limit=search_limit, sort=sort_method)
    if reddit_search_output.startswith("Error"):
        logger.error(f"Reddit search failed: {reddit_search_output}")
        reddit_search_output = "" # Pass empty string to potentially trigger invention

    logger.info(f"Reddit search output length: {len(reddit_search_output)} chars")
    # Optional: Log snippet of reddit_search_output for debugging
    # print(f"Reddit search snippet: {reddit_search_output[:500]}...")

    # Step 2: Summarize the results using OpenAI
    
    # Define the desired JSON schema for the output
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
4. **Handle Empty/Irrelevant Input**: IF the provided 'reddit_search_output' is empty, contains no useful comments, shows 'No posts found', or is generally irrelevant to the original query '{query}', THEN invent ONE single, concise, plausible answer to the query '{query}', still using the young student tone. In this invented case, use an empty string "" for author, 0 for score, and "N/A" for the link.
5. **Extract Details (If Relevant Input)**: For summaries based on actual comments, extract the original comment's author, score, and the URL of the POST it belongs to.
6. **Format Output**: Output ONLY a JSON object conforming precisely to the provided schema. The main key must be "summaries", containing a list of objects. Each object MUST have at least a "summary" key. Include "author", "score", and "link" if available from the source comment, otherwise use the placeholders defined in step 4 for invented answers.

Example of a SINGLE item (from real comment):
{{
  "summary": "Basically everyone says Huntsman is packed, try Fisher Fine Arts instead lol",
  "author": "student_redditor_1",
  "score": 18,
  "link": "https://www.reddit.com/r/UPenn/comments/qxxxxx/favorite_underrated_study_spots/"
}}

Example of a SINGLE item (invented answer for empty input):
{{
  "summary": "Honestly just hit up Van Pelt, it's basic but gets the job done most times.",
  "author": "",
  "score": 0,
  "link": "N/A"
}}

Ensure the output is a single, valid JSON object with the specified structure. Aim for brevity, 1-3 summaries max.
"""

    logger.info("Calling OpenAI for summarization...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                # Pass the potentially empty search output here
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
        
        # Validate the parsed data - check for summaries list
        if isinstance(summary_data, dict) and "summaries" in summary_data and isinstance(summary_data["summaries"], list):
            validated_summaries = []
            for item in summary_data["summaries"]:
                if isinstance(item, dict) and "summary" in item:
                    item.setdefault('author', 'Unknown') # Default if missing
                    item.setdefault('score', 0)
                    item.setdefault('link', 'N/A')
                    validated_summaries.append(item)
                else:
                    logger.warning(f"Skipping invalid summary item (missing 'summary' key): {item}")
            logger.info(f"OpenAI summarization successful, returning {len(validated_summaries)} summaries.")
            return validated_summaries
        else:
             logger.error(f"Error: Unexpected JSON structure received from OpenAI: {summary_data}")
             return []

    except json.JSONDecodeError as json_err:
        logger.error(f"Error decoding JSON response from OpenAI: {json_err}")
        logger.error(f"Received raw JSON: {summary_json_string}")
        return []
    except Exception as e:
        logger.error(f"Error during OpenAI summarization: {e}", exc_info=True) # Added exc_info for more details
        return []
    