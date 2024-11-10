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

    search_query="Anne duchene UPenn"
    SEARCH_URL = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={search_query}&type=video&key={GOOGLE_CLOUD_API_KEY}'
    
    videos = []  # Initialize an empty list to store video details

    try:
        async with aiohttp.ClientSession() as session:
            # First API Call: Search for videos
            async with session.get(SEARCH_URL) as search_response:
                if search_response.status == 200:
                    logging.info(f"Successfully retrieved data from YouTube API for query '{search_query}' for {input_message}.")
                    search_data = await search_response.json()
                    video_ids = [item['id']['videoId'] for item in search_data.get('items', []) if item['id'].get('videoId')]
                    
                    # Second API Call: Get statistics for each video
                    if video_ids:
                        stats_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={",".join(video_ids)}&key={GOOGLE_CLOUD_API_KEY}'
                        async with session.get(stats_url) as stats_response:
                            if stats_response.status == 200:
                                stats_data = await stats_response.json()
                                for item in stats_data.get('items', []):
                                    if len(videos) >= 2:
                                        break  # Limit to 2 items
                                    title = item['snippet'].get('title', 'No title')
                                    video_url = f'https://www.youtube.com/watch?v={item["id"]}'
                                    view_count = item['statistics'].get('viewCount', "0")
                                    
                                    videos.append({
                                        "title": title,
                                        "link": video_url,
                                        "miniature": "",  # Add a miniature URL if available
                                        "nbr_view": view_count
                                    })
                                    logging.info(f"Video found: '{title}' - {video_url}, Views: {view_count} for {input_message}")
                            else:
                                logging.error(f"Error {stats_response.status}: Failed to retrieve video statistics from YouTube API for {input_message}.")
                else:
                    logging.error(f"Error {search_response.status}: Failed to retrieve data from YouTube API for query '{search_query}' for {input_message}.")
    except aiohttp.ClientError as e:
        logging.error(f"Client error occurred: {e} for {input_message}")
    except asyncio.TimeoutError:
        logging.error(f"Request timed out. for {input_message}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e} for {input_message}")

    return videos
