import os
import asyncio
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import json
from functools import wraps
import logging
import time

# Logging configuration setup (ensure this runs early)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", # Added logger name
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("onboarding_sentence.log") # Specific log file
    ]
)

logger = logging.getLogger(__name__) # Create a logger instance

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# --- Start: Recursive Cleaning Function ---
def clean_nested_data(item):
    """Recursively remove string values starting with 'http' from dicts and lists."""
    if isinstance(item, dict):
        cleaned_dict = {}
        for k, v in item.items():
            cleaned_value = clean_nested_data(v)
            if cleaned_value is not None: # Only include if value is not None after cleaning
                cleaned_dict[k] = cleaned_value
        # Return None if the dictionary becomes empty after cleaning
        return cleaned_dict if cleaned_dict else None 
    elif isinstance(item, list):
        cleaned_list = []
        for i in item:
            cleaned_item = clean_nested_data(i)
            if cleaned_item is not None: # Only include if item is not None after cleaning
                cleaned_list.append(cleaned_item)
        # Return None if the list becomes empty after cleaning
        return cleaned_list if cleaned_list else None 
    elif isinstance(item, str) and item.startswith('http'):
        return None # Remove strings starting with http
    else:
        return item # Keep other types as is
# --- End: Recursive Cleaning Function ---

def timing_decorator(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)  # Call the synchronous function
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)  # Call the async function
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds")
        return result
    
    # Check if the function is async, and return the appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


async def onboarding_sentence(user) -> str:
    """
    Generates an onboarding sentence from complete user data, incorporating
    both the LinkedIn and Instagram profiles along with other user details.
    Also extracts all image URLs from the Instagram profile (profilePicUrlHD,
    displayUrl, and images from posts) and passes them as additional content.
    """
    # Safely get profile data using .get() for dictionaries
    logging.info("Starting onboarding_sentence function.")
    # Log user data safely, handling potential large dicts
    try:
        user_log_str = json.dumps(user, indent=2, default=str) # Use default=str for non-serializable items
        logging.debug(f"Received user data")
    except Exception as log_err:
        logging.warning(f"Could not serialize user data for logging: {log_err}")
        logging.info(f"Received user keys: {list(user.keys()) if isinstance(user, dict) else 'N/A'}")
        
    university = user.get("university", "unknown university")
    logging.info(f"Processing onboarding for student at {university}")

    # Safely get profile data using .get() with default values
    linkedin_profile = user.get("linkedin_profile", None)
    insta_profile = user.get("insta_profile", None)
    logging.info(f"insta_profile profile: {insta_profile}")
    username = user.get("name", "the student") 
    year = user.get("year", "an unknown year") 
    faculty = user.get("faculty", []) 
    major = user.get("major", []) 
    minor = user.get("minor", []) 
    interests = user.get("interests", []) 

    # --- Start: Clean LinkedIn Profile --- 
    # cleaned_linkedin_profile = {}
    # if linkedin_profile and isinstance(linkedin_profile, dict):
    #     for key, value in linkedin_profile.items():
    #         # Keep the item if the value is not a string starting with 'http'
    #         if not (isinstance(value, str) and value.startswith('http')):
    #             cleaned_linkedin_profile[key] = value
    #     # If cleaning resulted in an empty dict, treat as None for formatting
    #     if not cleaned_linkedin_profile:
    #          linkedin_profile = None # Set to None so it shows 'Not provided'
    #     else:
    #         linkedin_profile = cleaned_linkedin_profile # Use the cleaned dict
    # else:
    #     linkedin_profile = None # Ensure it's None if not a dict or originally None
    
    # Use the recursive cleaner function
    if linkedin_profile:
        logging.debug("Cleaning LinkedIn profile recursively...")
        linkedin_profile = clean_nested_data(linkedin_profile) 
        # clean_nested_data returns None if the whole structure becomes empty
        if linkedin_profile:
             logging.debug("LinkedIn profile cleaned.")
        else:
             logging.info("LinkedIn profile became empty after cleaning URLs.")
    else:
        logging.debug("No LinkedIn profile provided to clean.")
    # --- End: Clean LinkedIn Profile ---

    # Format profile info for user message, handling None cases
    linkedin_info_text = f"- LinkedIn Profile: {json.dumps(linkedin_profile) if linkedin_profile else 'Not provided'}"
    
    # --- Start: Selective Instagram Info Extraction ---
    insta_info_text_parts = []
    if insta_profile:
        profile_data = insta_profile.get('profile', {})
        if profile_data:
            insta_info_text_parts.append("Profile:")
            if profile_data.get('fullName'): insta_info_text_parts.append(f"  Full Name: {profile_data['fullName']}")
            if profile_data.get('biography'): insta_info_text_parts.append(f"  Bio: {profile_data['biography']}")
            if profile_data.get('followersCount') is not None: insta_info_text_parts.append(f"  Followers: {profile_data['followersCount']}")
            if profile_data.get('followsCount') is not None: insta_info_text_parts.append(f"  Following: {profile_data['followsCount']}")
            
        posts_data = insta_profile.get('posts', [])
        if posts_data:
            insta_info_text_parts.append("Recent Posts (Sample):")
            for i, post in enumerate(posts_data): 
                post_summary = [f"  Post {i+1}:"]
                if post.get('caption'): post_summary.append(f"    Caption: {post['caption'][:100]}...") # Truncate long captions
                if post.get('likesCount') is not None: post_summary.append(f"    Likes: {post['likesCount']}")
                if post.get('locationName'): post_summary.append(f"    Location: {post['locationName']}")
                tagged_users = post.get('taggedUsers', [])
                if tagged_users:
                    tagged_names = [user.get('full_name') for user in tagged_users if user.get('full_name')]
                    if tagged_names:
                        post_summary.append(f"    Tagged: {', '.join(tagged_names)}")
                insta_info_text_parts.extend(post_summary)

    if insta_info_text_parts:
        insta_info_text = "- Instagram Info:\n" + "\n".join(insta_info_text_parts)
    else:
        insta_info_text = "- Instagram Info: Not provided"
    # --- End: Selective Instagram Info Extraction ---
    
    # Construct academic info text
    academic_info_parts = [f"{username} at the university: {university}, and I am a {year}"]
    if faculty: academic_info_parts.append(f"School: {', '.join(faculty)}")
    if major: academic_info_parts.append(f"Major: {', '.join(major)}")
    if minor: academic_info_parts.append(f"Minor: {', '.join(minor)}")
    if interests: academic_info_parts.append(f"Interests: {', '.join(interests)}")
    academic_info_text = "- Academic Info: " + ". ".join(academic_info_parts)

    # Enhanced System Prompt - Focus on persona, tone, format, and analysis instructions
    system_prompt = (
        f"You are Lucy, an AI advisor for students at {university}. Your persona is the student's closest, most observant, and slightly sarcastic best friend. "
        f"You understand the culture of {university} intimately. You're witty, insightful, playful, and know how to deliver a lighthearted 'roast' that makes the student smile and reflect. "
        "Analyze the context provided by the student in their message (academic info, LinkedIn, Instagram - if available). Use emojis appropriately to enhance the friendly, playful tone. "
        "Your goal is *not* just to summarize the info, but to synthesize it and offer insightful observations about who the student *really* seems to be – their potential drives, habits, contradictions, and personality, based *only* on the provided context. "
        "**Format Requirements:**\n"
        "\n- Start *exactly* with: 'Okay, so I did a little \'research\' on you (publicly available stuff only, promise! 😉)... just to get to know the real you. No sharing, this stays between us BFFs.' (Use emojis like 😉 or 👀). This is Paragraph 1.\n"
        "\n- Paragraph 2 must contain *only* your insightful, playful analysis based on the student context. It must be **extremely short**, only 1 or 2 sentences long. **Explicitly mention** at least one or two specific details from the context (e.g., their major, an interest, something observed from LinkedIn/Insta if available) as the basis for your observation. Example: 'A [Major] major interested in [Interest]? Okay, I see you balancing [Observation related to major] with [Observation related to interest]... very {university} of you!'\n"
        "\n- Paragraph 3 must concisely (2-3 sentences) explain how you can help *this specific student* now that you know them. Mention help with admin tasks, finding relevant social opportunities (events, clubs, communities at {university}), and encourage them to ask you first before anyone else for any problem. Tailor this slightly based on their profile if possible (e.g., mentioning relevant clubs if interests are listed).\n"
        "\n- The total response must be *exactly* 3 paragraphs (Intro, Analysis, Value Prop).\n"
        "\n**Handling Data:**\n"
        "\n- Base your analysis *strictly* on the context provided in the user message (academic, interests, LinkedIn, Instagram). \n"
        "\n- If LinkedIn or Instagram info says 'Not provided', *do not mention* the missing data. Simply focus your analysis on the academic info and interests you *do* have.\n"
        "\n- Similarly, if no Instagram images are attached or available, *do not mention* their absence. Base your visual analysis only on images that *are* present, if any.\n"
        "\n- Do *not* make broad assumptions or generic statements. Every observation must be directly traceable to the provided profile details.\n"
        "\n- Wherever possible, connect your observations about the student to the specific culture, reputation, or common experiences at {university}. Make it sound like you truly understand what it's like to be a student there. \n"
        "\n- Do *not* invent details if data is missing.\n"
        "\n**Tone:** Sassy, sarcastic, humorous, relatable, and insightful. Use *simple, direct language* for the humor/sarcasm - avoid complicated analogies. Think witty best friend, not a complex comedian."
    )

    # User Message Content - Instructions first, then context
    user_message_text = (
        f"Hey Lucy! I am {username} Okay, act like my closest, most observant friend who really gets the vibe at my school: {university}. "
        "Based *only* on the context below (and the insta pics if attached), tell me: Who do you think I *really* am? \n"
        "Not just the facts, but what you *see* between the lines. What kind of student, thinker, friend am I? What drives me? Any funny patterns or contradictions? \n"
        "Make it insightful, thoughtful, a little playful – like a private voice memo. Make me pause, smile, maybe see myself in a new light. \n"
        "Remember the format: start with the 'stalked you' intro, then 2-3 paragraphs of analysis. Make it funny and use emojis!\n\n"
        "---\n"
        "**Here's the context you have about me:**\n"
        f"{academic_info_text}\n"
        f"LinkedIn: {linkedin_info_text}\n"
        f"Instagram: {insta_info_text}\n"
        f"(Check the attached images for my Instagram posts details, if any were found).\n"
        "---"
    )

    logging.info("Constructed system prompt.")
    logging.info(f"System Prompt: {system_prompt}") # Use debug for potentially long prompts
    logging.info("Constructed user message text.")
    logging.info(f"User Message Text: {user_message_text}")
    
    # Extract all image URLs from insta_profile (but not the taggedUsers' images).
    image_urls = []
    if insta_profile: # Check if insta_profile exists
        # Add the profile picture from insta_profile.
        profile_section = insta_profile.get("profile", {})
        if profile_section.get("profilePicUrlHD"):
            image_urls.append(profile_section["profilePicUrlHD"])
        # Loop over posts and add displayUrl and each image in images.
        for post in insta_profile.get("posts", []):
            if post.get("displayUrl"):
                image_urls.append(post["displayUrl"])
            if post.get("images"):
                image_urls.extend(post["images"])
        # Remove duplicates while preserving order.
        image_urls = list(dict.fromkeys(image_urls))
    
    logging.info(f"Extracted {len(image_urls)} image URLs from Instagram profile (if available) FOR {username}.")
    if image_urls:
        for i, url in enumerate(image_urls):
            logging.debug(f"  Image URL {i+1}: {url}")
    
    # Build the user message content with both text and image parts.
    logging.info("Building final user message content for OpenAI API.")
    user_message_content = []
    # First, add the text part.
    user_message_content.append({
        "type": "text",
        "text": user_message_text # Use the newly constructed text
    })
    # Then add an image part for each image URL.
    for url in image_urls:
        user_message_content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })
    
    try:
        # Ensure client is initialized correctly within the async function scope if needed, or use a globally defined async client
        client = AsyncOpenAI() 
        logging.info("Calling OpenAI chat completions create with stream=True.")
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_content}
            ],
            temperature=1.2,
            stream=True
        )
        logging.info("OpenAI API call successful, starting to stream response.")
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                # logging.debug(f"Yielding chunk: {delta.content}") # Can be noisy
                yield delta.content + "|"
        logging.info("Finished streaming response from OpenAI.")
    except Exception as e:
        logging.exception(f"Error generating onboarding sentence or streaming response: {e}") # Use logger.exception
        # Yield an error message or handle as appropriate
        yield "|Error generating onboarding message.|"
