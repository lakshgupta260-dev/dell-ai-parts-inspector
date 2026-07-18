"""
Application configuration and environment variable management.

All secrets and environment-dependent values are loaded here via
python-dotenv so nothing is ever hardcoded.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend root (one level above app/)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class Settings:
    """Central settings object. Add new env vars here as the project grows."""

    # ── Server ────────────────────────────────────────────────────────────────
    APP_TITLE: str = "Dell AI Parts Inspector API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Enterprise-grade AI system that detects counterfeit or defective "
        "Dell hardware parts using Computer Vision, OCR, and Agentic AI."
    )

    # ── Storage ───────────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = Path(__file__).resolve().parents[2] / "uploads"
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    ALLOWED_CONTENT_TYPES: frozenset = frozenset(
        {"image/jpeg", "image/png", "image/webp", "image/tiff"}
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ── Authentication ────────────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dell-ai-inspector-dev-secret-change-in-prod")
    JWT_EXPIRE_MINUTES: str = os.getenv("JWT_EXPIRE_MINUTES", "480")  # 8 hours

    # ── AI ────────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── WhatsApp Cloud API ────────────────────────────────────────────────────
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")

    # ── Vapi ──────────────────────────────────────────────────────────────────
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_PHONE_NUMBER_ID: str = os.getenv("VAPI_PHONE_NUMBER_ID", "")

    # ── Resend (email) ────────────────────────────────────────────────────────
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")


# Singleton used everywhere in the application
settings = Settings()
