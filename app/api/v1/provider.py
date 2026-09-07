from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.providers.contracts import GenerationRequest
from app.services.generation_router import GenerationRouter

router = APIRouter(prefix="/generation", tags=["generation-routing"])

class RoutePreviewRequest(BaseModel):
    operation: str = Field(min_length=1)
    prompt: str = Field(min_length=1, max_length=10000)
    media_urls: list[str] = []
    model: str | None = None
    duration_seconds: int | None = Field(default=None, ge=1, le=300)
    aspect_ratio: str = "9:16"

@router.post("/route-preview")
async def route_preview(body: RoutePreviewRequest):
    try:
        req = GenerationRequest(**body.model_dump())
        decision = GenerationRouter().choose(req)
        return decision.__dict__
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
