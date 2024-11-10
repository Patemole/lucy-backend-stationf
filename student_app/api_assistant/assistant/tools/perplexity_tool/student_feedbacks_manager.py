import logging
import asyncpraw
import os

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)

async def get_top_comment(subreddit_name, search_query, input_message):
    logging.info(f"Starting async search for top Reddit feedback for input: '{input_message}' in subreddit '{subreddit_name}' with query '{search_query}'")
    search_query = "Does UPenn truly meet 100 percents of demonstrated financial need"
    
    reddit = asyncpraw.Reddit(
        client_id=os.getenv('GOOGLE_CLOUD_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLOUD_CLIENT_SECRET'),
        user_agent='lucy-2 by /u/your_username'
    )

    comments_list = []  # Initialize an empty list to store comments

    try:
        # Await the subreddit object
        subreddit = await reddit.subreddit(subreddit_name)
        
        # Search for the top post in the specified subreddit with the given query
        async for submission in subreddit.search(search_query, sort='relevance', limit=1):
            logging.info(f"Top post found: Title: '{submission.title}', Score: {submission.score}, URL: {submission.url}")
            
            # Load the submission to ensure comments are available
            await submission.load()
            
            # Fetch top-level comments for the submission
            await submission.comments.replace_more(limit=0)  # Load all comments asynchronously
            logging.info(f"Comments loaded for the submission. for {input_message}")

            # Check and return the top-level comment if available
            if submission.comments:
                # Iterate over the comments and add them to the list
                for top_comment in submission.comments:
                    logging.info(f"Top comment found: '{top_comment.body}' with score {top_comment.score} for {input_message}")
                    # Append each comment to the list in the required format
                    comments_list.append({
                        "comment": str(top_comment.body),
                        "score": str(top_comment.score)
                    })
                    break  # Currently fetching only the first top comment; remove this break to get more comments
            else:
                logging.warning(f"No comments found for the post with title '{submission.title}' for {input_message}")
                
    except Exception as e:
        logging.error(f"Error while fetching comments: {e} for {input_message}")
        
    # Ensure comments_list is a list with at least one element or an empty list if no comments were found
    return comments_list

