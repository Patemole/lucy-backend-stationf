import os
import sys
import logging
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import resend
from dotenv import load_dotenv
import json
import time

# --- Initial Setup ---

# Add parent directory to sys.path if necessary (adjust based on your structure)
# parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\'))
# if parent_dir not in sys.path:
#     sys.path.append(parent_dir)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("feedback_scheduler.log")
    ]
)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()

# --- Firebase Initialization ---
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
firebase_credentials_paths = {
    "dev": "../firestore_credentials/firebase_credentials_dev.json",
    "preprod": "../firestore_credentials/firebase_credentials_preprod.json",
    "prod": "../firestore_credentials/firebase_credentials_prod.json"
}

# If running in GitHub Actions or similar, credentials might be passed as a JSON string
firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
if firebase_credentials_json:
    logger.info("Loading Firebase credentials from FIREBASE_CREDENTIALS_JSON environment variable.")
    try:
        cred_dict = json.loads(firebase_credentials_json)
        cred = credentials.Certificate(cred_dict)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error creating certificate from JSON credentials: {e}")
        sys.exit(1)
else:
    # Fallback to using file path based on ENVIRONMENT
    logger.info(f"FIREBASE_CREDENTIALS_JSON not found. Loading credentials from file path for env: {ENVIRONMENT}.")
    cred_path = firebase_credentials_paths.get(ENVIRONMENT)
    if not cred_path or not os.path.exists(cred_path):
        logger.error(f"❌ Firebase credentials path not found or invalid for env {ENVIRONMENT} at {cred_path}")
        sys.exit(1)
    try:
        cred = credentials.Certificate(cred_path)
    except Exception as e:
        logger.error(f"❌ Error creating certificate from file path {cred_path}: {e}")
        sys.exit(1)

# Initialize the app using the created credentials object
try:
    # Check if the default app already exists before initializing
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    else:
        logger.info("Firebase Admin SDK already initialized.")
    db = firestore.client()
except Exception as e:
    logger.exception(f"🚨 Failed to initialize Firebase Admin SDK with provided credentials: {e}")
    sys.exit(1) # Exit if Firebase fails to initialize
# --- End Firebase Initialization ---

# Resend Initialization
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    logger.error("❌ RESEND_API_KEY is not configured in .env")
    sys.exit(1) # Exit if Resend key is missing
resend.api_key = RESEND_API_KEY
FROM_EMAIL = "mathieu.perez@my-lucy.com" # Or your preferred sender email

# --- Core Logic ---

def send_feedback_emails():
    """
    Finds users created exactly one week ago and sends them a feedback email.
    """
    logger.info("🚀 Starting feedback email process...")
    emails_sent_count = 0
    users_processed_count = 0

    try:
        # Calculate the date range for exactly one week ago (UTC)
        now_utc = datetime.now(timezone.utc)
        one_week_ago_date = (now_utc - timedelta(days=7)).date()
        start_of_target_day_utc = datetime.combine(one_week_ago_date, datetime.min.time(), tzinfo=timezone.utc)
        end_of_target_day_utc = start_of_target_day_utc + timedelta(days=1)

        logger.info(f"🎯 Targeting users created between {start_of_target_day_utc} and {end_of_target_day_utc} (UTC)")

        # Query Firestore for users created within the target date range
        users_ref = db.collection("users")
        # Note: Ensure you have a Firestore index on `createdAt` for this query
        query = users_ref.where(filter=firestore.FieldFilter("createdAt", ">=", start_of_target_day_utc)).where(filter=firestore.FieldFilter("createdAt", "<", end_of_target_day_utc))

        eligible_users_stream = query.stream()

        for user_snapshot in eligible_users_stream:
            users_processed_count += 1
            user_data = user_snapshot.to_dict()
            user_id = user_snapshot.id
            user_email = user_data.get("email")
            user_name = user_data.get("name", "there") # Fallback name

            if not user_email:
                logger.warning(f"🤷 User {user_id} missing email address. Skipping.")
                continue
                
            # --- Check if feedback email was already sent (Optional but recommended) ---
            # Uncomment and adapt if you add a 'feedbackEmailSentAt' field
            # if user_data.get("feedbackEmailSentAt"):
            #     logger.info(f"📨 Feedback email already sent to {user_email} ({user_id}). Skipping.")
            #     continue
            # -----------------------------------------------------------------------

            logger.info(f"✅ Found eligible user: {user_email} ({user_id})")

            # Compose Email - Updated Content (Less Formal, More Engaging)
            subject = "Your thoughts on Lucy? (from a fellow student)"
            html_body = f"""
            <html>
            <body>
                <p>Hey {user_name}!</p>
                <p>I am Mathieu, co-founder & CEO of Lucy (and a UPenn senior). Saw you gave Lucy a try last week - would love to know what you thought?</p>
                <p>Building this thing takes lots of work, and honest feedback from users like you is gold. Seriously, it helps us figure out what to build next.</p>
                <p>I you have 15 mins for a super quick chat sometime? No pressure, just your real thoughts!</p>
                <p>Grab a time here if you're free:</p>
                <p><a href="https://calendly.com/mathieu-perez-my-lucy/15min-feedback">Book a 15-min Call</a></p>
                <p>If not, no worries! Even a quick reply here with a thumbs up/down or a random thought would be awesome.</p>
                <p>Cheers,</p>
                <p>Mathieu Perez<br/>Co-founder & CEO, Lucy</p>
            </body>
            </html>
            """

            # Send Email via Resend
            try:
                logger.info(f"📤 Attempting to send feedback email to {user_email}...")
                response = resend.Emails.send({
                    "from": FROM_EMAIL,
                    "to": [user_email],
                    "subject": subject,
                    "html": html_body
                })
                logger.info(f"✅ Email sent successfully to {user_email}. Resend ID: {response.get('id')}")
                emails_sent_count += 1
                
                # --- Update user document (Optional but recommended) ---
                # Uncomment to mark email as sent
                # try:
                #     users_ref.document(user_id).update({"feedbackEmailSentAt": firestore.SERVER_TIMESTAMP})
                #     logger.info(f"📝 Marked user {user_id} as feedback email sent.")
                # except Exception as update_err:
                #     logger.error(f"🚨 Failed to update user {user_id} after sending email: {update_err}")
                # -------------------------------------------------------

            except Exception as email_error:
                logger.error(f"🚨 Failed to send email to {user_email} ({user_id}): {email_error}")

            # --- Add Rate Limiting Delay ---
            time.sleep(2) # Sleep for 600ms to stay below 2 requests/second limit
            # ------------------------------

    except Exception as e:
        logger.exception(f"🚨 An unexpected error occurred during the feedback email process: {e}")

    logger.info(f"🏁 Feedback email process finished. Processed {users_processed_count} users from the target day. Sent {emails_sent_count} emails.")

# --- Script Execution ---

if __name__ == "__main__":
    logger.info("Running feedback email scheduler script...")
    send_feedback_emails()
    logger.info("Script finished.") 