"""
History API router — inspection records and analytics.

Endpoints:
  GET /api/v1/history                    — paginated inspection list
  GET /api/v1/history/analytics          — dashboard KPIs
  GET /api/v1/history/{inspection_id}    — full inspection detail
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.history import AnalyticsSummary, InspectionDetail, PaginatedHistory
from app.services.history_service import get_analytics, get_history, get_inspection_detail

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/history", tags=["History"])


@router.get(
    "",
    response_model=PaginatedHistory,
    summary="Get paginated inspection history",
    description="Returns all inspection records, newest first, with pagination.",
)
def list_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Records per page."),
    db: Session = Depends(get_db),
) -> PaginatedHistory:
    return get_history(db, page=page, page_size=page_size)


@router.get(
    "/analytics",
    response_model=AnalyticsSummary,
    summary="Get dashboard analytics",
    description="Returns aggregated KPIs: total inspections, verdict counts, pass rate, avg fraud score.",
)
def analytics(db: Session = Depends(get_db)) -> AnalyticsSummary:
    return get_analytics(db)


@router.get(
    "/{inspection_id}",
    response_model=InspectionDetail,
    summary="Get full detail for one inspection",
)
def inspection_detail(
    inspection_id: str,
    db: Session = Depends(get_db),
) -> InspectionDetail:
    record = get_inspection_detail(db, inspection_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found in history.",
        )
    return record
