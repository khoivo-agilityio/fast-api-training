"""Async Redis client and token blacklist helpers."""

from redis.asyncio import Redis

from src.config import settings

_redis_client: Redis | None = None

TOKEN_BLACKLIST_PREFIX = "blacklist:"
REFRESH_TOKEN_PREFIX = "refresh:"


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    client = await get_redis()
    await client.setex(f"{TOKEN_BLACKLIST_PREFIX}{token}", ttl_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    client = await get_redis()
    return await client.exists(f"{TOKEN_BLACKLIST_PREFIX}{token}") == 1


async def store_refresh_token(user_id: str, token: str, ttl_seconds: int) -> None:
    client = await get_redis()
    await client.setex(f"{REFRESH_TOKEN_PREFIX}{user_id}", ttl_seconds, token)


async def get_stored_refresh_token(user_id: str) -> str | None:
    client = await get_redis()
    return await client.get(f"{REFRESH_TOKEN_PREFIX}{user_id}")


async def delete_refresh_token(user_id: str) -> None:
    client = await get_redis()
    await client.delete(f"{REFRESH_TOKEN_PREFIX}{user_id}")
