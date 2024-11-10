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
        "profilePicUrlHD": "https://scontent-iad3-2.cdninstagram.com/v/t51.2885-19/228301094_346165107054059_1707756379427772474_n.jpg?stp=dst-jpg_s320x320&_nc_ht=scontent-iad3-2.cdninstagram.com&_nc_cat=111&_nc_ohc=GxwY3uSTanoQ7kNvgEC5qIq&_nc_gid=1550b97cb65b4667bf8d3ee9bc81ca31&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AYAiu9W4h5YFLllAnaKIhXD22dheiN4KxahtP-v36o1CsA&oe=6736B243&_nc_sid=8b3546",
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
