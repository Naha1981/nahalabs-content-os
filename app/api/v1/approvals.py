import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import ApprovalGrant, Business, User
from app.schemas.publishing import ApprovalCreate, ApprovalResponse
from app.services.tenant import require_membership

router = APIRouter(prefix='/approvals', tags=['approvals'])

@router.post('', response_model=ApprovalResponse, status_code=201)
async def create_approval(business_id: uuid.UUID, body: ApprovalCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {'owner','admin','editor'}: raise HTTPException(403, 'Insufficient permission')
    grant = ApprovalGrant(business_id=business.id, granted_by_user_id=user.id, scope=body.scope, allowed_platforms=body.allowed_platforms, allowed_content_types=body.allowed_content_types, expires_at=body.expires_at)
    db.add(grant); await db.commit(); await db.refresh(grant)
    return ApprovalResponse.model_validate(grant, from_attributes=True)

@router.get('', response_model=list[ApprovalResponse])
async def list_approvals(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(select(ApprovalGrant).where(ApprovalGrant.business_id == business.id).order_by(ApprovalGrant.created_at.desc()))
    return [ApprovalResponse.model_validate(x, from_attributes=True) for x in result.scalars()]

@router.post('/{approval_id}/revoke', response_model=ApprovalResponse)
async def revoke(approval_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    grant = await db.get(ApprovalGrant, approval_id)
    if not grant: raise HTTPException(404, 'Approval not found')
    business = await db.get(Business, grant.business_id); await require_membership(db, user.id, business.organization_id)
    grant.revoked_at = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    await db.commit(); await db.refresh(grant)
    return ApprovalResponse.model_validate(grant, from_attributes=True)
