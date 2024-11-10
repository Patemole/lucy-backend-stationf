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

input_data = [
    {
        "searchSource": "threads",
        "inputUrl": "https://www.instagram.com/penngleeclub/",
        "username": "penngleeclub",
        "url": "https://www.instagram.com/penngleeclub",
        "fullName": "Penn Glee Club",
        "biography": "The longest continually running glee club in the US & the oldest performing arts group at @uofpenn\n⬇️ Get tickets for Soirée (Nov 13-15th, 8pm) below!",
        "followersCount": 1548,
        "highlightReelCount": 9,
        "joinedRecently": False,
        "profilePicUrlHD": "http://localhost:5001/static/academic_advisor/insta_club.png",
        "postsCount": 331
    }
]

def transform_instagram_data(query, input_message, data=input_data):
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
