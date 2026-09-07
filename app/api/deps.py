from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_claims
from app.db.session import get_db
from app.services.tenant import get_user


async def current_user(db: AsyncSession = Depends(get_db), claims: dict = Depends(get_current_claims)):
    user = await get_user(db, claims)
    await db.commit()
    return user


# Backward-compatible dependency name used by analytics/strategy routes.
get_current_user = current_user
