import hashlib
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from  app.core.config import settings


def _hash_token(token: str)-> str:
    """ Never store raw - store SHA-256 hash only """
    return hashlib.sha256(token.encode()).hexdigest()


class RefreshTokenRepo:
    def __init__(self, db: AsyncSession):
        self.db = db


# -------------------------------------------------------------------------
# SAVE — called on login
# -------------------------------------------------------------------------


    async def save(self, user_id: int, company_id: int, token: str) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        record = RefreshToken(
            user_id = user_id,
            company_id = company_id,
            token_hash = _hash_token(token),
            is_revoked = False,
            expires_at = expires_at,
        )
        self.db.add(record)
        await self.db.commit()







# -------------------------------------------------------------------------
    # VALIDATE — called on refresh
# -------------------------------------------------------------------------

    async def validate(self, token: str) -> RefreshToken | None:
        """Return the token record if valid and not revoked, else None."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == _hash_token(token),
                RefreshToken.is_revoked  == False,
                RefreshToken.expires_at   > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()
    
    
    
    # -------------------------------------------------------------------------
    # ROTATE — revoke old, save new (called on refresh)
    # -------------------------------------------------------------------------
    async def rotate(self, old_token: str, new_token: str, user_id: int, company_id: int) -> None:
        """Revoke old token"""

        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == _hash_token(old_token))
            .values(is_revoked=True)
        )  
        await self.db.commit()
        await self.save(user_id, company_id, new_token)

    # -----------------------------------------
    # ------------------------------------------
    # REVOKE ALL — called on logout
    # -------------------------------------------------------------------------



    async def revoke_all(self, user_id: int) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
            .values(is_revoked=True)
        )

        await self.db.commit()

