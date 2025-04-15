import os
import asyncio
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import json
from functools import wraps
import logging


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("file_server.log")
    ]
)

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
    university = getattr(user, "university", "unknown university")
    logging.info(f"Starting onboarding_sentence for student at {university}")

    # Build the system prompt.
    # Safely get profile data using getattr with default values
    linkedin_profile = getattr(user, "linkedin_profile", None)
    insta_profile = getattr(user, "insta_profile", None)
    #username = getattr(user, "username", "the student")
    username = user.username
    year = getattr(user, "year", "an unknown year")
    faculty = getattr(user, "faculty", [])
    major = getattr(user, "major", [])
    minor = getattr(user, "minor", [])
    interests = getattr(user, "interests", [])

    # Format profile info, handling None cases
    linkedin_info = f"LinkedIn Profile: {json.dumps(linkedin_profile) if linkedin_profile else 'Not provided'}"
    # Safely access nested insta_profile data
    insta_profile_data = insta_profile.get('profile', {}) if insta_profile else {}
    insta_info = f"Instagram Profile Summary: {json.dumps(insta_profile_data) if insta_profile_data else 'Not provided'}"  # Excluding post images for brevity in prompt
    
    base_text = f"{username} at {university}, {year}"
    faculty_text = f"School: {', '.join(faculty)}" if faculty else ""
    major_text = f"Major: {', '.join(major)}" if major else ""
    minor_text = f"Minor: {', '.join(minor)}" if minor else ""
    interests_text = f"Interests: {', '.join(interests)}" if interests else ""

    system_prompt = (
        f"Lucy, you are an advisor for {username} at {university}. "
        f"You role is to show everything you know about the student from all the context you have but in a funny way. I want you to roast him on his profile, also link it to what you know about his school find something niche and be very very sarcastic "
        f"Here are their profile details:\n{linkedin_info}\n{insta_info}\n"
        f"Profile Overview: {base_text}. {faculty_text}. {major_text}. {minor_text}. {interests_text}"
    )

    print(f"system_prompt: {system_prompt}")
    
    logging.info("Constructed system prompt:")
    logging.info(system_prompt)
    
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
    
    logging.info("Extracted image URLs from Instagram:")
    if image_urls:
        for url in image_urls:
            logging.info(url)
    
    # Build the user message content with both text and image parts.
    user_message_content = []
    # First, add the text part.
    user_message_content.append({
        "type": "text",
        "text": (
            """
                On context you have info about me like my academic background, my school, my linkedin profile and insta with pics (attached)            
                I want you to act like my closest, most observant friend.  you understand the culture of the school I attend. You know what I post and what I don't, how I present myself publicly, and what that might reveal privately. 
                Now, based only on that, tell me:
                Who do you think I really am?
                Not what I say I am, but what you see. What kind of student, thinker, friend, and person am I? What drives me? What patterns do you notice? What contradictions stand out?

                This isn't a roast it is more a game. It's more like a private voice memo from someone who knows me better than I know myself. Be insightful, thoughtful, a little playful—and make me pause, smile, and maybe see myself in a new light.    

                ---
                format:
                do 2 or 3 paragraphs 
                start off with a sentence like: i stalked you on the internet (only public data, i promise) just to get to know you better. no sharing, not even with the school—just between us bff and then about me
            """
        )
    })
    # Then add an image part for each image URL.
    for url in image_urls:
        user_message_content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })
    
    try:
        client = AsyncOpenAI()
        stream = await client.chat.completions.create(
            model="gpt-4o",  # Use the appropriate model.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_content}
            ],
            temperature=1.2,
            stream=True
        )
        logging.info("OpenAI API call successful for onboarding sentence with streaming")
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content + "|"
    except Exception as e:
        logging.error(f"Error generating onboarding sentence: {e}")
        # Yield an error message or handle as appropriate
        yield "|Error generating onboarding message.|"
