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
        "like_count": 59141,
        "comment_count": 321,
        "play_count": 271373,
        "username": "noahschnapp",
        "url": "https://scontent-atl3-1.cdninstagram.com/o1/v/t16/f2/m69/AQPDxlPP0g_kp6VbnPznB41oezslnSwfVpC8KDKmQKLqdYPMh55t4hMFiyO0NItj3MUY2kWH9T8DZMM0RXGdKceU.mp4?efg=eyJ4cHZfYXNzZXRfaWQiOjE1Nzg3ODIyMTkxNjE3MzMsInZlbmNvZGVfdGFnIjoieHB2X3Byb2dyZXNzaXZlLklOU1RBR1JBTS5DTElQUy5DMy40MzIuZGFzaF9iYXNlbGluZV8yX3YxIn0&_nc_ht=scontent-atl3-1.cdninstagram.com&_nc_cat=101&strext=1&vs=f54728c5aadd3fd8&_nc_vs=HBksFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HUGc2NnctekRTaERJVG9DQUUwYm1rV3VNaGNSYnFfRUFBQUYVAALIAQAVAhg6cGFzc3Rocm91Z2hfZXZlcnN0b3JlL0dDXzdCQkRnZWREVGJXZ0FBSkNEaTJ3dFRKaERicV9FQUFBRhUCAsgBACgAGAAbAogHdXNlX29pbAExEnByb2dyZXNzaXZlX3JlY2lwZQExFQAAJorCzpWc-c0FFQIoAkMzLBdAPGZmZmZmZhgSZGFzaF9iYXNlbGluZV8yX3YxEQB1_gcA&ccb=9-4&oh=00_AYCINOCUpER3Dt7UNUKLv14ELA0lhE9zOTmFrM3ujv-UGA&oe=6732C2CA&_nc_sid=1d576d",
        "fullName": "Noah Schnapp",
        "video_duration": 28.4,
        "caption": "Congrats to @noahschnapp for getting into UPENN !#noahschnapp #tiktoo #college",
        "profile_pic_url": "https://scontent-atl3-1.cdninstagram.com/v/t51.2885-19/156856636_183566933265786_6924390351265028832_n.jpg?stp=dst-jpg_e0_s150x150&_nc_ht=scontent-atl3-1.cdninstagram.com&_nc_cat=1&_nc_ohc=1uivLsYL4_gQ7kNvgGP8TVx&_nc_gid=064b0cfc8a2d4e07bc40ef97939b2adf&edm=AL2I2h8BAAAA&ccb=7-5&oh=00_AYD2Pcy8tllxTMvDi9vQeN3x85Dk1S2A3d4g-o1uZAUOhA&oe=6736C891&_nc_sid=026283",
        "first_frame_url": "http://localhost:5001/static/academic_advisor/demo_reels.png"
    }
]

def transform_instagram_reels_data(query, input_message, data=input_data):
    transformed_data = []
    logging.info(f"Starting transformation of Instagram reels data for query '{query}' and message '{input_message}'")

    for item in data:
        try:
            # Log the username being processed
            logging.info(f"Processing reel data for username: {item.get('username', 'N/A')} with query '{query}'")

            # Construct the transformed item
            transformed_item = {
                "link": item.get("url", ""),
                "picture": item.get("first_frame_url", ""),
                "nbr_view": str(item.get("play_count", 0)),
                "title": item.get("caption", "")
            }
            
            # Append the transformed item to the list
            transformed_data.append(transformed_item)
            logging.info(f"Successfully transformed reel data for {transformed_item['username']} with query '{input_message}'")

        except KeyError as e:
            logging.error(f"KeyError: Missing key {e} in item: {item} with query '{query}' and message '{input_message}'")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing item: {e} with query '{query}' and message '{input_message}'")

    logging.info(f"Transformation of Instagram reels data completed for query '{query}' and message '{input_message}'")
    return transformed_data
