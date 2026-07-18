"""
SQLAlchemy ORM models for inspection history and user accounts.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


class InspectionRecord(Base):
    """Persists high-level metadata for every completed inspection."""

    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(36), unique=True, index=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # OCR fields
    service_tag = Column(String(20), nullable=True)
    part_number = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    express_service_code = Column(String(20), nullable=True)

    # AI results
    fraud_score = Column(Integer, nullable=True)
    verdict = Column(String(20), nullable=True)          # AUTHENTIC | SUSPICIOUS | COUNTERFEIT
    confidence_level = Column(String(10), nullable=True) # HIGH | MEDIUM | LOW
    ai_model_used = Column(String(50), nullable=True)
    final_reasoning = Column(Text, nullable=True)

    # Vision
    front_blur_score = Column(Float, nullable=True)
    back_blur_score = Column(Float, nullable=True)
    overall_quality_ok = Column(Integer, nullable=True)  # 0 | 1

    # Comparison
    comparison_risk_score = Column(Integer, nullable=True)

    # Status
    pipeline_status = Column(String(30), default="uploaded")
    report_path = Column(String(300), nullable=True)

    # Inspector (set after auth is integrated)
    inspector_username = Column(String(100), nullable=True)


class User(Base):
    """User accounts for Inspector and QA Manager roles."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="INSPECTOR", nullable=False)  # INSPECTOR | QA_MANAGER
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)
