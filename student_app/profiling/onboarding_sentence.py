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
    # Safely get profile data using .get() for dictionaries
    university = user.get("university", "unknown university")
    logging.info(f"Starting onboarding_sentence for student at {university}")

    # Safely get profile data using .get() with default values
    linkedin_profile = user.get("linkedin_profile", None)
    insta_profile = user.get("insta_profile", None)
    username = user.get("name", "the student") 
    year = user.get("year", "an unknown year") 
    faculty = user.get("faculty", []) 
    major = user.get("major", []) 
    minor = user.get("minor", []) 
    interests = user.get("interests", []) 

    # Format profile info for user message, handling None cases
    linkedin_info_text = f"- LinkedIn Profile: {json.dumps(linkedin_profile) if linkedin_profile else 'Not provided'}"
    insta_profile_data = insta_profile.get('profile', {}) if insta_profile else {}
    insta_info_text = f"- Instagram Profile Summary: {json.dumps(insta_profile_data) if insta_profile_data else 'Not provided'}"
    
    # Construct academic info text
    academic_info_parts = [f"{username} at {university}, {year}"]
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
        "Hey Lucy! Okay, act like my closest, most observant friend who really gets the vibe at my school. "
        "Based *only* on the context below (and the insta pics if attached), tell me: Who do you think I *really* am? \n"
        "Not just the facts, but what you *see* between the lines. What kind of student, thinker, friend am I? What drives me? Any funny patterns or contradictions? \n"
        "Make it insightful, thoughtful, a little playful – like a private voice memo. Make me pause, smile, maybe see myself in a new light. \n"
        "Remember the format: start with the 'stalked you' intro, then 2-3 paragraphs of analysis. Make it funny and use emojis!\n\n"
        "---\n"
        "**Here's the context you have about me:**\n"
        f"{academic_info_text}\n"
        f"{linkedin_info_text}\n"
        f"{insta_info_text}\n"
        f"(Check the attached images for my Instagram posts details, if any were found).\n"
        "---"
    )

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
        stream = await client.chat.completions.create(
            model="gpt-4o",
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
