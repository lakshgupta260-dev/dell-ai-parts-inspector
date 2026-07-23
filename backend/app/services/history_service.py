"""
Inspection History Service — CRUD operations for inspection records.

Persists inspection results into SQLite via SQLAlchemy.
Called by the pipeline endpoint after each stage completes.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.database import InspectionRecord
from app.models.history import AnalyticsSummary, InspectionDetail, InspectionSummary, PaginatedHistory

logger = logging.getLogger(__name__)


def create_or_update_inspection(
    db: Session,
    inspection_id: str,
    inspector_username: Optional[str] = None,
    **kwargs,
) -> InspectionRecord:
    """
    Upsert an inspection record.

    Creates a new record if one doesn't exist for inspection_id,
    otherwise updates the existing record with the provided kwargs.
    """
    record = db.query(InspectionRecord).filter_by(inspection_id=inspection_id).first()
    if record is None:
        record = InspectionRecord(
            inspection_id=inspection_id,
            inspector_username=inspector_username,
        )
        db.add(record)

    for key, value in kwargs.items():
        if hasattr(record, key):
            setattr(record, key, value)

    db.commit()
    db.refresh(record)
    logger.debug("Upserted inspection record %s", inspection_id)
    return record


def get_history(
    db: Session, page: int = 1, page_size: int = 20
) -> PaginatedHistory:
    """
    Return a paginated list of inspection summaries, newest first.
    """
    offset = (page - 1) * page_size
    total = db.query(InspectionRecord).count()
    records = (
        db.query(InspectionRecord)
        .order_by(InspectionRecord.uploaded_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    items = [InspectionSummary.model_validate(r) for r in records]
    return PaginatedHistory(total=total, page=page, page_size=page_size, items=items)

def get_escalated_history(
    db: Session, page: int = 1, page_size: int = 20
) -> PaginatedHistory:
    """
    Return a paginated list of escalated inspections, newest first.
    """
    offset = (page - 1) * page_size
    query = db.query(InspectionRecord).filter(InspectionRecord.is_escalated == 1)
    total = query.count()
    records = (
        query
        .order_by(InspectionRecord.uploaded_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    items = [InspectionSummary.model_validate(r) for r in records]
    return PaginatedHistory(total=total, page=page, page_size=page_size, items=items)

def get_inspection_detail(db: Session, inspection_id: str) -> Optional[InspectionDetail]:
    """Return full detail for one inspection, or None if not found."""
    record = db.query(InspectionRecord).filter_by(inspection_id=inspection_id).first()
    if record is None:
        return None
    return InspectionDetail.model_validate(record)


def get_analytics(db: Session) -> AnalyticsSummary:
    """Compute dashboard analytics from all inspection records."""
    total = db.query(InspectionRecord).count()
    authentic = db.query(InspectionRecord).filter_by(verdict="AUTHENTIC").count()
    suspicious = db.query(InspectionRecord).filter_by(verdict="SUSPICIOUS").count()
    counterfeit = db.query(InspectionRecord).filter_by(verdict="COUNTERFEIT").count()

    scores = [
        r.fraud_score
        for r in db.query(InspectionRecord).all()
        if r.fraud_score is not None
    ]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    pass_rate = round((authentic / total * 100), 1) if total > 0 else 0.0

    return AnalyticsSummary(
        total_inspections=total,
        authentic_count=authentic,
        suspicious_count=suspicious,
        counterfeit_count=counterfeit,
        pass_rate=pass_rate,
        avg_fraud_score=avg_score,
    )
