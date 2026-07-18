"""
AI Analysis API router.
Endpoint: POST /api/v1/ai/analyze/{inspection_id}
"""
import logging, uuid
from fastapi import APIRouter, HTTPException, Path, status
from app.models.ai_analysis import AIAnalysisResult
from app.services.ai_service import run_ai_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai", tags=["AI Reasoning"])

@router.post(
    "/analyze/{inspection_id}",
    response_model=AIAnalysisResult,
    summary="Run LangGraph AI reasoning and generate fraud score",
    description=(
        "Uses a LangGraph agentic workflow with GPT-4.1 to analyse all upstream signals "
        "(Vision + OCR + Comparison) and produce a fraud score (0-100), verdict "
        "(AUTHENTIC/SUSPICIOUS/COUNTERFEIT), detailed reasoning, and recommendations. "
        "Falls back to rule-based scoring if OPENAI_API_KEY is not configured. "
        "Run Vision, OCR, and Comparison endpoints first."
    ),
)
async def ai_analyze(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint.")
) -> AIAnalysisResult:
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"'{inspection_id}' is not a valid UUID.")
    logger.info("AI analysis requested for %s", inspection_id)
    return run_ai_analysis(inspection_id)
