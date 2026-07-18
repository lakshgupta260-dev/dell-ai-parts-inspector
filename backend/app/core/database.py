"""
SQLAlchemy database engine, session factory, and Base.

Uses SQLite for the hackathon (zero-config, file-based).
Switch DATABASE_URL to PostgreSQL in .env for production.
"""

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# Ensure DB directory exists
_db_path = settings.UPLOAD_DIR.parent / "dell_inspector.db"
_db_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = settings.DATABASE_URL or f"sqlite:///{_db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called at application startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised at %s", DATABASE_URL)
