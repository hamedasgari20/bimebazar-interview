import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()


class RedisManager:
    def __init__(self):
        self._redis = aioredis.Redis(
            host=settings.REDIS_URL,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB_NUMBER,
            password=settings.REDIS_PASSWORD
        )

    async def get(self, key):
        value = await self._redis.get(key)
        return value

    async def set(self, key, value, *args, **kwargs):
        await self._redis.set(key, value, *args, **kwargs)

    async def delete(self, key):
        await self._redis.delete(key)

    async def publish(self, channel, message, **kwargs):
        await self._redis.publish(channel, message, **kwargs)

    def create_pubsub(self, **kwargs):
        return self._redis.pubsub(**kwargs)

    async def subscribe(self, pubsub, channel):
        await pubsub.subscribe(channel)

    async def unsubscribe(self, pubsub, channel):
        await pubsub.unsubscribe(channel)
