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

# Sample input data for LinkedIn profiles
input_data = [
    {
        "name": "Anne Duchene",
        "picture": "https://media.licdn.com/dms/image/v2/C4E03AQEdJCKHyIiWyA/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1663636910616?e=1736985600&v=beta&t=2YqBhWfviiQG_wOSURkhp8Qbs2O5GHQQqBezyIJhAg4",
        "headline": "https://media.licdn.com/dms/image/v2/D4E16AQFgK-lKx4ZMow/profile-displaybackgroundimage-shrink_350_1400/profile-displaybackgroundimage-shrink_350_1400/0/1698073166590?e=1736985600&v=beta&t=w5cTRMPSnS0KusfcEx961MQnzJF_vwdLfEZHqnnUrlc",
        "sentence": "ECON teacher",
        "link": "https://www.linkedin.com/in/guy-lorenzotti/"
    }
]

def transform_linkedin_profiles_data(query, input_message, data=input_data):
    transformed_data = []
    logging.info(f"Starting transformation of LinkedIn profiles data for query '{query}' and message '{input_message}'")

    for item in data:
        try:
            # Log the name being processed
            logging.info(f"Processing LinkedIn profile for name: {item.get('name', 'N/A')} with query '{query}'")

            # Construct the transformed item
            transformed_item = {
                "name": item.get("name", ""),
                "picture": item.get("picture", ""),
                "headline": item.get("headline", ""),
                "sentence": item.get("sentence", ""),
                "link": item.get("link", "")
            }
            
            # Append the transformed item to the list
            transformed_data.append(transformed_item)
            logging.info(f"Successfully transformed LinkedIn profile for {transformed_item['name']} with query '{input_message}'")

        except KeyError as e:
            logging.error(f"KeyError: Missing key {e} in item: {item} with query '{query}' and message '{input_message}'")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing item: {e} with query '{query}' and message '{input_message}'")

    logging.info(f"Transformation of LinkedIn profiles data completed for query '{query}' and message '{input_message}'")
    return transformed_data