"""
Auth Repository — BlacklistedToken queries.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import BlacklistedToken
from src.core.repository import BaseRepository


class BlacklistedTokenRepository(BaseRepository[BlacklistedToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(BlacklistedToken, session)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        result = await self.session.execute(
            select(BlacklistedToken).where(BlacklistedToken.jti == jti)
        )
        return result.scalar_one_or_none() is not None
