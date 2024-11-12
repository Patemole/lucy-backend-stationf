import logging

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

input_dat_admission = [
    {
        "searchSource": "threads",
        "inputUrl": "https://www.instagram.com/penngleeclub/",
        "username": "previewingpenn",
        "url": "https://www.instagram.com/previewingpenn?igsh=NXJoMmU2ejh0b2lp",
        "fullName": "Penn Admissions",
        "biography": "Official Instagram of Penn Undergraduate Admissions 💙  \n Visit our website to learn more! 👇 \n linktr.ee/previewingpenn",
        "followersCount": "26.3k",
        "highlightReelCount": 9,
        "joinedRecently": False,
        "profilePicUrlHD": "http://localhost:5001/static/academic_advisor/penn_admission_logo.png",
        "postsCount": "1,528"
    }
]

input_dat_research = [
    {
        "searchSource": "threads",
        "inputUrl": "https://www.instagram.com/previewingpenn/",
        "username": "previewingpenn",
        "url": "https://www.instagram.com/previewingpenn?igsh=NXJoMmU2ejh0b2lp",
        "fullName": "Penn Admissions",
        "biography": "Official Instagram of Penn Undergraduate Admissions 💙  \n Visit our website to learn more! 👇 \n linktr.ee/previewingpenn",
        "followersCount": "26.3k",
        "highlightReelCount": 9,
        "joinedRecently": False,
        "profilePicUrlHD": "http://localhost:5001/static/academic_advisor/penn_admission_logo.png",
        "postsCount": "1,528"
    }
]

def transform_instagram_data(query, input_message, data=input_dat_admission):
    transformed_data = []
    logging.info(f"Starting transformation of Instagram data. for {input_message}")

    for item in data:
        try:
            # Log the username being processed
            logging.info(f"Processing data for username: {item.get('username', 'N/A')} for {input_message}")

            # Construct the transformed item
            transformed_item = {
                "username": f"@{item['username']}",
                "title": item.get("fullName", ""),
                "link": item.get("inputUrl", ""),
                "picture": item.get("profilePicUrlHD", ""),
                "posts": str(item.get("postsCount", 0)),
                "followers": str(item.get("followersCount", 0))
                #TODO turn off for bio 
                #"biography": item.get("biography", "") 
            }
            
            # Append the transformed item to the list
            transformed_data.append(transformed_item)
            logging.info(f"Successfully transformed data for {transformed_item['username']} for {input_message}")

        except KeyError as e:
            logging.error(f"KeyError: Missing key {e} in item: {item} for {input_message}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing item: {e} for {input_message}")

    logging.info(f"Transformation of Instagram data completed. {input_message}")
    return transformed_data
