"""
Pipeline API router — runs the complete inspection pipeline in one request.

Endpoint: POST /api/v1/pipeline/run/{inspection_id}

Chains: Vision → OCR → Comparison → AI → PDF
Saves every stage result and updates the inspection history DB record.
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ai_analysis import AIAnalysisResult
from app.models.comparison import ComparisonResult
from app.models.ocr import OCRResult
from app.models.report import ReportResult
from app.models.vision import VisionResult
from app.services.ai_service import run_ai_analysis
from app.services.comparison_service import run_comparison
from app.services.history_service import create_or_update_inspection
from app.services.ocr_service import extract_text
from app.services.report_service import generate_report
from app.services.vision_service import analyze_inspection
from app.utils.results_store import (
    STAGE_AI, STAGE_COMPARISON, STAGE_OCR, STAGE_REPORT, STAGE_VISION,
    save_result,
)
from pydantic import BaseModel, ConfigDict
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


class PipelineResult(BaseModel):
    """Combined result of the full inspection pipeline."""
    model_config = ConfigDict(protected_namespaces=())
    inspection_id: str
    vision_status: str
    ocr_status: str
    comparison_status: str
    ai_status: str
    report_status: str
    fraud_score: Optional[int] = None
    verdict: Optional[str] = None
    report_path: Optional[str] = None
    overall_quality_ok: Optional[bool] = None
    service_tag: Optional[str] = None
    model_name: Optional[str] = None
    completed_at: datetime = None
    status: str = "pipeline_complete"


@router.post(
    "/run/{inspection_id}",
    response_model=PipelineResult,
    status_code=status.HTTP_200_OK,
    summary="Run the full inspection pipeline",
    description=(
        "Chains all 5 pipeline stages in sequence for the given inspection:\n\n"
        "1. **Vision** — OpenCV image quality + label detection\n"
        "2. **OCR** — PaddleOCR text extraction + Dell field parsing\n"
        "3. **Comparison** — Rules-based field validation\n"
        "4. **AI** — LangGraph + GPT-4.1 reasoning + fraud score\n"
        "5. **PDF** — ReportLab inspection report generation\n\n"
        "Results from each stage are persisted as JSON and in the inspection history DB. "
        "Only the Upload endpoint needs to be called first."
    ),
)
async def run_pipeline(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint."),
    db: Session = Depends(get_db),
) -> PipelineResult:
    """Execute the full 5-stage inspection pipeline."""
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")

    logger.info("Full pipeline started for inspection %s", inspection_id)

    # ── Stage 1: Vision ───────────────────────────────────────────────────────
    try:
        vision: VisionResult = analyze_inspection(inspection_id)
        save_result(inspection_id, STAGE_VISION, vision)
        create_or_update_inspection(
            db, inspection_id,
            front_blur_score=vision.front.quality.blur_score,
            back_blur_score=vision.back.quality.blur_score,
            overall_quality_ok=int(vision.overall_quality_ok),
            pipeline_status="vision_complete",
        )
        vision_status = "ok"
    except Exception as exc:
        logger.exception("Vision stage failed for %s", inspection_id)
        vision_status = f"error: {exc}"

    # ── Stage 2: OCR ──────────────────────────────────────────────────────────
    try:
        ocr: OCRResult = extract_text(inspection_id)
        save_result(inspection_id, STAGE_OCR, ocr)
        f = ocr.combined_dell_fields
        create_or_update_inspection(
            db, inspection_id,
            service_tag=f.service_tag,
            part_number=f.part_number,
            model_name=f.model_name,
            express_service_code=f.express_service_code,
            pipeline_status="ocr_complete",
        )
        ocr_status = "ok"
    except Exception as exc:
        logger.exception("OCR stage failed for %s", inspection_id)
        ocr_status = f"error: {exc}"
        f = None

    # ── Stage 3: Comparison ───────────────────────────────────────────────────
    try:
        comparison: ComparisonResult = run_comparison(inspection_id)
        create_or_update_inspection(
            db, inspection_id,
            comparison_risk_score=comparison.total_risk_score,
            pipeline_status="comparison_complete",
        )
        comparison_status = "ok"
    except Exception as exc:
        logger.exception("Comparison stage failed for %s", inspection_id)
        comparison_status = f"error: {exc}"

    # ── Stage 4: AI Reasoning ─────────────────────────────────────────────────
    try:
        ai: AIAnalysisResult = run_ai_analysis(inspection_id)
        create_or_update_inspection(
            db, inspection_id,
            fraud_score=ai.fraud_score,
            verdict=ai.verdict,
            confidence_level=ai.confidence_level,
            ai_model_used=ai.ai_model_used,
            final_reasoning=ai.final_reasoning,
            pipeline_status="ai_complete",
        )
        ai_status = "ok"
    except Exception as exc:
        logger.exception("AI stage failed for %s", inspection_id)
        ai_status = f"error: {exc}"
        ai = None

    # ── Stage 5: PDF Report ───────────────────────────────────────────────────
    try:
        report: ReportResult = generate_report(inspection_id)
        create_or_update_inspection(
            db, inspection_id,
            report_path=report.report_path,
            completed_at=datetime.utcnow(),
            pipeline_status="complete",
        )
        report_status = "ok"
    except Exception as exc:
        logger.exception("Report stage failed for %s", inspection_id)
        report_status = f"error: {exc}"
        report = None

    logger.info("Full pipeline complete for inspection %s", inspection_id)

    return PipelineResult(
        inspection_id=inspection_id,
        vision_status=vision_status,
        ocr_status=ocr_status,
        comparison_status=comparison_status,
        ai_status=ai_status,
        report_status=report_status,
        fraud_score=ai.fraud_score if ai else None,
        verdict=ai.verdict if ai else None,
        report_path=report.report_path if report else None,
        overall_quality_ok=vision.overall_quality_ok if vision else None,
        service_tag=f.service_tag if f else None,
        model_name=f.model_name if f else None,
        completed_at=datetime.utcnow(),
    )
