import requests
import httpx
import logging
import time
from google.cloud import firestore
import os

import firebase_admin
from firebase_admin import credentials, auth, firestore

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
firebase_admin.initialize_app(cred)
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
    
    try:
        # Poll the actor run status until it is finished.
        run_url = f'https://api.apify.com/v2/actor-runs/{ACTOR_RUN_ID}?token={APIFY_API_KEY}'
        logger.info("Waiting for actor run to complete...")
        while True:
            response = requests.get(run_url)
            run_data = response.json()
            status = run_data.get('data', {}).get('status')
            if status == 'SUCCEEDED':
                logger.info("Run completed successfully.")
                break
            elif status == 'FAILED':
                logger.error("Run failed.")
                return None
            logger.info("Run is still in progress. Waiting...")
            time.sleep(10)  # wait for 10 seconds before checking again

        # Retrieve the dataset items.
        dataset_url = f'https://api.apify.com/v2/datasets/{DATASET_ID}/items?token={APIFY_API_KEY}'
        logger.info("Fetching dataset items...")
        response = requests.get(dataset_url)
        data = response.json()

        # Filter results by the specified Instagram username.
        results = [item for item in data if item.get('username', '').lower() == username.lower()]
        if not results:
            logger.error(f"No data found for the username: {username}")
            return None

        profile_data = results[0]
        curated_profile = {
            'followersCount': profile_data.get('followersCount'),
            'followsCount': profile_data.get('followsCount'),
            'biography': profile_data.get('biography'),
            'fullName': profile_data.get('fullName'),
            'username': profile_data.get('username'),
            'inputUrl': profile_data.get('inputUrl'),
            'profilePicUrlHD': profile_data.get('profilePicUrlHD')
        }

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

        logger.info("Curated output:")
        logger.info(curated_output)

        # Update Firestore document for the user (using the uid).
        try:
            doc_ref = db.collection("users").document(uid)
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logger.error(f"Document with uid {uid} does not exist")
                return None
            doc_ref.update({"insta_profile": curated_output})
            logger.info("Firestore updated with insta_profile successfully.")
        except Exception as firestore_error:
            logger.error(f"Failed to update Firestore: {firestore_error}")
            return None

        return curated_output

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


@timing_decorator
def scrape_linkedin_profile(linkedin_url, uid):
    """
    Scrapes a LinkedIn profile via Proxycurl and updates the Firestore document
    (identified by uid) with a new field "linkedin_profile" containing the scraped data.
    """
    endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    try:
        with httpx.Client() as client:
            response = client.get(
                endpoint,
                params={'url': linkedin_url, 'fallback_to_cache': 'on-error'},
                headers={'Authorization': f'Bearer {PROXYCURL_API_KEY}'},
                timeout=10
            )

        if response.status_code != 200:
            logging.error(f'❌ LinkedIn scrape error {response.status_code}: {response.text}')
            return {}

        logging.info(f'✅ Successfully scraped LinkedIn profile: {linkedin_url}')
        result = response.json()

        # Update Firestore document for the user with the linkedin_profile field.
        try:
            doc_ref = db.collection("users").document(uid)
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logging.error(f"Document with uid {uid} does not exist")
                return {}
            doc_ref.update({"linkedin_profile": result})
            logging.info("Firestore updated with linkedin_profile successfully.")
        except Exception as e:
            logging.error(f"Failed to update Firestore: {e}")
            return {}

        return result

    except httpx.RequestError as e:
        logging.error(f'🚨 Request exception while scraping LinkedIn profile: {e}')
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
    url = "https://api.peopledatalabs.com/v5/person/enrich?pretty=false&min_likelihood=2&include_if_matched=false&titlecase=false"
    
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
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        json_response = response.json()
        data = json_response.get("data", {})
        
        linkedin_found = bool(data.get("linkedin_url"))
        
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

        try:
            doc_ref = db.collection("users").document(uid)
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logging.error(f"Document with uid {uid} does not exist")
                return {}
            doc_ref.update({"linkedin_profile": curated_data})
            logging.info("Firestore updated with linkedin_profile successfully.")
        except Exception as e:
            logging.error(f"Failed to update Firestore: {e}")
            return {}

        return curated_data, linkedin_found
    else:
        error_data = {"error": response.status_code, "message": response.text}
        return error_data, False



def LLM_profile_generation(username: str, academic_advisor: str, year: str, university: str, faculty: str, major: str, minor: str):

    print("\n")
    print("\n")
    print(f"Profiling of the user")
    print(f"username: {username}, year: {year}, university: {university}, School: {faculty}, major: {major}, minor: {minor}, academic_advisor: {academic_advisor}")

    try:
        student_profile = f"My name is {username}. I am enrolled at {university} in the {faculty} school. I am majoring in {major} and minoring in {minor}. Currently in my {year} year, I am guided by academic advisor: {academic_advisor}."
        return student_profile
    except Exception as e:
        print(e)


def main():
    # modify these variables for testing
    test_username = 'holyfamilyu'
    test_uid = '07rS7v9k5YYdLRDOX9gxKI7M29L2'
    test_linkedin_url = 'linkedin.com/in/mathieu-perez-719019201'

    # Test Firebase connection first
    try:
        print(f"\nTesting Firebase connection...")
        print(f"Environment: {ENVIRONMENT}")
        print(f"Credentials path: {cred_path}")
        
        # Try to list all documents in users collection
        users_ref = db.collection('users')
        docs = users_ref.stream()
        print("\nAvailable user documents:")
        for doc in docs:
            print(f"Document ID: {doc.id}")
            
        # Try to get specific document
        doc_ref = db.collection('users').document(test_uid)
        doc = doc_ref.get()
        if doc.exists:
            print(f"\nFound test document: {test_uid}")
            print(f"Document data: {doc.to_dict().keys()}")
        else:
            print(f"\nTest document not found: {test_uid}")
            
    except Exception as e:
        print(f"Firebase test failed: {str(e)}")

    # call the instagram scrape function
    print("\nTesting Instagram scraping...")
    insta_result = scrape_instagram(test_username, test_uid)
    if insta_result is not None:
        print("✅ Instagram scraping and Firebase update successful")
    else:
        print("❌ Instagram scraping or Firebase update failed")

    # call the linkedin scrape function
    print("\nTesting LinkedIn scraping...")
    linkedin_result = enrich_person_data("mathieu", "perez", "university of Pennsylvania", test_uid)
    if linkedin_result:  # Check if the result is not an empty dict
        print("✅ LinkedIn scraping and Firebase update successful")
    else:
        print("❌ LinkedIn scraping or Firebase update failed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()