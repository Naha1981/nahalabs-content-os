import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.core.config import get_settings
from app.api.v1.organizations import router as organizations_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.media import router as media_router
from app.api.v1.content import router as content_router
from app.api.v1.social import router as social_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.generation import router as generation_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.publishing import router as publishing_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.strategy import router as strategy_router
from app.api.v1.adaptive_strategy import router as adaptive_strategy_router
from app.api.v1.content_intelligence import router as content_intelligence_router
from app.api.v1.provider import router as provider_router
from app.api.v1.quality import router as quality_router

settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.app_name, version='0.1.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://app.nahalabs.ai'],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'Idempotency-Key', 'X-Zernio-Signature'],
)

app.include_router(organizations_router, prefix=settings.api_prefix)
app.include_router(businesses_router, prefix=settings.api_prefix)
app.include_router(media_router, prefix=settings.api_prefix)
app.include_router(content_router, prefix=settings.api_prefix)
app.include_router(social_router, prefix=settings.api_prefix)
app.include_router(webhooks_router, prefix=settings.api_prefix)
app.include_router(generation_router, prefix=settings.api_prefix)
app.include_router(approvals_router, prefix=settings.api_prefix)
app.include_router(publishing_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(strategy_router, prefix=settings.api_prefix)
app.include_router(adaptive_strategy_router, prefix=settings.api_prefix)
app.include_router(content_intelligence_router, prefix=settings.api_prefix)
app.include_router(provider_router, prefix=settings.api_prefix)
app.include_router(quality_router, prefix=settings.api_prefix)


@app.get('/healthz', tags=['system'])
async def healthz():
    return {'status': 'ok', 'service': settings.app_name}


handler = Mangum(app)

