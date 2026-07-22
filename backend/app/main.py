"""
Dell AI Parts Inspector — Application entry point.

Responsibilities:
  - Instantiate the FastAPI application with metadata from settings.
  - Configure structured logging once, at startup.
  - Initialise the database and create all tables.
  - Mount all API routers.
  - Expose the health-check root endpoint (preserved from initial skeleton).
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai as ai_router
from app.api import auth as auth_router
from app.api import comparison as comparison_router
from app.api import history as history_router
from app.api import notifications as notifications_router
from app.api import ocr as ocr_router
from app.api import pipeline as pipeline_router
from app.api import report as report_router
from app.api import upload as upload_router
from app.api import vision as vision_router
from app.core.config import settings
from app.core.database import init_db

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
)

# ── CORS (wide-open for local development; tighten in production) ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: initialise DB tables ─────────────────────────────────────────────
@app.on_event("startup")
def on_startup() -> None:
    """Create all SQLAlchemy tables on server startup."""
    init_db()
    logger.info("Dell PartVision AI API started successfully.")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(upload_router.router)
app.include_router(vision_router.router)
app.include_router(ocr_router.router)
app.include_router(comparison_router.router)
app.include_router(ai_router.router)
app.include_router(report_router.router)
app.include_router(notifications_router.router)
app.include_router(history_router.router)
app.include_router(pipeline_router.router)


# ── Health check (preserved from initial skeleton) ────────────────────────────
@app.get("/", tags=["Health"])
def root() -> dict:
    """Return a simple liveness signal."""
    return {"message": "Dell PartVision AI Backend is Running 🚀"}