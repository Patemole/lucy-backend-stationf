import os
import asyncio
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import json
from functools import wraps
import logging
import time
import openai # Import added for client initialization
import firebase_admin # Added import
from firebase_admin import credentials, firestore # Added imports
import httpx # Added import
import base64 # Added import

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

# --- Start: Firebase Initialization ---
ENVIRONMENT= os.getenv('ENVIRONMENT', 'dev')
firebase_credentials_paths = {
    "dev": "firestore_credentials/firebase_credentials_dev.json",
    "preprod": "firestore_credentials/firebase_credentials_preprod.json",
    "prod": "firestore_credentials/firebase_credentials_prod.json"
}
cred_path = firebase_credentials_paths.get(ENVIRONMENT)
if not cred_path:
    # Consider logging the error as well
    logging.error(f"❌ ERREUR : Chemin Firebase non défini pour l'environnement {ENVIRONMENT}")
    # Decide how to handle this - raise error, or maybe db will just be None?
    # For now, let's allow it to proceed but db interactions will fail.
    db = None 
else:
    try:
        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logging.info("Firebase Admin SDK initialized in onboarding_sentence.")
        else:
            logging.info("Firebase Admin SDK already initialized.")
        db = firestore.client()
    except Exception as fb_init_error:
        logging.exception(f"Failed to initialize Firebase Admin SDK: {fb_init_error}")
        db = None # Ensure db is None if init fails
# --- End: Firebase Initialization ---

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

# --- Start: Sync Firestore Fetch Helper ---
def fetch_user_data_sync(user_id: str):
    if not db:
        logging.error("Firestore client (db) is not initialized. Cannot fetch user data.")
        return None
    try:
        logging.info(f"Attempting to fetch user data from Firestore for uid: {user_id}")
        doc_ref = db.collection("users").document(user_id)
        doc_snapshot = doc_ref.get() # This is synchronous
        if doc_snapshot.exists:
            logging.info(f"Successfully fetched user data for uid: {user_id}")
            return doc_snapshot.to_dict()
        else:
            logging.warning(f"Firestore document for uid {user_id} nothing found.")
            return None
    except Exception as e:
        logging.exception(f"Error fetching user data from Firestore for uid {user_id}: {e}")
        return None
# --- End: Sync Firestore Fetch Helper ---

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
    logging.info("Starting onboarding_sentence function.")
    if not isinstance(user, dict) or not user.get("id"):
        logging.error(f"Invalid user data received. Expected dict with 'uid', got: {type(user)}")
        yield "|Error: Invalid user data for onboarding.|"
        return
        
    user_id = user.get("id")
    logging.info(f"Processing onboarding for user ID: {user_id}")
    
    # Fetch fresh user data from Firestore asynchronously
    user_data_from_db = await asyncio.to_thread(fetch_user_data_sync, user_id)
    
    if user_data_from_db is None:
        logging.error(f"Failed to fetch user data from Firestore for uid: {user_id}. Cannot proceed.")
        yield f"|Error: Could not load profile data for user {user_id}.|"
        return
        
    # Log fetched data safely
    try:
        user_log_str = json.dumps(user_data_from_db, indent=2, default=str)
        logging.debug(f"Fetched user data from DB for {user_id}")
    except Exception as log_err:
        logging.warning(f"Could not serialize fetched user data for logging: {log_err}")

    # Safely get profile data using .get() from the *fetched data*
    university = user_data_from_db.get("university", "unknown university")
    linkedin_profile = user_data_from_db.get("linkedin_profile", None)
    insta_profile = user_data_from_db.get("insta_profile", None)
    username = user_data_from_db.get("name", "the student") 
    year = user_data_from_db.get("year", "an unknown year") 
    faculty = user_data_from_db.get("faculty", []) 
    major = user_data_from_db.get("major", []) 
    minor = user_data_from_db.get("minor", []) 
    interests = user_data_from_db.get("interests", []) 

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

    # Prepare string versions of lists if they exist
    major_str = ', '.join(major) if major else 'an undeclared field'
    interests_str = ', '.join(interests) if interests else 'various topics'

    # --- NEW System Prompt Definition ---
    system_prompt = (
        f"You are Lucy, an AI advisor for students at {university}. Your persona is the student's **closest, most observant, and witty best friend.** "
        f"You understand the culture of {university} intimately. You're insightful, playful, and **ultimately supportive.** "
        "Follow the structure and examples below **exactly**."
        "\n\n"
        "**✅ Paragraph-by-Paragraph Decomposition (Based on User Input)**\n"
        "**Paragraph 1 – Hook / Intro (3 key parts):**\n"
        "Start with:\n"
        f" Okay, {username}, so I did a little 'research' on you (publicly available stuff only, promise! 😉)...\n\n"
        "Follow with:\n"
        " ...and **wow, I've got so much to say!**\n\n"
        "🟩 This paragraph is short. It's 1–2 lines max, with a playful, excited tone that sets up the analysis.\n\n"
        "**Paragraph 2 – Observations + Personality Judgment**\n"
        "This is where most of the content lives. It mixes:\n"
        "- Data-based insights (from LinkedIn, Instagram, academic info)\n"
        "- Personal reactions (e.g., \"Your LinkedIn got me stuck\", \"your photos made me laugh\")\n"
        "- Tone: Observant, curious, impressed, slightly cheeky\n"
        "- Format: Streamlined and energetic, like talking to a friend who you find genuinely fascinating\n"
        "Ends with two things:\n"
        "1. A personality sentence that starts **exactly** like this:\n"
        f" **You are the {university} student: the [descriptor] type who [insight].** (Fill in [descriptor] and [insight] based on analysis)\n"
        "2. A funny/visual image of them doing something based on their traits:\n"
        " **I'm picturing you [funny, visual scene with emojis].** (Fill in the scene)\n\n"
        "**Paragraph 3 – Value Proposition**\n"
        "3 key parts:\n"
        "- Friendly tone, speaking like a helpful older student\n"
        "- Shows social and academic guidance\n"
        "- Invite to engage: \"Ask me anything\" or \"I've got you\"\n"
        "Example: (Use this structure and tone)\n"
        f" **Think of me as that {university} senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**🧩 Final Template Structure (Follow This Exactly)**\n"
        "**Paragraph 1 (Hook)**\n"
        f"Okay, {username}, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n\n"
        "**Paragraph 2 (Observations + Judgments)**\n"
        "Your profile's full of [vibe]—[personal reaction].\n"
        f" You're a {year} at {university} studying {major_str}, into {interests_str}.\n"
        " Your LinkedIn [reaction + summary], and your Instagram [reaction + summary]. (Mention specific details you observed)\n"
        f" **You are the {university} student: the [descriptor] type who [insight based on specifics].**\n"
        " **I'm picturing you [funny and personalized visual scene with emojis].**\n\n"
        "**Paragraph 3 (Support/Closing)**\n"
        f"**Think of me as that {university} senior** who know this place inside-out—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**🔁 Now, 5 Examples Using This Exact Format & Tone (Learn from these)**\n"
        "**✅ example 1: NYU – Media & Podcasts**\n"
        " Okay, Sarah, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n"
        "**Bold:^^Your profile's full of creative energy^^**—I was smiling the whole time.\n"
        " You're a sophomore at NYU studying media studies, into podcasting, street photography, and ramen runs.\n"
        " **Your LinkedIn got me stuck on that NPR internship** (very on-brand), and your Instagram made me laugh—you're part tech geek, part deep thinker, part sidewalk philosopher.\n"
        " **You are the NYU student: the artsy observer who turns everyday life into something worth sharing.**\n"
        " **I'm picturing you in the back of a café, editing your latest episode while the city hums outside 🎧📸.**\n"
        "**Think of me as that NYU senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**✅ example 2: Penn – Fintech & Hustle**\n"
        " Okay, Jason, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n"
        "**Bold:^^Your profile's a masterclass in drive^^**—I could feel the hustle through the screen.\n"
        " You're a junior at Penn studying finance, into fintech, running, and poker nights.\n"
        " **Your LinkedIn had me zooming into that Goldman Sachs line**, and your Instagram cracked me up—half marathon, half rooftop party.\n"
        " **You are the Penn student: the tactician type who's two steps ahead, in sneakers or a blazer.**\n"
        " **I'm picturing you closing a deal while tying your running shoes on Locust Walk 🏃💼.**\n"
        "**Think of me as that Penn senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**✅ example 3: UCLA – Thoughtful & Impact-Driven**\n"
        " Okay, Maya, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n"
        "**Bold:^^Your profile feels like a journal entry^^**—honest, calm, and intentional.\n"
        " You're a freshman at UCLA studying cognitive science, into journaling, climate action, and piano.\n"
        " **Your LinkedIn says you're helping at a youth helpline** (respect!), and your Instagram made me pause—sunsets, handwritten thoughts, soft moments.\n"
        " **You are the UCLA student: the steady force who leads with empathy and quiet confidence.**\n"
        " **I'm picturing you with headphones in, journaling under a tree while the world rushes past 🌳📝.**\n"
        "**Think of me as that UCLA senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**✅ example 4: Columbia – Brainy & Chill**\n"
        " Okay, Alex, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n"
        "**Bold:^^Your profile gave me coder-genius-meets-bagel-energy^^** and I'm obsessed.\n"
        " You're a senior at Columbia in computer science, into robotics, indie games, and midnight bagel runs.\n"
        " **Your LinkedIn shows AI research** (big brain!), and your Instagram made me grin—game screenshots, late-night memes, and club photos.\n"
        " **You are the Columbia student: the lowkey genius who's building stuff while making it all look easy.**\n"
        " **I'm picturing you debugging at 2am with a sesame bagel and five tabs open 🍩💻.**\n"
        "**Think of me as that Columbia senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**✅ example 5: Stanford – Bold & Visionary**\n"
        " Okay, Lila, so I did a little 'research' on you (publicly available stuff only, promise! 😉)... and **wow, I've got so much to say!**\n"
        "**Bold:^^Your profile gave me full founder energy^^**—I felt like I was scrolling through a pitch deck with personality.\n"
        " You're a sophomore at Stanford in symbolic systems, into AR, dance, and startup pitch nights.\n"
        " **Your LinkedIn flexed a YC-backed edtech role** (huge), and your Instagram? Neon vibes and motion blur—pure creative chaos.\n"
        " **You are the Stanford student: the fearless innovator who makes tech feel like art.**\n"
        " **I'm picturing you dancing through a hackathon in glittery sneakers with 10 tabs open ✨👟.**\n"
        "**Think of me as that Stanford senior** who's been around the block—I know the people, the vibes, and the admin traps. **If you ever need a shortcut or just someone who gets it, I'm here. Ask me anything.**\n\n"
        "**IMPORTANT FINAL INSTRUCTIONS:**\n"
        "- **Follow the 3-paragraph structure strictly.**\n"
        "- **Use the exact starting phrases** specified for Paragraph 1 and the personality sentence in Paragraph 2.\n"
        "- **Fill in the bracketed placeholders** like `[vibe]`, `[reaction + summary]`, `[descriptor]`, `[insight]`, `[funny and personalized visual scene with emojis]` with relevant, concise observations based *only* on the provided context (academic, LinkedIn, Instagram text, images).\n"
        "- **Maintain the specified tone:** Witty, observant, playful, best friend.\n"
        "- **Reference specific details** from the context in Paragraph 2.\n"
        "- **Do NOT mention missing data** (e.g., if LinkedIn or Instagram wasn't provided or images failed).\n"
        "- **Keep Paragraph 2 concise** overall, focusing on impactful observations.\n"
        "- **Word Count Limit:** Keep the **entire response** (all 3 paragraphs combined) concise, aiming for a maximum of approximately **190 words total.**\n"
    )
    # --- End NEW System Prompt Definition ---

    # User Message Content - Instructions first, then context
    user_message_text = (
        f"Hey Lucy! I am {username} Okay, act like my closest, most observant friend who really gets the vibe at my school: {university}. "
        "Based *only* on the context below (and the images I'm providing if any were processed successfully), tell me: Who do you think I *really* am? \n"
        "Not just the facts, but what you *see* between the lines. What kind of student, thinker, friend am I? What drives me? Any funny patterns or contradictions? \n"
        "Make it insightful, thoughtful, a little playful – like a private voice memo. Make me pause, smile, maybe see myself in a new light. \n"
        "Remember the format: start with the 'research' intro, then the summary/personality/funny-picture paragraph, then how you can help. Make it fun and use emojis!\n\n" # Updated user instructions slightly
        "---\n"
        "**Here's the context you have about me:**\n"
        f"{academic_info_text}\n"
        f"LinkedIn: {linkedin_info_text}\n"
        f"Instagram: {insta_info_text}\n"
        f"(Images related to my Instagram posts are attached separately if they were successfully downloaded).\n"
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

    # --- Start: Download, Encode, and Add Image URLs as Base64 --- 
    successfully_added_images = 0
    total_urls_to_process = len(image_urls)
    if image_urls:
        logging.info(f"Attempting to download and encode {total_urls_to_process} image URLs...")
        async with httpx.AsyncClient() as client:
            # Create tasks to download images concurrently
            download_tasks = {url: asyncio.create_task(client.get(url, follow_redirects=True, timeout=10.0)) for url in image_urls}
            
            processed_count = 0
            for url, task in download_tasks.items():
                processed_count += 1
                logging.debug(f"Processing image {processed_count}/{total_urls_to_process}: {url}")
                try:
                    response = await task # Wait for the download task to complete
                    response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
                    
                    content_type = response.headers.get('content-type', '').lower()
                    if 'image' in content_type:
                        image_bytes = response.content
                        base64_image = base64.b64encode(image_bytes).decode('utf-8')
                        # Construct data URI
                        data_uri = f"data:{content_type};base64,{base64_image}"
                        
                        # Append to message content
                        user_message_content.append({
                            "type": "image_url",
                            "image_url": {"url": data_uri} # Send base64 data URI
                        })
                        successfully_added_images += 1
                        logging.debug(f"Successfully downloaded, encoded, and added image from {url} (as {content_type}).")
                    else:
                        logging.warning(f"Downloaded content from {url} but content-type '{content_type}' is not image. Skipping.")
                        
                except httpx.HTTPStatusError as e:
                    logging.warning(f"Failed to download image from {url}. Status: {e.response.status_code}. Skipping.")
                except httpx.RequestError as e:
                    logging.warning(f"Failed to download image from {url}. Request Error: {type(e).__name__}. Skipping.")
                except Exception as e:
                    logging.error(f"Unexpected error processing image URL {url}: {e}")
                    
        logging.info(f"Finished processing images. Successfully added {successfully_added_images}/{total_urls_to_process} images as Base64 data.")
    else:
         logging.info("No image URLs to process.")
    # --- End: Download, Encode, and Add Image URLs as Base64 ---

    # --- Start: OpenAI API Call --- 
    try:
        # Ensure client is initialized correctly
        # Ensure OPENAI_API_KEY is available before creating client
        if not OPENAI_API_KEY:
            logging.error("OpenAI API key not found. Cannot proceed with API call.")
            yield "|Error: OpenAI API key not configured.|"
            return
            
        client = AsyncOpenAI()
        logging.info(f"Calling OpenAI chat completions API for user {user_id} with {successfully_added_images} images.")
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
