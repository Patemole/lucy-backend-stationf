import requests
import os
import json

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')


# Function to search for images using Google Custom Search JSON API and save locally
def google_image_search(query, num_images=3):
    # Your Google Custom Search API key
    API_KEY = GOOGLE_API_KEY
    
    # Your Custom Search Engine ID
    SEARCH_ENGINE_ID = 'c43aac779112b4278'
    
    # Google Custom Search JSON API endpoint
    url = "https://www.googleapis.com/customsearch/v1"
    
    # Search parameters
    params = {
        'q': query,  # The search query (student's input)
        'cx': SEARCH_ENGINE_ID,  # Custom Search Engine ID
        'key': API_KEY,  # API Key
        'searchType': 'image',  # We are specifically searching for images
        'fileType': 'png',  # Specify PNG format
        'num': num_images,  # Number of images to return
        #'safe': 'active'  # Safe search filter
    }
    
    # Make the request to the API
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Create a list to hold all the image results
        image_results = []
        
        current_directory = os.path.dirname(os.path.abspath(__file__))
    
        # Define the folder where images will be saved inside the 'perplexity_tool' folder
        save_folder = os.path.join(current_directory, 'downloaded_images')
        
        # Ensure the folder to save images exists
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        # Iterate over each result to create the JSON object for each image
        if 'items' in data:
            for i, item in enumerate(data['items']):
                image_url = item['link']  # Get the image URL
                image_filename = f"image_{i+1}.png"  # Create a filename
                
                # Download the image
                image_data = requests.get(image_url).content
                local_path = os.path.join(save_folder, image_filename)  # Local file path
                
                # Save the image to the local folder
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                
                # Create the JSON output for each image, using the local path
                result = {
                    "image_id": f"img{i+1}",  # Dynamic image ID
                    "image_url": local_path,  # Local file path instead of web URL
                    "image_description": ""  # Fixed value
                }
                image_results.append(result)
                
            return image_results  # Return the list of JSON objects as a JSON string
        
        else:
            return "No images found"
    else:
        return f"Error: {response.status_code}, {response.text}"