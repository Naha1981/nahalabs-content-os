import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from pathlib import Path
from .models import BusinessProspect
from .scoring import opportunity_score, social_gap_score, grade
from .discovery import extract_contact_details, extract_social_links, maps_search_url
from .maps_worker import discover_google_maps
from .enrichment import enrich_business
from .activity import ActivityObservation, analyse_channel, historical_activity_score, social_gap_from_activity
from .social_evidence import extract_social_evidence
from .social_browser import collect_social_url, collect_social_urls
from .social_pipeline import enrich_social_profiles
from .prospect_radar import radar_record
from .storage import init_db, upsert_many, list_prospects, get_prospect, update_qualification
from .outreach_intelligence import build_outreach_intelligence
from .content_intelligence import normalise_pattern, generate_concepts
from .generation import generate_content_assets
from .production import build_production_brief
from .renderer import render_local_preview, RendererUnavailable
from .assembly import assemble_mp4, AssemblyUnavailable
from .media_layer import synthesize_voiceover, make_captions, mux_voice_and_captions, MediaLayerUnavailable
from .kie_video import submit_kie_video, get_kie_task, KIEUnavailable, KIETaskError
from .pattern_extractor import extract_pattern
from .source_ingestion import fetch_url_text
from .storage import create_pattern, list_patterns, get_pattern, create_content_assets, list_content_assets, update_content_asset, get_content_asset, create_production_job, list_production_jobs, get_production_job, update_production_job
from .publishing import create_publish_job, list_publish_jobs, get_publish_job, update_publish_job, dry_run_publish
from .performance import record_observation, list_observations, learning_summary
from .learning_engine import build_content_learning
from .campaigns import create_campaign, get_campaign, list_campaigns, list_active_campaigns, update_campaign
from .command_center import campaign_command_center
from .outreach_events import create_outreach_event, list_outreach_events, outreach_summary
from .revenue import create_revenue_event, revenue_summary, EVENTS
from .crm import create_opportunity, get_opportunity, list_opportunities, update_opportunity, crm_summary, STAGES
from .unified_workspace import prospect_workspace
from .daily_operator import daily_operator
from .scheduler import list_scheduled_jobs, set_job_enabled, run_job, list_job_runs, automation_health
from .browser_runtime import browser_worker_status, require_browser_worker, BrowserWorkerUnavailable

APP_VERSION = "0.38.5"

app = FastAPI(title="NahaLabs Reactivate API", version=APP_VERSION)
init_db()
MEDIA_DIR = Path(os.environ.get("REACTIVATE_MEDIA_DIR", str(Path(__file__).resolve().parent.parent / "media")))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

_CORS_RAW = os.environ.get(
    "REACTIVATE_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175",
)
_CORS_ORIGINS = [o.strip().rstrip("/") for o in _CORS_RAW.split(",") if o.strip()]
_CORS_WILDCARD = "*" in _CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _CORS_WILDCARD else _CORS_ORIGINS,
    allow_credentials=not _CORS_WILDCARD,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health", tags=["ops"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "nahalabs-reactivate",
        "version": APP_VERSION,
        "browser_worker": browser_worker_status(),
    }

# Optional bearer-token protection for hosted environments. Health stays public.
_API_TOKEN = os.environ.get("REACTIVATE_API_TOKEN", "").strip()

@app.middleware("http")
async def hosted_api_auth(request, call_next):
    if not _API_TOKEN or request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"} or request.method == "OPTIONS":
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {_API_TOKEN}":
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)



def _discover_maps_guarded(query: str, location: str, limit: int, headless: bool) -> list[dict]:
    try:
        require_browser_worker()
    except BrowserWorkerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    try:
        return discover_google_maps(query, location, limit, headless)
    except HTTPException:
        raise
    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=(
            "The browser worker could not start a subprocess on this platform "
            f"({exc}). On Windows this means the Playwright event loop is not a "
            "ProactorEventLoop; restart the backend so the compatibility shim applies."
        ))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Maps discovery failed: {exc}")


class ScoreResponse(BaseModel):
    score: float
    grade: str
    social_gap_score: float


class DiscoveryRequest(BaseModel):
    query: str = Field(min_length=2)
    location: str = Field(min_length=2)


class PageInspectionRequest(BaseModel):
    html: str = Field(min_length=1)


class MapsWorkerRequest(DiscoveryRequest):
    limit: int = Field(default=10, ge=1, le=50)
    headless: bool = True


class MediaLayerRequest(BaseModel):
    voice: str = "en"
    duration_seconds: float | None = None

@app.post("/api/v1/production-jobs/{job_id}/media-layer")
def production_media_layer(job_id: int, request: MediaLayerRequest) -> dict:
    job = get_production_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")
    if not job.get("media_url"):
        raise HTTPException(status_code=409, detail="Render a video before applying voice and captions")
    voice_text = (job.get("voiceover") or job.get("hook") or "").strip()
    if not voice_text:
        raise HTTPException(status_code=422, detail="Production job has no voiceover text")
    try:
        video_path = MEDIA_DIR / Path(str(job["media_url"])).name if str(job["media_url"]).startswith("/media/") else Path(str(job["media_url"]))
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        voice = synthesize_voiceover(voice_text, MEDIA_DIR, request.voice)
        captions = make_captions(voice_text, MEDIA_DIR, request.duration_seconds or job.get("duration_seconds"))
        final = mux_voice_and_captions(video_path, Path(voice["media_path"]), Path(captions["media_path"]), MEDIA_DIR)
        media_url = "/media/" + final["media_filename"]
        updated = update_production_job(job_id, {"media_url": media_url, "renderer": "LOCAL_FFMPEG_MEDIA_LAYER", "status": "READY_TO_PUBLISH", "render_error": "", "rendered_at": datetime.now(timezone.utc).isoformat()})
        return {"job": updated, "voiceover": {**voice, "media_url": "/media/" + voice["media_filename"]}, "captions": {**captions, "media_url": "/media/" + captions["media_filename"]}, "final": final | {"media_url": media_url}}
    except (MediaLayerUnavailable, FileNotFoundError, RuntimeError, ValueError) as exc:
        update_production_job(job_id, {"status": "BLOCKED", "render_error": str(exc)})
        raise HTTPException(status_code=503, detail=str(exc))


class PerformanceObservationRequest(BaseModel):
    observed_at: str = ""
    published_url: str = ""
    impressions: int = Field(default=0, ge=0)
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    leads: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    revenue: float = Field(default=0, ge=0)
    source: str = "MANUAL"
    notes: str = ""


@app.post("/api/v1/publishing-jobs/{publish_job_id}/performance")
def add_performance_observation(publish_job_id: int, request: PerformanceObservationRequest) -> dict:
    job = get_publish_job(publish_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Publishing job not found")
    observation = record_observation(job, request.model_dump())
    return {"observation": observation, "learning_ready": True}


@app.get("/api/v1/prospects/{prospect_id}/performance")
def prospect_performance(prospect_id: int, limit: int = 100) -> dict:
    if not get_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")
    observations = list_observations(prospect_id, limit=limit)
    return {"prospect_id": prospect_id, "count": len(observations), "observations": observations}


@app.get("/api/v1/prospects/{prospect_id}/learning")
def prospect_learning(prospect_id: int) -> dict:
    if not get_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")
    return learning_summary(prospect_id)

@app.get("/api/v1/prospects/{prospect_id}/content-learning")
def prospect_content_learning(prospect_id: int) -> dict:
    if not get_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")
    return build_content_learning(prospect_id)


@app.get("/api/v1/learning")
def global_learning() -> dict:
    return learning_summary()


@app.get("/api/v1/campaign-command-center")
def campaign_command_center_api() -> dict:
    return campaign_command_center()

@app.get("/api/v1/daily-operator")
def daily_operator_api() -> dict:
    return daily_operator()

@app.get("/api/v1/scheduler/jobs")
def scheduler_jobs_api() -> dict:
    return {"jobs": list_scheduled_jobs()}

@app.get("/api/v1/scheduler/health")
def scheduler_health_api() -> dict:
    return automation_health()

@app.post("/api/v1/scheduler/jobs/{job_id}/run")
def scheduler_run_api(job_id: int) -> dict:
    try: return run_job(job_id)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))

class SchedulerToggleRequest(BaseModel):
    enabled: bool

@app.post("/api/v1/scheduler/jobs/{job_id}/toggle")
def scheduler_toggle_api(job_id: int, request: SchedulerToggleRequest) -> dict:
    job=set_job_enabled(job_id, request.enabled)
    if not job: raise HTTPException(status_code=404, detail="Scheduled job not found")
    return {"job":job}

@app.get("/api/v1/scheduler/runs")
def scheduler_runs_api(job_id: int | None = None, limit: int = 50) -> dict:
    return {"runs": list_job_runs(job_id, min(max(limit,1),200))}

class RevenueEventRequest(BaseModel):
    event_type: str = Field(min_length=3)
    amount: float = Field(default=0, ge=0)
    currency: str = "ZAR"
    campaign_id: int | None = None
    performance_observation_id: int | None = None
    source: str = "MANUAL"
    note: str = ""
    occurred_at: str = ""

@app.post("/api/v1/prospects/{prospect_id}/revenue/events")
def log_revenue_event(prospect_id:int, request:RevenueEventRequest)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    try: return create_revenue_event(prospect_id, **request.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/prospects/{prospect_id}/revenue")
def prospect_revenue(prospect_id:int, campaign_id:int|None=None)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    return revenue_summary(prospect_id,campaign_id)


class OpportunityRequest(BaseModel):
    name: str = Field(min_length=2)
    value: float = Field(default=0, ge=0)
    currency: str = "ZAR"
    campaign_id: int | None = None
    owner: str = ""
    next_follow_up_at: str = ""
    note: str = ""
    stage: str = "DISCOVERY"

class OpportunityUpdateRequest(BaseModel):
    name: str | None = None
    value: float | None = Field(default=None, ge=0)
    currency: str | None = None
    campaign_id: int | None = None
    owner: str | None = None
    next_follow_up_at: str | None = None
    note: str | None = None
    stage: str | None = None

@app.post("/api/v1/prospects/{prospect_id}/opportunities")
def create_crm_opportunity(prospect_id:int, request:OpportunityRequest)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    try: return create_opportunity(prospect_id, **request.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))

@app.get("/api/v1/prospects/{prospect_id}/opportunities")
def prospect_opportunities(prospect_id:int)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    return {"prospect_id":prospect_id,"opportunities":list_opportunities(prospect_id)}

@app.patch("/api/v1/opportunities/{opportunity_id}")
def patch_opportunity(opportunity_id:int, request:OpportunityUpdateRequest)->dict:
    try:
        out=update_opportunity(opportunity_id, request.model_dump(exclude_none=True))
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    if not out: raise HTTPException(status_code=404, detail="Opportunity not found")
    return out

@app.get("/api/v1/crm/summary")
def get_crm_summary()->dict:
    return crm_summary()


class OutreachEventRequest(BaseModel):
    channel: str = Field(min_length=2)
    event_type: str = Field(min_length=2)
    subject: str = ""
    note: str = ""
    campaign_id: int | None = None
    occurred_at: str = ""

@app.post("/api/v1/prospects/{prospect_id}/outreach/events")
def log_outreach_event(prospect_id: int, request: OutreachEventRequest) -> dict:
    if not get_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")
    allowed_channels={"WHATSAPP","EMAIL","INSTAGRAM","FACEBOOK","LINKEDIN","PHONE"}
    if request.channel not in allowed_channels:
        raise HTTPException(status_code=422, detail=f"Invalid channel: {request.channel}")
    return create_outreach_event(prospect_id, **request.model_dump())

@app.get("/api/v1/prospects/{prospect_id}/outreach/events")
def get_outreach_events(prospect_id: int, campaign_id: int | None = None, limit: int = 50) -> dict:
    if not get_prospect(prospect_id):
        raise HTTPException(status_code=404, detail="Prospect not found")
    events = list_outreach_events(prospect_id, campaign_id, limit)
    return {"prospect_id": prospect_id, "count": len(events), "events": events}



@app.post("/api/v1/opportunities/score", response_model=ScoreResponse)
def score_opportunity(prospect: BusinessProspect) -> ScoreResponse:
    score = opportunity_score(prospect)
    gap = social_gap_score(prospect)
    return ScoreResponse(score=score, grade=grade(score), social_gap_score=gap)


@app.post("/api/v1/discovery/maps-search")
def discovery_url(request: DiscoveryRequest) -> dict[str, str]:
    return {"provider": "google_maps", "search_url": maps_search_url(request.query, request.location)}


@app.post("/api/v1/discovery/inspect-page")
def inspect_page(request: PageInspectionRequest) -> dict:
    phone, website = extract_contact_details(request.html)
    social_urls = extract_social_links(request.html)
    return {
        "website": website,
        "phone": phone,
        "social_urls": social_urls,
        "evidence_state": "OBSERVED",
    }


@app.post("/api/v1/discovery/maps")
def discover_maps(request: MapsWorkerRequest) -> dict:
    businesses = _discover_maps_guarded(request.query, request.location, request.limit, request.headless)
    return {
        "provider": "google_maps",
        "query": request.query,
        "location": request.location,
        "count": len(businesses),
        "businesses": businesses,
    }


class EnrichmentRequest(BaseModel):
    business: dict


class SocialActivityRequest(BaseModel):
    platform: str = Field(min_length=2)
    post_dates: list[datetime]


class SocialActivityBatchRequest(BaseModel):
    channels: list[SocialActivityRequest]


class SocialEvidenceRequest(BaseModel):
    url: str = Field(min_length=10)
    html: str = Field(min_length=1)


@app.post("/api/v1/discovery/social-evidence")
def social_evidence(request: SocialEvidenceRequest) -> dict:
    return extract_social_evidence(request.html, request.url)




class SocialBrowserRequest(BaseModel):
    url: str = Field(min_length=10)
    headless: bool = True


class SocialBrowserBatchRequest(BaseModel):
    urls: dict[str, str]
    headless: bool = True


@app.post("/api/v1/discovery/social-browser")
def social_browser(request: SocialBrowserRequest) -> dict:
    return collect_social_url(request.url, headless=request.headless)


@app.post("/api/v1/discovery/social-enrich")
def social_enrich(request: SocialBrowserBatchRequest) -> dict:
    return enrich_social_profiles(request.urls, headless=request.headless)


@app.post("/api/v1/discovery/social-browser/batch")
def social_browser_batch(request: SocialBrowserBatchRequest) -> dict:
    results = collect_social_urls(request.urls, headless=request.headless)
    return {"count": len(results), "results": results}


@app.post("/api/v1/discovery/activity")
def analyse_activity(request: SocialActivityBatchRequest) -> dict:
    summaries = [
        analyse_channel(
            ActivityObservation(channel.platform, channel.post_dates)
        )
        for channel in request.channels
    ]
    return {
        "channels": [summary.__dict__ for summary in summaries],
        "historical_activity_score": historical_activity_score(summaries),
        "social_gap_score": social_gap_from_activity(summaries),
    }


@app.post("/api/v1/discovery/enrich")
def enrich(request: EnrichmentRequest) -> dict:
    return enrich_business(request.business)


@app.post("/api/v1/discovery/pipeline")
def discovery_pipeline(request: MapsWorkerRequest) -> dict:
    businesses = _discover_maps_guarded(request.query, request.location, request.limit, request.headless)
    enriched = [enrich_business(business) for business in businesses]
    return {
        "provider": "google_maps",
        "query": request.query,
        "location": request.location,
        "count": len(enriched),
        "businesses": enriched,
    }


@app.post("/api/v1/prospects/radar/run")
def run_prospect_radar(request: MapsWorkerRequest) -> dict:
    """End-to-end radar: Maps discovery -> website enrichment -> social evidence -> scoring."""
    discovered = discover_google_maps(request.query, request.location, request.limit, request.headless)
    enriched = []
    pipeline_errors = []

    for business in discovered:
        try:
            item = enrich_business(business)
            social_urls = item.get("social_urls") or {}
            if social_urls:
                try:
                    social = enrich_social_profiles(social_urls, headless=request.headless)
                    item["social_channels"] = social.get("channels", [])
                    item["historical_activity_score"] = social.get("historical_activity_score", 0)
                    item["social_gap_score"] = social.get("social_gap_score", 0)
                    item.setdefault("evidence", []).extend(
                        evidence
                        for channel in social.get("channels", [])
                        for evidence in channel.get("evidence", [])
                    )
                except Exception as exc:
                    item["social_enrichment_status"] = "NOT_VERIFIED"
                    item["social_enrichment_error"] = str(exc)
            else:
                item["social_enrichment_status"] = "NO_SOCIAL_URLS_FOUND"
            enriched.append(item)
        except Exception as exc:
            pipeline_errors.append({"name": business.get("name", "Unknown"), "stage": "enrichment", "error": str(exc)})

    radar = [radar_record(item) for item in enriched]
    radar.sort(key=lambda item: item["score"], reverse=True)
    saved = upsert_many(radar)
    return {
        "provider": "google_maps",
        "query": request.query,
        "location": request.location,
        "count": len(saved),
        "prospects": saved,
        "errors": pipeline_errors,
        "pipeline": ["google_maps", "website_enrichment", "social_evidence", "radar_scoring", "prospect_database"],
    }


@app.get("/api/v1/prospects/{prospect_id}/outreach-intelligence")
def prospect_outreach_intelligence(prospect_id: int) -> dict:
    record = get_prospect(prospect_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect not found")
    return {"prospect_id": prospect_id, "intelligence": build_outreach_intelligence(record)}




class PatternIngestRequest(BaseModel):
    source_url: str = ""
    title: str = ""
    source_type: str = "URL"
    transcript: str = ""
    text: str = ""
    audience: str = ""
    tags: list[str] = []
    notes: str = ""


@app.post("/api/v1/patterns/ingest")
def ingest_pattern(request: PatternIngestRequest) -> dict:
    """Ingest supplied transcript/text or fetch readable public HTML from a URL, then save the extracted pattern."""
    source = request.transcript.strip() or request.text.strip()
    fetch_status = "SUPPLIED_TEXT" if source else "NOT_FETCHED"
    fetched = None
    title = request.title.strip()
    if not source and request.source_url.strip():
        try:
            fetched = fetch_url_text(request.source_url.strip())
            fetch_status = fetched.get("status", "UNKNOWN")
            source = (fetched.get("text") or "").strip()
            title = title or (fetched.get("title") or "").strip()
        except Exception as exc:
            return {"status": "FETCH_FAILED", "source_url": request.source_url, "error": str(exc), "saved": False}
    record = extract_pattern({
        "title": title, "source_url": request.source_url.strip(),
        "source_type": request.source_type, "transcript": source,
        "audience": request.audience, "tags": request.tags, "notes": request.notes
    })
    saved = create_pattern(record) if record.get("extraction_status") == "EXTRACTED" else None
    return {"status": fetch_status, "saved": bool(saved), "pattern": saved or record, "source": {"url": request.source_url, "title": title, "characters": len(source)}}


@app.post("/api/v1/patterns/ingest-file")
async def ingest_pattern_file(file: UploadFile = File(...), source_url: str = "", title: str = "", audience: str = "") -> dict:
    """Ingest a text/markdown transcript file. Binary media is intentionally not transcribed here."""
    content_type = (file.content_type or "").lower()
    if not any(x in content_type for x in ("text/", "json", "markdown")) and not (file.filename or "").lower().endswith((".txt", ".md", ".markdown", ".json")):
        raise HTTPException(status_code=415, detail="Upload a text, markdown, or JSON transcript file")
    raw = await file.read()
    if len(raw) > 2_000_000:
        raise HTTPException(status_code=413, detail="Transcript file is larger than 2 MB")
    text = raw.decode("utf-8", errors="replace").strip()
    record = extract_pattern({"title": title or file.filename or "Uploaded transcript", "source_url": source_url, "source_type": "UPLOAD", "transcript": text, "audience": audience})
    saved = create_pattern(record) if record.get("extraction_status") == "EXTRACTED" else None
    return {"status": "SUPPLIED_TEXT", "saved": bool(saved), "pattern": saved or record, "source": {"filename": file.filename, "characters": len(text)}}


class RadarRequest(BaseModel):
    businesses: list[dict]


@app.post("/api/v1/prospects/radar")
def prospect_radar(request: RadarRequest) -> dict:
    records = []
    errors = []
    for business in request.businesses:
        try:
            records.append(radar_record(business))
        except Exception as exc:
            errors.append({"name": business.get("name", "Unknown"), "error": str(exc)})
    records.sort(key=lambda item: item["score"], reverse=True)
    return {"count": len(records), "prospects": records, "errors": errors}


class ProspectListQuery(BaseModel):
    search: str = ""
    city: str = ""
    min_score: float = Field(default=0, ge=0, le=100)
    limit: int = Field(default=100, ge=1, le=500)


@app.get("/api/v1/prospects")
def get_prospects(search: str = "", city: str = "", min_score: float = 0, status: str = "", priority: str = "", limit: int = 100) -> dict:
    prospects = list_prospects(search=search, city=city, min_score=min_score, status=status, priority=priority, limit=limit)
    return {"count": len(prospects), "prospects": prospects}


@app.get("/api/v1/prospects/{prospect_id}/workspace")
def get_prospect_workspace(prospect_id: int) -> dict:
    workspace = prospect_workspace(prospect_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return workspace


@app.get("/api/v1/prospects/{prospect_id}")
def get_prospect_by_id(prospect_id: int) -> dict:
    record = get_prospect(prospect_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect not found")
    return record


@app.post("/api/v1/prospects/save")
def save_prospects(request: RadarRequest) -> dict:
    records = []
    errors = []
    for business in request.businesses:
        try:
            records.append(radar_record(business))
        except Exception as exc:
            errors.append({"name": business.get("name", "Unknown"), "error": str(exc)})
    saved = upsert_many(records)
    return {"count": len(saved), "saved": saved, "errors": errors}


class QualificationUpdate(BaseModel):
    qualification_status: str | None = None
    priority: str | None = None
    contact_status: str | None = None
    notes: str | None = None
    next_action: str | None = None
    outreach_channel: str | None = None
    outreach_draft: str | None = None
    follow_up_at: str | None = None
    contacted_at: str | None = None


@app.patch("/api/v1/prospects/{prospect_id}/qualification")
def patch_qualification(prospect_id: int, request: QualificationUpdate) -> dict:
    allowed = {
        "qualification_status": {"UNQUALIFIED", "QUALIFIED", "DISQUALIFIED", "NURTURE"},
        "priority": {"HOT", "HIGH", "NORMAL", "LOW"},
        "contact_status": {"NOT_CONTACTED", "QUEUED", "CONTACTED", "REPLIED", "MEETING", "WON", "LOST"},
        "outreach_channel": {"WHATSAPP", "EMAIL", "INSTAGRAM", "FACEBOOK", "LINKEDIN", "PHONE"},
    }
    for field, values in allowed.items():
        value = getattr(request, field)
        if value is not None and value not in values:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=f"Invalid {field}: {value}")
    updates = request.model_dump(exclude_none=True)
    if updates.get("contact_status") == "CONTACTED" and not updates.get("contacted_at"):
        updates["contacted_at"] = datetime.now(timezone.utc).isoformat()
    record = update_qualification(prospect_id, updates)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect not found")
    return record


class OutreachQueueUpdate(BaseModel):
    channel: str
    follow_up_at: str = ""


def _outreach_draft(record: dict) -> str:
    gap = record.get("social_gap") or {}
    headline = gap.get("headline") or "your social content has gone quiet"
    channel = (record.get("channels") or [{}])[0]
    platform = channel.get("platform", "social media")
    days = channel.get("last_meaningful_post_days")
    detail = f"I noticed your {platform} activity has been quiet for around {days} days" if days is not None else "I noticed a gap in your recent social activity"
    return (f"Hi {record.get('name','there')},\n\n{detail}. {headline}\n\n"
            "We help local businesses reactivate the audience they already built with a simple, consistent content system. "
            "I put together a quick Social Gap audit showing what I found and a few content opportunities.\n\n"
            "Would you like me to send it through?")


@app.get("/api/v1/prospects/outreach-queue")
def outreach_queue(status: str = "", priority: str = "", channel: str = "", limit: int = 100) -> dict:
    # Qualified prospects or explicitly queued/contacted prospects enter the sales queue.
    prospects = list_prospects(status=status, priority=priority, limit=limit)
    if not status:
        prospects = [p for p in prospects if p.get("qualification_status") == "QUALIFIED" or p.get("contact_status") not in {"NOT_CONTACTED", "LOST", "WON"}]
    if channel:
        prospects = [p for p in prospects if p.get("outreach_channel") == channel]
    for p in prospects:
        if not p.get("outreach_draft"):
            p["outreach_draft"] = _outreach_draft(p)
    return {"count": len(prospects), "queue": prospects}


@app.post("/api/v1/prospects/{prospect_id}/outreach/queue")
def queue_outreach(prospect_id: int, request: OutreachQueueUpdate) -> dict:
    if request.channel not in {"WHATSAPP", "EMAIL", "INSTAGRAM", "FACEBOOK", "LINKEDIN", "PHONE"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Invalid channel: {request.channel}")
    record = get_prospect(prospect_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect not found")
    draft = record.get("outreach_draft") or _outreach_draft(record)
    updated = update_qualification(prospect_id, {
        "contact_status": "QUEUED", "outreach_channel": request.channel,
        "outreach_draft": draft, "follow_up_at": request.follow_up_at,
    })
    return updated


class PatternCreate(BaseModel):
    title: str = Field(min_length=1)
    source_url: str = ""
    source_type: str = "URL"
    transcript: str = ""
    hook: str = ""
    promise: str = ""
    structure: str = ""
    cta: str = ""
    angle: str = ""
    audience: str = ""
    format: str = ""
    emotional_trigger: str = ""
    tags: list[str] = []
    notes: str = ""


@app.get("/api/v1/patterns")
def get_patterns(search: str = "", limit: int = 100) -> dict:
    items = list_patterns(search=search, limit=limit)
    return {"count": len(items), "patterns": items}


@app.get("/api/v1/patterns/{pattern_id}")
def get_pattern_by_id(pattern_id: int) -> dict:
    record = get_pattern(pattern_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pattern not found")
    return record


@app.post("/api/v1/patterns")
def save_pattern(request: PatternCreate) -> dict:
    return create_pattern(normalise_pattern(request.model_dump()))


class PatternExtractRequest(BaseModel):
    title: str = ""
    source_url: str = ""
    source_type: str = "TRANSCRIPT"
    transcript: str = ""
    text: str = ""
    audience: str = ""
    tags: list[str] = []
    notes: str = ""


@app.post("/api/v1/patterns/extract")
def extract_and_save_pattern(request: PatternExtractRequest) -> dict:
    extracted = extract_pattern(request.model_dump())
    if extracted["extraction_status"] != "EXTRACTED":
        return extracted
    return create_pattern(extracted)


@app.get("/api/v1/prospects/{prospect_id}/content-concepts")
def prospect_content_concepts(prospect_id: int, limit_patterns: int = 10) -> dict:
    record = get_prospect(prospect_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prospect not found")
    patterns = list_patterns(limit=limit_patterns)
    return {"prospect_id": prospect_id, "patterns_used": [p["id"] for p in patterns], "concepts": generate_concepts(record, patterns)}


class CampaignCreateRequest(BaseModel):
    name: str = "Reactivation Campaign"
    objective: str = "REACTIVATE_DEMAND"
    content_count: int = Field(default=3, ge=1, le=3)
    platform: str = "INSTAGRAM_REELS"

@app.get("/api/v1/prospects/{prospect_id}/campaigns")
def get_campaigns(prospect_id:int, limit:int=20)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    return {"prospect_id":prospect_id,"campaigns":list_campaigns(prospect_id,limit=limit)}

@app.post("/api/v1/prospects/{prospect_id}/campaigns/auto")
def auto_start_campaign(prospect_id:int, request:CampaignCreateRequest)->dict:
    """Start a reactivation campaign directly from a qualified prospect.

    This is intentionally gated by seller-owned qualification and refuses to
    create duplicate active campaigns.
    """
    prospect=get_prospect(prospect_id)
    if not prospect: raise HTTPException(status_code=404, detail="Prospect not found")
    if prospect.get("qualification_status") != "QUALIFIED":
        raise HTTPException(status_code=409, detail="Prospect must be QUALIFIED before automation can start.")
    active=list_active_campaigns(prospect_id)
    if active:
        return {"created":False,"reason":"ACTIVE_CAMPAIGN_EXISTS","campaign":active[0]}
    campaign=create_campaign(prospect_id,request.name,request.objective)
    learning=build_content_learning(prospect_id)
    patterns=list_patterns(limit=10)
    assets=generate_content_assets(prospect,patterns,request.content_count,learning)
    saved=create_content_assets(prospect_id,assets)
    asset_ids=[a["id"] for a in saved]
    blockers=[f"Asset #{a['id']} needs human approval before production/publishing." for a in saved]
    result=update_campaign(campaign["id"],{"asset_ids":asset_ids,"status":"AWAITING_APPROVAL","stage":"APPROVAL","blockers":blockers,"next_action":"Review the generated content assets and set each to APPROVED."})
    return {"created":True,"campaign":result,"learning":learning,"assets":saved,"automation":"QUALIFIED_PROSPECT_TO_CAMPAIGN_V0.27"}


@app.post("/api/v1/prospects/{prospect_id}/campaigns")
def start_campaign(prospect_id:int, request:CampaignCreateRequest)->dict:
    prospect=get_prospect(prospect_id)
    if not prospect: raise HTTPException(status_code=404, detail="Prospect not found")
    campaign=create_campaign(prospect_id,request.name,request.objective)
    learning=build_content_learning(prospect_id)
    patterns=list_patterns(limit=10)
    assets=generate_content_assets(prospect,patterns,request.content_count,learning)
    saved=create_content_assets(prospect_id,assets)
    asset_ids=[a["id"] for a in saved]
    blockers=[f"Asset #{a['id']} needs human approval before production/publishing." for a in saved]
    return update_campaign(campaign["id"],{"asset_ids":asset_ids,"status":"AWAITING_APPROVAL","stage":"APPROVAL","blockers":blockers,"next_action":"Review the generated content assets and set each to APPROVED."})

@app.post("/api/v1/campaigns/{campaign_id}/advance")
def advance_campaign(campaign_id:int)->dict:
    campaign=get_campaign(campaign_id)
    if not campaign: raise HTTPException(status_code=404, detail="Campaign not found")
    from .storage import get_content_asset, list_production_jobs
    if campaign["stage"]=="APPROVAL":
        assets=[get_content_asset(i) for i in campaign["asset_ids"]]
        approved=[a for a in assets if a and a.get("status") in {"APPROVED","PRODUCED"}]
        blockers=[f"Asset #{a['id']} is {a.get('status','UNKNOWN')}; approval is required." for a in assets if a and a.get("status") not in {"APPROVED","PRODUCED"}]
        if blockers: return update_campaign(campaign_id,{"status":"AWAITING_APPROVAL","stage":"APPROVAL","blockers":blockers,"next_action":"Approve the remaining content assets."})
        from .production import build_production_brief
        jobs=[]
        for a in approved:
            brief=build_production_brief(a,get_prospect(campaign["prospect_id"]),"INSTAGRAM_REELS")
            from .storage import create_production_job
            jobs.append(create_production_job(campaign["prospect_id"],a["id"],brief)["id"])
        return update_campaign(campaign_id,{"status":"IN_PRODUCTION","stage":"PRODUCTION","production_job_ids":jobs,"blockers":[],"next_action":"Render production jobs; publishing remains credential-gated."})
    if campaign["stage"]=="PRODUCTION":
        jobs=list_production_jobs(campaign["prospect_id"],limit=100)
        mine=[j for j in jobs if j["id"] in campaign["production_job_ids"]]
        if not mine or any(j["status"] not in {"RENDERED","READY_TO_PUBLISH","PUBLISHED"} for j in mine):
            return update_campaign(campaign_id,{"status":"IN_PRODUCTION","stage":"PRODUCTION","next_action":"Render all campaign production jobs before packaging for publication."})
        return update_campaign(campaign_id,{"status":"READY_TO_PUBLISH","stage":"PUBLISH","next_action":"Create platform publishing packages. Live publishing requires authenticated provider credentials."})
    if campaign["stage"]=="PUBLISH":
        return update_campaign(campaign_id,{"status":"MEASURING","stage":"MEASURE","next_action":"Record observed platform performance; learning will feed the next campaign."})
    if campaign["stage"]=="MEASURE":
        return update_campaign(campaign_id,{"status":"COMPLETED","stage":"MEASURE","next_action":"Review learning signals and start the next campaign iteration."})
    return campaign

class ContentGenerateRequest(BaseModel):
    count: int = Field(default=3, ge=1, le=3)

class ContentUpdateRequest(BaseModel):
    title: str | None = None
    hook: str | None = None
    script: str | None = None
    caption: str | None = None
    cta: str | None = None
    status: str | None = None
    notes: str | None = None

@app.get("/api/v1/prospects/{prospect_id}/content-assets")
def get_content_assets(prospect_id:int, limit:int=50)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    return {"prospect_id":prospect_id,"assets":list_content_assets(prospect_id,limit=limit)}

@app.post("/api/v1/prospects/{prospect_id}/content/generate")
def generate_prospect_content(prospect_id:int, request:ContentGenerateRequest)->dict:
    prospect=get_prospect(prospect_id)
    if not prospect: raise HTTPException(status_code=404, detail="Prospect not found")
    patterns=list_patterns(limit=10)
    learning=build_content_learning(prospect_id)
    assets=generate_content_assets(prospect,patterns,request.count,learning)
    saved=create_content_assets(prospect_id,assets)
    return {"prospect_id":prospect_id,"count":len(saved),"assets":saved,"generation":"template_engine_v0.25","ai_provider":"not_configured","learning":learning}

@app.patch("/api/v1/content-assets/{asset_id}")
def patch_content_asset(asset_id:int,request:ContentUpdateRequest)->dict:
    asset=update_content_asset(asset_id,request.model_dump(exclude_none=True))
    if not asset: raise HTTPException(status_code=404, detail="Content asset not found")
    return asset


class ProductionCreateRequest(BaseModel):
    platform: str = "INSTAGRAM_REELS"

class ProductionUpdateRequest(BaseModel):
    status: str | None = None
    media_url: str | None = None
    production_notes: str | None = None
    platform: str | None = None
    aspect_ratio: str | None = None
    duration_seconds: int | None = Field(default=None, ge=1, le=300)


class RenderRequest(BaseModel):
    provider: str = "LOCAL_FFMPEG_PREVIEW"
    model: str = "veo-3-1"
    callback_url: str = ""

@app.post("/api/v1/production-jobs/{job_id}/ai-submit")
def submit_ai_production_job(job_id:int, request:RenderRequest)->dict:
    job=get_production_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Production job not found")
    if request.provider.upper() != "KIE":
        raise HTTPException(status_code=400, detail="Use provider=KIE for the AI provider adapter")
    if job["status"] not in {"BRIEF_READY", "BLOCKED", "IN_PRODUCTION"}:
        raise HTTPException(status_code=409, detail=f"Job status {job['status']} cannot be submitted")
    try:
        result=submit_kie_video(job, model=request.model or "veo-3-1", callback_url=request.callback_url)
    except KIEUnavailable as exc:
        update_production_job(job_id, {"status":"BLOCKED", "renderer":"KIE", "render_error":str(exc)})
        raise HTTPException(status_code=503, detail=str(exc))
    except KIETaskError as exc:
        update_production_job(job_id, {"status":"BLOCKED", "renderer":"KIE", "render_error":str(exc)})
        raise HTTPException(status_code=502, detail=str(exc))
    updated=update_production_job(job_id, {"status":"IN_PRODUCTION", "renderer":"KIE", "provider_task_id":result["task_id"], "provider_model":result["model"], "render_error":""})
    return {"job":updated, "provider_task":result, "media_created":False, "note":"KIE generation is asynchronous; poll the task or use a callback."}


@app.get("/api/v1/production-jobs/{job_id}/ai-status")
def get_ai_production_status(job_id:int)->dict:
    job=get_production_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Production job not found")
    if not job.get("provider_task_id"):
        raise HTTPException(status_code=409, detail="No provider task is attached to this job")
    try:
        result=get_kie_task(job["provider_task_id"])
    except KIEUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except KIETaskError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    if result["state"] == "success" and result["result_urls"]:
        updated=update_production_job(job_id, {"status":"RENDERED", "media_url":result["result_urls"][0], "renderer":"KIE", "render_error":"", "rendered_at":datetime.now(timezone.utc).isoformat()})
        update_content_asset(job["content_asset_id"], {"status":"PRODUCED"})
        return {"job":updated, "provider_task":result, "media_created":True}
    if result["state"] == "fail":
        updated=update_production_job(job_id, {"status":"BLOCKED", "renderer":"KIE", "render_error":result.get("fail_message") or result.get("fail_code") or "KIE generation failed"})
        return {"job":updated, "provider_task":result, "media_created":False}
    return {"job":job, "provider_task":result, "media_created":False}


@app.post("/api/v1/providers/kie/callback")
def kie_callback(payload: dict)->dict:
    data=payload.get("data") or payload
    task_id=data.get("taskId") or data.get("task_id")
    if not task_id:
        return {"accepted":False, "reason":"missing taskId"}
    return {"accepted":True, "task_id":task_id, "note":"Callback received. Status can be reconciled through the KIE task-status endpoint."}


@app.get("/api/v1/prospects/{prospect_id}/production-jobs")
def get_production_jobs(prospect_id:int, limit:int=50)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    jobs=list_production_jobs(prospect_id,limit=limit)
    return {"prospect_id":prospect_id,"count":len(jobs),"jobs":jobs}

@app.post("/api/v1/content-assets/{asset_id}/production")
def create_production(asset_id:int, request:ProductionCreateRequest)->dict:
    asset=get_content_asset(asset_id)
    if not asset: raise HTTPException(status_code=404, detail="Content asset not found")
    prospect=get_prospect(asset['prospect_id'])
    if not prospect: raise HTTPException(status_code=404, detail="Prospect not found")
    if asset['status'] not in {'REVIEW','APPROVED','PRODUCED'}:
        raise HTTPException(status_code=409, detail="Content asset must be REVIEW, APPROVED, or PRODUCED before production")
    brief=build_production_brief(asset,prospect,request.platform)
    job=create_production_job(prospect['id'],asset_id,brief)
    return {"production":job,"brief":brief,"renderer":"NOT_CONFIGURED","media_created":False}

@app.patch("/api/v1/production-jobs/{job_id}")
def patch_production_job(job_id:int, request:ProductionUpdateRequest)->dict:
    job=update_production_job(job_id,request.model_dump(exclude_none=True))
    if not job: raise HTTPException(status_code=404, detail="Production job not found")
    return job


class AssemblyRequest(BaseModel):
    job_ids: list[int] = Field(min_length=1, max_length=10)


class PublishPackageRequest(BaseModel):
    platform: str
    caption: str = ''
    hashtags: list[str] = Field(default_factory=list, max_length=30)
    scheduled_for: str = ''
    provider: str = 'DRY_RUN'

class PublishUpdateRequest(BaseModel):
    status: str | None = None
    scheduled_for: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None


@app.get("/api/v1/prospects/{prospect_id}/publishing-jobs")
def get_publishing_jobs(prospect_id:int, limit:int=50)->dict:
    if not get_prospect(prospect_id): raise HTTPException(status_code=404, detail="Prospect not found")
    jobs=list_publish_jobs(prospect_id,limit=limit)
    return {"prospect_id":prospect_id,"count":len(jobs),"jobs":jobs}

@app.post("/api/v1/production-jobs/{job_id}/publish-package")
def create_publish_package(job_id:int, request:PublishPackageRequest)->dict:
    job=get_production_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Production job not found")
    if job.get("status") not in {"READY_TO_PUBLISH","RENDERED","PUBLISHED"}:
        raise HTTPException(status_code=409, detail=f"Job status {job.get('status')} is not ready for publishing")
    if not job.get("media_url"): raise HTTPException(status_code=409, detail="Production job has no media_url")
    caption=request.caption or job.get("title","")
    publish=create_publish_job(job_id,job["prospect_id"],request.platform,caption,request.hashtags,job["media_url"],request.scheduled_for,request.provider)
    return {"publishing":publish,"publishable":True,"live_platform_publish":False,"note":"v0.23 creates the publishing package and queue. Real platform publishing requires authenticated provider credentials."}

@app.patch("/api/v1/publishing-jobs/{publish_job_id}")
def patch_publishing_job(publish_job_id:int, request:PublishUpdateRequest)->dict:
    job=get_publish_job(publish_job_id)
    if not job: raise HTTPException(status_code=404, detail="Publishing job not found")
    if request.status and request.status not in {"QUEUED","SCHEDULED","PUBLISHING","PUBLISHED","FAILED","CANCELLED"}: raise HTTPException(status_code=400, detail="Invalid publishing status")
    updates=request.model_dump(exclude_none=True)
    return update_publish_job(publish_job_id,updates)

@app.post("/api/v1/publishing-jobs/{publish_job_id}/publish")
def publish_queued_job(publish_job_id:int)->dict:
    job=get_publish_job(publish_job_id)
    if not job: raise HTTPException(status_code=404, detail="Publishing job not found")
    if job.get("provider") != "DRY_RUN": raise HTTPException(status_code=400, detail="Only DRY_RUN publisher is configured in v0.23")
    published=dry_run_publish(job)
    return {"publishing":published,"live_platform_publish":False,"note":"Dry-run only; no social platform was contacted."}

@app.post("/api/v1/prospects/{prospect_id}/media/assemble")
def assemble_prospect_media(prospect_id: int, request: AssemblyRequest) -> dict:
    jobs=[]
    for jid in request.job_ids:
        job=get_production_job(jid)
        if not job or int(job.get("prospect_id")) != prospect_id:
            raise HTTPException(status_code=404, detail=f"Production job {jid} not found for this prospect")
        if job.get("status") != "RENDERED" or not job.get("media_url"):
            raise HTTPException(status_code=409, detail=f"Job {jid} must have a rendered media file before assembly")
        url=str(job["media_url"])
        if not url.startswith("/media/"):
            raise HTTPException(status_code=409, detail=f"Job {jid} does not point to a local media file")
        path=MEDIA_DIR / Path(url.removeprefix("/media/")).name
        jobs.append({"id":jid,"media_path":str(path)})
    try:
        result=assemble_mp4(jobs, MEDIA_DIR)
    except (AssemblyUnavailable, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"prospect_id":prospect_id,"job_ids":request.job_ids,"assembly":result,"media_url":"/media/"+result["media_filename"],"media_created":True}

@app.post("/api/v1/production-jobs/{job_id}/render")
def render_production_job(job_id:int, request:RenderRequest)->dict:
    job=get_production_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Production job not found")
    provider=request.provider.upper()
    if provider != "LOCAL_FFMPEG_PREVIEW":
        raise HTTPException(status_code=400, detail="Only LOCAL_FFMPEG_PREVIEW is configured in v0.19")
    if job["status"] not in {"BRIEF_READY", "IN_PRODUCTION", "BLOCKED"}:
        raise HTTPException(status_code=409, detail=f"Job status {job['status']} cannot be rendered")

    update_production_job(job_id, {"status":"IN_PRODUCTION", "renderer":provider, "render_error":""})
    job=get_production_job(job_id)
    try:
        result=render_local_preview(job, MEDIA_DIR)
    except RendererUnavailable as exc:
        updated=update_production_job(job_id, {"status":"BLOCKED", "renderer":provider, "render_error":str(exc)})
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        updated=update_production_job(job_id, {"status":"BLOCKED", "renderer":provider, "render_error":str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))

    media_url=f"/media/{result['media_filename']}"
    rendered_at=datetime.now(timezone.utc).isoformat()
    updated=update_production_job(job_id, {"status":"RENDERED", "media_url":media_url, "renderer":provider, "render_error":"", "rendered_at":rendered_at})
    update_content_asset(job["content_asset_id"], {"status":"PRODUCED"})
    return {"job":updated, "render":result, "media_url":media_url, "media_created":True}



def _sort_routes_by_specificity() -> None:
    app.router.routes.sort(key=lambda route: getattr(route, "path", "").count("{"))


_sort_routes_by_specificity()
