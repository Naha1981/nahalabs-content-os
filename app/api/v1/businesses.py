from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.errors import not_found
from app.db.session import get_db
from app.models import Business, User
from app.schemas.common import BusinessCreate, BusinessOut
from app.services.tenant import require_membership

router = APIRouter(prefix='/businesses', tags=['businesses'])


@router.post('', response_model=BusinessOut, status_code=201)
async def create_business(payload: BusinessCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await require_membership(db, user.id, payload.organization_id)
    business = Business(**payload.model_dump(mode='json'))
    db.add(business)
    await db.commit()
    await db.refresh(business)
    return business


@router.get('', response_model=list[BusinessOut])
async def list_businesses(organization_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    import uuid
    await require_membership(db, user.id, uuid.UUID(organization_id))
    result = await db.execute(select(Business).where(Business.organization_id == uuid.UUID(organization_id)))
    return list(result.scalars().all())


@router.get('/{business_id}', response_model=BusinessOut)
async def get_business(business_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    import uuid
    business = await db.get(Business, uuid.UUID(business_id))
    if not business:
        raise not_found('Business')
    await require_membership(db, user.id, business.organization_id)
    return business
