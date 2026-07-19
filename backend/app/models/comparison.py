"""
Pydantic models for the Comparison Engine output.

The Comparison Engine checks OCR-extracted Dell fields against known
authenticity rules and flags any discrepancies.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FieldCheck(BaseModel):
    """Result of validating one specific Dell label field."""
    field_name: str = Field(..., description="Name of the field checked.")
    extracted_value: Optional[str] = Field(None, description="Value extracted by OCR.")
    is_present: bool = Field(..., description="Whether the field was found.")
    is_valid_format: bool = Field(..., description="Whether the value matches the expected format.")
    expected_format: str = Field(..., description="Human-readable description of expected format.")
    flags: List[str] = Field(default_factory=list, description="Any warnings or anomalies for this field.")
    risk_contribution: int = Field(
        default=0,
        ge=0, le=50,
        description="How much this field contributes to the fraud risk score (0-50)."
    )


class ComparisonResult(BaseModel):
    """Full output of the Comparison Engine."""
    inspection_id: str
    field_checks: List[FieldCheck] = Field(default_factory=list)
    total_risk_score: int = Field(
        default=0, ge=0, le=100,
        description="Aggregated risk score from all field checks (0-100)."
    )
    missing_critical_fields: List[str] = Field(
        default_factory=list,
        description="Names of mandatory Dell fields that were not found."
    )
    format_violations: List[str] = Field(
        default_factory=list,
        description="Field names whose values fail the expected format."
    )
    comparison_summary: str = Field(
        default="",
        description="Human-readable summary of the comparison result."
    )
    golden_reference_used: Optional[str] = Field(
        default=None,
        description="The name of the golden profile used as a reference (e.g. 'latitude')."
    )
    similarity_metrics: dict = Field(
        default_factory=dict,
        description="Scores comparing the upload to the golden reference (e.g., ocr_similarity, vision_match, anomaly_score)."
    )
    status: str = Field(default="comparison_complete")
