import requests
import httpx
import logging
import time
from google.cloud import firestore
import os

import firebase_admin
from firebase_admin import credentials, auth, firestore

# Logging configuration setup (ensure this runs early)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", # Added logger name
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("profile_generation.log") # Specific log file
    ]
)
logger = logging.getLogger(__name__) # Create a logger instance

# Comment out or remove this line as it's causing the error
# db = firestore.Client()

def timing_decorator(func):
    import functools, time
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logging.info(f"{func.__name__} took {elapsed:.2f} seconds")
        return result
    return wrapper

import requests
import time
import logging
from google.cloud import firestore

# Firestore client initialization.
# Make sure that your environment is set up with the correct credentials.

ENVIRONMENT= os.getenv('ENVIRONMENT', 'dev')
firebase_credentials_paths = {
    "dev": "firestore_credentials/firebase_credentials_dev.json",
    "preprod": "firestore_credentials/firebase_credentials_preprod.json",
    "prod": "firestore_credentials/firebase_credentials_prod.json"
}

cred_path = firebase_credentials_paths.get(ENVIRONMENT)
if not cred_path:
    raise ValueError(f"❌ ERREUR : Chemin Firebase non défini pour l'environnement {ENVIRONMENT}")
cred = credentials.Certificate(cred_path)
# Initialize Firebase Admin SDK only if it hasn't been initialized yet
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized.") # Use logger
else:
    logger.info("Firebase Admin SDK already initialized.") # Use logger

db = firebase_admin.firestore.client()

# These are assumed to be defined somewhere in your config.
ACTOR_RUN_ID = "dPrF3WOkNGnISo9Co"
DATASET_ID = "wWcBu2Xs9rjwPQBwH"
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
PDL_API_KEY = os.getenv("PDL_API_KEY")
PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")

def timing_decorator(func):
    # Example timing decorator; replace with your actual decorator if needed.
    import functools, time
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.2f} seconds")
        return result
    return wrapper

@timing_decorator
def scrape_instagram(username, uid):
    """
    Scrapes Instagram for the given username, curates the profile and posts data,
    and then updates the Firestore document for the given uid with a new field "insta_profile".
    
    :param username: Instagram username to scrape.
    :param uid: The Firestore document ID (user UID) to update.
    :return: The curated output (dict) or None if an error occurred.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting scrape_instagram for username: {username}, uid: {uid}")
    
    try:
        # Poll the actor run status until it is finished, with a timeout.
        run_url = f'https://api.apify.com/v2/actor-runs/{ACTOR_RUN_ID}?token={APIFY_API_KEY}'
        logger.info("Waiting for actor run to complete...")
        
        start_time = time.time() # Record start time for timeout
        timeout_seconds = 10 # 5 minutes timeout
        
        while True:
            # Check for timeout
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Timeout ({timeout_seconds}s) reached waiting for Apify actor run {ACTOR_RUN_ID} to complete for user {username}. Moving on.")
                return None # Exit function if timeout is reached
                
            response = requests.get(run_url)
            # Add basic check for non-200 status codes from the polling request itself
            if response.status_code != 200:
                 logger.error(f"Error polling Apify run status ({response.status_code}): {response.text}. Trying again shortly.")
                 time.sleep(5) # Wait longer if there was an API error
                 continue
                 
            run_data = response.json()
            status = run_data.get('data', {}).get('status')

            if status == 'SUCCEEDED':
                logger.info("Run completed successfully.")
                break
            elif status == 'FAILED':
                logger.error(f"Apify actor run {ACTOR_RUN_ID} failed for user {username}.")
                return None # Exit if run failed
            elif status in ['ABORTED', 'TIMED-OUT', 'TIMING-OUT', 'ABORTING']:
                logger.warning(f"Apify actor run {ACTOR_RUN_ID} is in non-successful terminal state: {status} for user {username}. Aborting wait.")
                return None # Exit for other non-successful terminal states
            
            # If still running or in another state, log and wait
            logger.info(f"Run status is {status}. Waiting...")
            time.sleep(5)  # Check every 5 seconds instead of 1 to reduce polling frequency

        # Retrieve the dataset items.
        dataset_url = f'https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_API_KEY}'
        logger.info(f"Fetching dataset items from {dataset_url}...")
        response = requests.get(dataset_url)
        logger.info(f"Apify dataset response status: {response.status_code}")
        data = response.json()

        # Filter results by the specified Instagram username.
        logger.info(f"Filtering dataset for username: {username}")
        results = [item for item in data if item.get('username', '').lower() == username.lower()]
        if not results:
            logger.warning(f"No data found for the username: {username} in Apify dataset.")
            return None
        logger.info(f"Found data for {username}.")

        profile_data = results[0]
        logger.info("Curating profile data...")
        curated_profile = {
            'followersCount': profile_data.get('followersCount'),
            'followsCount': profile_data.get('followsCount'),
            'biography': profile_data.get('biography'),
            'fullName': profile_data.get('fullName'),
            'username': profile_data.get('username'),
            'inputUrl': profile_data.get('inputUrl'),
            'profilePicUrlHD': profile_data.get('profilePicUrlHD')
        }

        logger.info("Curating post data...")
        # Assume 'latestPosts' is ordered from newest to oldest.
        latest_posts = profile_data.get('latestPosts', [])
        # Filter out posts that are not "Image" or "Sidecar" (skip Videos).
        filtered_posts = [post for post in latest_posts if post.get('type') in ['Image', 'Sidecar']]
        # Limit to the first 4 posts.
        filtered_posts = filtered_posts[:4]

        curated_posts = []
        for post in filtered_posts:
            post_type = post.get('type')
            if post_type == 'Image':
                curated_post = {
                    'caption': post.get('caption'),
                    'displayUrl': post.get('displayUrl'),
                    'mentions': post.get('mentions', []),
                    'commentsCount': post.get('commentsCount'),
                    'likesCount': post.get('likesCount'),
                    'timestamp': post.get('timestamp'),
                    'taggedUsers': post.get('taggedUsers'),
                    'locationName': post.get('locationName')
                }
            elif post_type == 'Sidecar':
                # Extract all image URLs from the child posts.
                if 'childPosts' in post and isinstance(post['childPosts'], list):
                    images = [child.get('displayUrl') for child in post['childPosts'] if child.get('displayUrl')]
                else:
                    images = [post.get('displayUrl')]
                curated_post = {
                    'caption': post.get('caption'),
                    'mentions': post.get('mentions', []),
                    'commentsCount': post.get('commentsCount'),
                    'displayUrl': post.get('displayUrl'),
                    'likesCount': post.get('likesCount'),
                    'images': images,
                    'timestamp': post.get('timestamp'),
                    'locationName': post.get('locationName'),
                    'taggedUsers': post.get('taggedUsers')
                }
            else:
                # Skip posts that are not Image or Sidecar.
                continue

            curated_posts.append(curated_post)

        curated_output = {
            'profile': curated_profile,
            'posts': curated_posts
        }

        logger.info(f"Curated Instagram output generated for {username}.")
        # logger.debug(f"Curated output data: {curated_output}") # Use debug level for potentially large data

        # Update Firestore document for the user (using the uid).
        logger.info(f"Attempting to update Firestore for uid: {uid} with insta_profile.")
        try:
            doc_ref = db.collection("users").document(uid)
            # Check if document exists
            logger.info(f"Checking existence of document: users/{uid}")
            doc = doc_ref.get()
            if not doc.exists:
                logger.error(f"Firestore document with uid {uid} does not exist. Cannot update insta_profile.")
                return None
            logger.info(f"Document users/{uid} exists. Updating with insta_profile.")
            doc_ref.update({"insta_profile": curated_output})
            logger.info(f"Firestore successfully updated for uid: {uid} with insta_profile.")
        except Exception as firestore_error:
            logger.error(f"Failed to update Firestore for uid {uid}: {firestore_error}")
            return None

        logger.info(f"scrape_instagram finished successfully for {username}, uid: {uid}.")
        return curated_output

    except Exception as e:
        logger.exception(f"An unexpected error occurred in scrape_instagram for {username}, uid: {uid}: {e}") # Log exception info
        return None


@timing_decorator
def scrape_linkedin_profile(linkedin_url, uid):
    """
    Scrapes a LinkedIn profile via Proxycurl and updates the Firestore document
    (identified by uid) with a new field "linkedin_profile" containing the scraped data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting scrape_linkedin_profile for url: {linkedin_url}, uid: {uid}")
    endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    
    if not PROXYCURL_API_KEY:
        logger.error("❌ ERREUR : PROXYCURL_API_KEY is not configured.")
        return {}
        
    try:
        logger.info(f"Calling Proxycurl endpoint: {endpoint} for url: {linkedin_url}")
        with httpx.Client() as client:
            response = client.get(
                endpoint,
                params={'url': linkedin_url, 'fallback_to_cache': 'on-error'},
                headers={'Authorization': f'Bearer {PROXYCURL_API_KEY}'},
                timeout=10
            )

        logger.info(f"Proxycurl response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f'❌ LinkedIn scrape error {response.status_code}: {response.text}')
            return {}

        logger.info(f'✅ Successfully scraped LinkedIn profile: {linkedin_url}')
        result = response.json()

        # Update Firestore document for the user with the linkedin_profile field.
        logger.info(f"Attempting to update Firestore for uid: {uid} with linkedin_profile.")
        try:
            doc_ref = db.collection("users").document(uid)
            # Check if document exists
            logger.info(f"Checking existence of document: users/{uid}")
            doc = doc_ref.get()
            if not doc.exists:
                logger.error(f"Firestore document with uid {uid} does not exist. Cannot update linkedin_profile.")
                return {}
            logger.info(f"Document users/{uid} exists. Updating with linkedin_profile.")
            doc_ref.update({"linkedin_profile": result})
            logger.info(f"Firestore successfully updated for uid: {uid} with linkedin_profile.")
        except Exception as e:
            logger.error(f"Failed to update Firestore for uid {uid}: {e}")
            return {}

        logger.info(f"scrape_linkedin_profile finished successfully for {linkedin_url}, uid: {uid}.")
        return result

    except httpx.TimeoutException:
        logger.error(f'🚨 Timeout exception while scraping LinkedIn profile: {linkedin_url}')
        return {}
    except httpx.RequestError as e:
        logger.exception(f'🚨 Request exception while scraping LinkedIn profile: {e}') # Log exception info
        return {}
    except Exception as e:
        logger.exception(f"An unexpected error occurred in scrape_linkedin_profile for {linkedin_url}, uid: {uid}: {e}") # Log exception info
        return {}

@timing_decorator
def enrich_person_data(first_name: str, last_name: str, school: str, uid: str):
    """
    Calls the People Data Labs API to enrich a person's data based on first name, last name,
    and school. It builds a curated dictionary with the following keys:
    
      - full_name, sex, linkedin_url, linkedin_username, facebook_username, twitter_username,
        job_title, job_title_role, job_title_levels, job_company_name,
        job_company_location_locality, job_company_location_country, location_country, skills,
      - experience: a list of dicts with keys company_name, company_location_locality,
        company_location_country, start_date, end_date, title_name,
      - education: a list of dicts with keys school_name, school_type, school_location_locality,
        degrees, majors, minors, gpa.
        
    The function also updates the Firestore document (identified by uid) with the new field 
    "linkedin_profile".
    
    Returns:
        A tuple: (curated_data, linkedin_found)
        linkedin_found is a boolean indicating whether a LinkedIn URL was found.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting enrich_person_data for: {first_name} {last_name}, school: {school}, uid: {uid}")
    url = "https://api.peopledatalabs.com/v5/person/enrich?pretty=false&min_likelihood=2&include_if_matched=false&titlecase=false"
    
    if not PDL_API_KEY:
        logger.error("❌ ERREUR : PDL_API_KEY is not configured.")
        return False # Return False as linkedin_found indication
        
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Key": PDL_API_KEY
    }
    
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "school": school
    }
    
    logger.info(f"Calling PDL enrich API: {url}")
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=10 # Added 30 second timeout
        )
        logger.info(f"PDL API response status: {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error(f"🚨 Timeout exception while calling PDL API for {first_name} {last_name}")
        return False # Indicate failure/no linkedin found
    except requests.RequestException as req_err:
        logger.exception(f"🚨 PDL API request failed: {req_err}")
        return False # Indicate failure/no linkedin found
    
    if response.status_code == 200:
        logger.info("PDL API call successful.")
        try:
            json_response = response.json()
            data = json_response.get("data", {})
            
            linkedin_url = data.get("linkedin_url")
            linkedin_found = bool(linkedin_url)
            logger.info(f"PDL enrichment found LinkedIn URL: {linkedin_found} ({linkedin_url or 'N/A'})")
            
            logger.info("Curating PDL data...")
            curated_data = {
                "full_name": data.get("full_name"),
                "sex": data.get("sex"),
                "linkedin_url": data.get("linkedin_url"),
                "linkedin_username": data.get("linkedin_username"),
                "facebook_username": data.get("facebook_username"),
                "twitter_username": data.get("twitter_username"),
                "job_title": data.get("job_title"),
                "job_title_role": data.get("job_title_role"),
                "job_title_levels": data.get("job_title_levels"),
                "job_company_name": data.get("job_company_name"),
                "job_company_location_locality": data.get("job_company_location_locality"),
                "job_company_location_country": data.get("job_company_location_country"),
                "location_country": data.get("location_country"),
                "skills": data.get("skills")
            }
            
            # Process experience: extract only the required fields.
            experience_list = []
            for exp in data.get("experience", []):
                exp_item = {
                    "company_name": exp.get("company", {}).get("name"),
                    "company_location_locality": exp.get("company", {}).get("location", {}).get("locality"),
                    "company_location_country": exp.get("company", {}).get("location", {}).get("country"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "title_name": exp.get("title", {}).get("name")
                }
                experience_list.append(exp_item)
            curated_data["experience"] = experience_list
            
            # Process education: extract only the required fields.
            education_list = []
            for edu in data.get("education", []):
                school_obj = edu.get("school", {}) if edu.get("school") else {}
                edu_item = {
                    "school_name": school_obj.get("name"),
                    "school_type": school_obj.get("type"),
                    "school_location_locality": school_obj.get("location", {}).get("locality"),
                    "degrees": edu.get("degrees"),
                    "majors": edu.get("majors"),
                    "minors": edu.get("minors"),
                    "gpa": edu.get("gpa")
                }
                education_list.append(edu_item)
            curated_data["education"] = education_list
            logger.info("PDL data curated.")

            logger.info(f"Attempting to update Firestore for uid: {uid} with PDL linkedin_profile data.")
            try:
                doc_ref = db.collection("users").document(uid)
                # Check if document exists
                logger.info(f"Checking existence of document: users/{uid}")
                doc = doc_ref.get()
                if not doc.exists:
                    logger.error(f"Firestore document with uid {uid} does not exist. Cannot update linkedin_profile from PDL.")
                    # Decide if you should still return linkedin_found = True/False here
                    return linkedin_found # Or maybe False since update failed?
                logger.info(f"Document users/{uid} exists. Updating with linkedin_profile from PDL.")
                doc_ref.update({"linkedin_profile": curated_data})
                logger.info(f"Firestore successfully updated for uid: {uid} with PDL linkedin_profile data.")
            except Exception as e:
                logger.error(f"Failed to update Firestore for uid {uid} with PDL data: {e}")
                # Return linkedin_found status even if Firestore update fails, as enrichment itself worked
                return linkedin_found

            logger.info(f"enrich_person_data finished successfully for {first_name} {last_name}, uid: {uid}. LinkedIn found: {linkedin_found}")
            return linkedin_found
        except Exception as e:
             logger.exception(f"Error processing PDL response or updating Firestore for {first_name} {last_name}, uid: {uid}: {e}")
             # Decide return value. PDL call was 200, but processing failed. Let's indicate no linkedin found.
             return False
    else:
        logger.error(f"PDL API call failed. Status: {response.status_code}, Message: {response.text}")
        return False # Indicate failure/no linkedin found


def LLM_profile_generation(username: str, academic_advisor: str, year: str, university: str, faculty: str, major: str, minor: str):
    logger = logging.getLogger(__name__)
    logger.info("Starting LLM_profile_generation.")
    logger.info(f"Input - username: {username}, advisor: {academic_advisor}, year: {year}, university: {university}, faculty: {faculty}, major: {major}, minor: {minor}")

    # print("\n")
    # print("\n")
    # print(f"Profiling of the user")
    # print(f"username: {username}, year: {year}, university: {university}, School: {faculty}, major: {major}, minor: {minor}, academic_advisor: {academic_advisor}")

    try:
        student_profile = f"My name is {username}. I am enrolled at {university} in the {faculty} school. I am majoring in {major} and minoring in {minor}. Currently in my {year} year, I am guided by academic advisor: {academic_advisor}."
        logger.info("Generated student profile string.")
        # logger.debug(f"Generated profile: {student_profile}")
        return student_profile
    except Exception as e:
        logger.exception(f"Error during LLM_profile_generation: {e}") # Log exception info
        # print(e)
        return None # Return None or raise exception on error
