"""ResumeLens HTTP API."""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .config import get_settings
from .engine import analyze
from .engine.skills import categorize, extract_skills
from .parsers import UnsupportedFileError, extract_text
from .ratelimit import RateLimiter
from .schemas import AnalyzeRequest, AnalyzeResponse, SkillsRequest, SkillsResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("resumelens")

settings = get_settings()
limiter = RateLimiter(settings.rate_limit_per_minute)
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="ResumeLens",
    version=__version__,
    description="Explainable ATS-style resume vs job description analysis.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    if request.url.path.startswith("/api/"):
        client = request.client.host if request.client else "unknown"
        retry_after = limiter.check(client)
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
                headers={"Retry-After": str(int(retry_after) + 1), "X-Request-ID": request_id},
            )
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    log.info("%s %s %s %.1fms id=%s", request.method, request.url.path, response.status_code, elapsed_ms, request_id)
    return response


@app.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "UP", "version": __version__}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze_text(req: AnalyzeRequest) -> dict:
    """Score a plain-text resume against a job description."""
    return analyze(req.resume_text, req.job_description).to_dict()


@app.post("/api/v1/analyze/file", response_model=AnalyzeResponse, tags=["analysis"])
async def analyze_file(resume: UploadFile = File(...), job_description: str = Form(..., min_length=50)) -> dict:
    """Score an uploaded PDF/DOCX/TXT resume against a job description."""
    data = await resume.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Resume file is too large (max 2 MB).")
    if len(job_description) > settings.max_text_chars:
        raise HTTPException(status_code=413, detail="Job description is too long.")
    try:
        text = extract_text(resume.filename or "", data)
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    if len(text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Could not find enough text in the resume.")
    return analyze(text[: settings.max_text_chars], job_description).to_dict()


@app.post("/api/v1/skills/extract", response_model=SkillsResponse, tags=["analysis"])
def skills(req: SkillsRequest) -> dict:
    """List known technical skills mentioned in any text."""
    found = extract_skills(req.text)
    return {"skills": dict(found.most_common()), "by_category": categorize(list(found))}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
