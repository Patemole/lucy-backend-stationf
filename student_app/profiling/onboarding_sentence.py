
import os
import asyncio
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import json



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
    linkedin_info = f"LinkedIn Profile: {user.linkedin_profile}"
    insta_info = f"Instagram Profile: {user.insta_profile['profile']}"  # Excluding post images.
    base_text = f"{user.username} at {university}, {user.year}"
    faculty_text = f"School: {', '.join(user.faculty)}" if user.faculty else ""
    major_text = f"Major: {', '.join(user.major)}" if user.major else ""
    minor_text = f"Minor: {', '.join(user.minor)}" if user.minor else ""
    interests_text = f"Interests: {', '.join(user.interests)}" if user.interests else ""

    system_prompt = (
        f"Lucy, you are an advisor for {user.username} at {university}. "
        f"You role is to show everything you know about the student from all the context you have but in a funny way. I want you to roast him on his profile, also link it to what you know about his school find something niche and be very very sarcastic "
        f"Here are their profile details:\n{linkedin_info}\n{insta_info}\n"
        f"Profile Overview: {base_text}. {faculty_text}. {major_text}. {minor_text}. {interests_text}"
    )
    
    logging.info("Constructed system prompt:")
    logging.info(system_prompt)
    
    # Extract all image URLs from insta_profile (but not the taggedUsers' images).
    image_urls = []
    # Add the profile picture from insta_profile.
    profile_section = user.insta_profile.get("profile", {})
    if profile_section.get("profilePicUrlHD"):
        image_urls.append(profile_section["profilePicUrlHD"])
    # Loop over posts and add displayUrl and each image in images.
    for post in user.insta_profile.get("posts", []):
        if post.get("displayUrl"):
            image_urls.append(post["displayUrl"])
        if post.get("images"):
            image_urls.extend(post["images"])
    # Remove duplicates while preserving order.
    image_urls = list(dict.fromkeys(image_urls))
    
    logging.info("Extracted image URLs from Instagram:")
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
                I want you to act like my closest, most observant friend.  you understand the culture of the school I attend. You know what I post and what I don’t, how I present myself publicly, and what that might reveal privately. 
                Now, based only on that, tell me:
                Who do you think I really am?
                Not what I say I am, but what you see. What kind of student, thinker, friend, and person am I? What drives me? What patterns do you notice? What contradictions stand out?

                This isn’t a roast it is more a game. It’s more like a private voice memo from someone who knows me better than I know myself. Be insightful, thoughtful, a little playful—and make me pause, smile, and maybe see myself in a new light.    

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
        # Create the AsyncOpenAI client with the API key and USE IT
        client = openai.AsyncOpenAI(api_key=openai.api_key)
        
        # Use the client variable here instead of creating a new instance
        response = await client.chat.completions.create(
            model="gpt-4o",  # Use the appropriate model.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message_content}
            ],
            temperature=1.2
        )
        logging.info("OpenAI API call successful for onboarding sentence")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating onboarding sentence: {e}")
        return None

