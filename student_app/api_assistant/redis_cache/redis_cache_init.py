import redis
import os

# Connexion à Redis
def get_redis_client():
    return redis.Redis(
        host=os.getenv('REDIS_HOST', '127.0.0.1'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )

# Récupérer le thread_id depuis Redis
def get_thread_id_from_cache(redis_client, chat_id):
    return redis_client.get(chat_id)

# Sauvegarder le thread_id dans Redis avec expiration
def save_thread_id_to_cache(redis_client, chat_id, thread_id, expiration=3600):
    redis_client.setex(chat_id, expiration, thread_id)