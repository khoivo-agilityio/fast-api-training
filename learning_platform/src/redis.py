"""
Redis — Async client and token blacklist helpers.

Used for JWT token blacklisting (logout) and optional caching.
All Redis operations use async/await.
"""

from redis.asyncio import Redis

from src.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the blacklist with a TTL matching the token's expiry."""
    await redis_client.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a JWT ID has been blacklisted."""
    return await redis_client.exists(f"blacklist:{jti}") > 0
