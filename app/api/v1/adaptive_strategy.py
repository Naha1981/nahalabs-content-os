from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, ContentExperiment, User
from app.services.adaptive_strategy import build_adaptive_plan, choose_experiment_variant
from app.services.tenant import require_membership

router = APIRouter(prefix="/strategy", tags=["adaptive-strategy"])

@router.get("/businesses/{business_id}/adaptive-plan")
async def adaptive_plan(
    business_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    return await build_adaptive_plan(db, business_id, limit)

@router.get("/businesses/{business_id}/experiments/{experiment_id}/assignment")
async def assignment(
    business_id: uuid.UUID,
    experiment_id: uuid.UUID,
    sequence_number: int = Query(ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    experiment = await db.get(ContentExperiment, experiment_id)
    if not experiment or experiment.business_id != business_id:
        raise HTTPException(404, "Experiment not found")
    if experiment.status != "running":
        raise HTTPException(409, "Experiment is not running")
    variant = choose_experiment_variant(experiment, sequence_number)
    return {"experiment_id": str(experiment.id), "sequence_number": sequence_number, "assignment": variant,
            "configuration": experiment.control if variant == "control" else experiment.variant}
