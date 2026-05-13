"""
Redis — Async client and token blacklist helpers.

Used for JWT token blacklisting (logout) and optional caching.
All Redis operations use async/await.

When REDIS_URL is not configured the module degrades gracefully:
  - blacklist_token  → silent no-op (token not stored)
  - is_token_blacklisted → always returns False (token treated as valid)
This means logout won't invalidate tokens across restarts, but the app
won't crash with a 500 on every authenticated request.
"""

import logging

from redis.asyncio import Redis

from src.config import settings

logger = logging.getLogger(__name__)

# Build the client lazily — None when REDIS_URL is not configured.
redis_client: Redis | None = (
    Redis.from_url(settings.REDIS_URL, decode_responses=True)
    if settings.REDIS_URL
    else None
)

if redis_client is None:
    logger.warning(
        "REDIS_URL is not set — token blacklisting disabled. "
        "Logout will not invalidate tokens until the server restarts."
    )


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the blacklist with a TTL matching the token's expiry."""
    if redis_client is None:
        return  # Degraded mode: no-op
    await redis_client.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a JWT ID has been blacklisted."""
    if redis_client is None:
        return False  # Degraded mode: treat all tokens as valid
    return await redis_client.exists(f"blacklist:{jti}") > 0
