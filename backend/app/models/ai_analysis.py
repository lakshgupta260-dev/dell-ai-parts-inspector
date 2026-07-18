"""
Pydantic models for the AI Reasoning and Fraud Score output.
"""

from typing import List
from pydantic import BaseModel, Field


class AIAnalysisResult(BaseModel):
    """Full AI reasoning and fraud scoring output."""
    inspection_id: str
    visual_analysis: str = Field(..., description="AI interpretation of vision signals.")
    text_analysis: str = Field(..., description="AI interpretation of OCR/field signals.")
    discrepancy_analysis: str = Field(..., description="AI interpretation of comparison discrepancies.")
    final_reasoning: str = Field(..., description="Final synthesised reasoning paragraph.")
    fraud_score: int = Field(..., ge=0, le=100, description="Fraud probability score 0-100.")
    verdict: str = Field(..., description="AUTHENTIC | SUSPICIOUS | COUNTERFEIT")
    confidence_level: str = Field(..., description="HIGH | MEDIUM | LOW AI confidence.")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations.")
    ai_model_used: str = Field(default="gpt-4.1", description="LLM model used for reasoning.")
    status: str = Field(default="ai_complete")
