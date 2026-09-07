from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, User
from app.services.content_intelligence import generate_content_intelligence_plan
from app.services.tenant import require_membership

router = APIRouter(prefix="/content-intelligence", tags=["content-intelligence"])

class IntelligencePlanRequest(BaseModel):
    asset_count: int = Field(default=10, ge=1, le=50)
    source_media_id: uuid.UUID | None = None

@router.post("/businesses/{business_id}/plan", status_code=201)
async def create_intelligence_plan(
    business_id: uuid.UUID,
    payload: IntelligencePlanRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    return await generate_content_intelligence_plan(
        db, business_id, payload.asset_count, payload.source_media_id, True
    )

@router.get("/businesses/{business_id}/preview")
async def preview_intelligence_plan(
    business_id: uuid.UUID,
    asset_count: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    # Preview uses the same engine but rolls back persistence.
    result = await generate_content_intelligence_plan(db, business_id, asset_count, None, False)
    return {**result, "preview": True}
