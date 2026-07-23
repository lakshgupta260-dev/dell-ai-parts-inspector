"""
Pydantic schemas for Inspection History API responses.
These are separate from the SQLAlchemy ORM models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InspectionSummary(BaseModel):
    """Lightweight inspection record for list views."""

    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    inspection_id: str
    uploaded_at: datetime
    completed_at: Optional[datetime] = None
    service_tag: Optional[str] = None
    model_name: Optional[str] = None
    fraud_score: Optional[int] = None
    verdict: Optional[str] = None
    pipeline_status: str
    inspector_username: Optional[str] = None
    is_escalated: bool = False

class InspectionDetail(InspectionSummary):
    """Full inspection record for detail views."""

    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    part_number: Optional[str] = None
    express_service_code: Optional[str] = None
    confidence_level: Optional[str] = None
    ai_model_used: Optional[str] = None
    final_reasoning: Optional[str] = None
    front_blur_score: Optional[float] = None
    back_blur_score: Optional[float] = None
    overall_quality_ok: Optional[bool] = None
    comparison_risk_score: Optional[int] = None
    report_path: Optional[str] = None



class PaginatedHistory(BaseModel):
    """Paginated list of inspection summaries."""

    total: int
    page: int
    page_size: int
    items: List[InspectionSummary]


class AnalyticsSummary(BaseModel):
    """High-level analytics for the dashboard."""

    total_inspections: int
    authentic_count: int
    suspicious_count: int
    counterfeit_count: int
    pass_rate: float = Field(..., description="Percentage of AUTHENTIC verdicts.")
    avg_fraud_score: float
