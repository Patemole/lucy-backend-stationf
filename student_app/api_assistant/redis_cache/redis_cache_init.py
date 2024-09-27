import redis
import os

# Connexion à Redis
# Connexion à Redis
def get_redis_client():
    print("Inside redis client cache")
    host = os.getenv('REDIS_HOST_PROD', '127.0.0.1')
    port = int(os.getenv('REDIS_PORT_PROD', 6379))

    print(f"Connecting to Redis at {host}:{port}")
    
    try:
        redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        print("Go for redis client")
        print("\n")
        print(redis_client)
        return redis_client
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        return None

    

# Récupérer le thread_id depuis Redis
def get_thread_id_from_cache(redis_client, chat_id):
    return redis_client.get(chat_id)

# Sauvegarder le thread_id dans Redis avec expiration
def save_thread_id_to_cache(redis_client, chat_id, thread_id, expiration=3600):
    redis_client.setex(chat_id, expiration, thread_id)