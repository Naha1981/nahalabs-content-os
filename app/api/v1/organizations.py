from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Membership, Organization, User
from app.schemas.common import OrganizationCreate, OrganizationOut

router = APIRouter(prefix='/organizations', tags=['organizations'])


@router.post('', response_model=OrganizationOut, status_code=201)
async def create_organization(payload: OrganizationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    existing = await db.scalar(select(Organization).where(Organization.slug == payload.slug))
    if existing:
        raise HTTPException(409, 'Organization slug already exists')
    org = Organization(name=payload.name, slug=payload.slug)
    db.add(org)
    await db.flush()
    db.add(Membership(organization_id=org.id, user_id=user.id, role='owner'))
    await db.commit()
    await db.refresh(org)
    return org


@router.get('', response_model=list[OrganizationOut])
async def list_organizations(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    result = await db.execute(
        select(Organization).join(Membership, Membership.organization_id == Organization.id).where(Membership.user_id == user.id)
    )
    return list(result.scalars().all())
