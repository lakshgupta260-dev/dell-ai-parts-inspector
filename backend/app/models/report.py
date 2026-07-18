"""
Pydantic models for the PDF Report output.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ReportResult(BaseModel):
    inspection_id: str
    report_path: str = Field(..., description="Relative path to the generated PDF.")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = Field(default=3)
    status: str = Field(default="report_generated")
