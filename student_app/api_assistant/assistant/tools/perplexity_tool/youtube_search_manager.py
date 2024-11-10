import os
import aiohttp
import asyncio
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

async def get_youtube_videos(search_query, input_message):
    logging.info(f"YouTube API for query '{search_query}' for {input_message}.")
    GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY')
    URL = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={search_query}&type=video&key={GOOGLE_CLOUD_API_KEY}'
    
    videos = []  # Initialize an empty list to store video details

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                if response.status == 200:
                    logging.info(f"Successfully retrieved data from YouTube API for query '{search_query}' for {input_message}.")
                    data = await response.json()
                    for item in data.get('items', []):
                        video_id = item['id'].get('videoId')
                        if video_id:
                            title = item['snippet'].get('title', 'No title')
                            video_url = f'https://www.youtube.com/watch?v={video_id}'
                            videos.append({"title": title, "link": video_url})
                            logging.info(f"Video found: '{title}' - {video_url} for {input_message}")
                        else:
                            logging.warning(f"Video ID not found in response item. for {input_message}")
                else:
                    logging.error(f"Error {response.status}: Failed to retrieve data from YouTube API for query '{search_query}' for {input_message}.")
    except aiohttp.ClientError as e:
        logging.error(f"Client error occurred: {e} for {input_message}")
    except asyncio.TimeoutError:
        logging.error(f"Request timed out. for {input_message}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e} for {input_message}")

    return videos

