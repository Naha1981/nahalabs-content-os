import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Membership, User


async def get_user(db: AsyncSession, claims: dict) -> User:
    sub = claims['sub']
    email = claims.get('email') or f'{sub}@cognito.local'
    result = await db.execute(select(User).where(User.cognito_sub == sub))
    user = result.scalar_one_or_none()
    if not user:
        user = User(cognito_sub=sub, email=email, name=claims.get('name'))
        db.add(user)
        await db.flush()
    elif email and user.email != email:
        user.email = email
    return user


async def require_membership(db: AsyncSession, user_id: uuid.UUID, organization_id: uuid.UUID) -> Membership:
    result = await db.execute(
        select(Membership).where(Membership.user_id == user_id, Membership.organization_id == organization_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        from app.core.errors import forbidden
        raise forbidden()
    return membership
