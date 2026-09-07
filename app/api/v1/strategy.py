from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, ContentExperiment, User
from app.services.strategy_context import build_strategy_context, strategy_directives
from app.services.tenant import require_membership

router = APIRouter(prefix="/strategy", tags=["strategy"])

class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(min_length=1)
    variable: str = Field(min_length=1, max_length=64)
    control: dict = Field(default_factory=dict)
    variant: dict = Field(default_factory=dict)
    min_sample_size: int = Field(default=20, ge=2, le=10000)

@router.get("/businesses/{business_id}/context")
async def context(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    result = await build_strategy_context(db, business_id)
    result["directives"] = strategy_directives(result)
    return result

@router.post("/businesses/{business_id}/experiments", status_code=201)
async def create_experiment(business_id: uuid.UUID, body: ExperimentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {"owner", "admin", "editor"}:
        raise HTTPException(403, "Insufficient permission")
    experiment = ContentExperiment(business_id=business_id, **body.model_dump())
    db.add(experiment)
    await db.commit(); await db.refresh(experiment)
    return experiment

@router.get("/businesses/{business_id}/experiments")
async def list_experiments(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business:
        raise HTTPException(404, "Business not found")
    await require_membership(db, user.id, business.organization_id)
    rows = (await db.execute(select(ContentExperiment).where(ContentExperiment.business_id == business_id).order_by(ContentExperiment.created_at.desc()))).scalars().all()
    return rows

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    experiment = await db.get(ContentExperiment, experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    business = await db.get(Business, experiment.business_id)
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {"owner", "admin", "editor"}:
        raise HTTPException(403, "Insufficient permission")
    if experiment.status not in {"planned", "paused"}:
        raise HTTPException(409, "Experiment cannot be started from its current state")
    experiment.status = "running"
    experiment.started_at = datetime.now(timezone.utc)
    await db.commit(); await db.refresh(experiment)
    return experiment
