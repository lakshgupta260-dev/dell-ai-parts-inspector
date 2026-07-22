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


import asyncio
import json
from fastapi.responses import StreamingResponse

@router.post(
    "/run/{inspection_id}",
    summary="Run the full inspection pipeline (SSE)",
    description=(
        "Chains all 5 pipeline stages in sequence for the given inspection, "
        "streaming progress back via Server-Sent Events (SSE). "
        "Vision and OCR are run concurrently to save time."
    ),
)
async def run_pipeline(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint."),
    db: Session = Depends(get_db),
):
    """Execute the full 5-stage inspection pipeline using SSE."""
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")

    logger.info("Full pipeline started for inspection %s", inspection_id)

    async def event_generator():
        # Start event
        yield f"data: {json.dumps({'stage': 'started'})}\\n\\n"
        
        vision = None
        ocr = None
        comparison = None
        ai = None
        report = None
        
        vision_status = "pending"
        ocr_status = "pending"
        comparison_status = "pending"
        ai_status = "pending"
        report_status = "pending"
        f = None

        # ── Stage 1 & 2: Vision and OCR (Concurrent) ─────────────────────────
        async def run_vision():
            try:
                v = await asyncio.to_thread(analyze_inspection, inspection_id)
                await asyncio.to_thread(save_result, inspection_id, STAGE_VISION, v)
                return "ok", v
            except Exception as e:
                logger.exception("Vision stage failed")
                return f"error: {e}", None

        async def run_ocr():
            try:
                o = await asyncio.to_thread(extract_text, inspection_id)
                await asyncio.to_thread(save_result, inspection_id, STAGE_OCR, o)
                return "ok", o
            except Exception as e:
                logger.exception("OCR stage failed")
                return f"error: {e}", None

        (v_stat, vision), (o_stat, ocr) = await asyncio.gather(run_vision(), run_ocr())
        vision_status = v_stat
        ocr_status = o_stat
        
        if vision:
            create_or_update_inspection(
                db, inspection_id,
                front_blur_score=vision.front.quality.blur_score,
                back_blur_score=vision.back.quality.blur_score,
                overall_quality_ok=int(vision.overall_quality_ok),
                pipeline_status="vision_complete",
            )
        if ocr:
            f = ocr.combined_dell_fields
            create_or_update_inspection(
                db, inspection_id,
                service_tag=f.service_tag,
                part_number=f.part_number,
                model_name=f.model_name,
                express_service_code=f.express_service_code,
                pipeline_status="ocr_complete",
            )
            
        yield f"data: {json.dumps({'stage': 'vision', 'status': vision_status})}\\n\\n"
        yield f"data: {json.dumps({'stage': 'ocr', 'status': ocr_status})}\\n\\n"

        # ── Stage 3: Comparison ───────────────────────────────────────────────────
        try:
            comparison = await asyncio.to_thread(run_comparison, inspection_id)
            create_or_update_inspection(
                db, inspection_id,
                comparison_risk_score=comparison.total_risk_score,
                pipeline_status="comparison_complete",
            )
            comparison_status = "ok"
        except Exception as exc:
            logger.exception("Comparison stage failed")
            comparison_status = f"error: {exc}"
            
        yield f"data: {json.dumps({'stage': 'comparison', 'status': comparison_status})}\\n\\n"

        # ── Stage 4: AI Reasoning ─────────────────────────────────────────────────
        try:
            ai = await asyncio.to_thread(run_ai_analysis, inspection_id)
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
            logger.exception("AI stage failed")
            ai_status = f"error: {exc}"
            
        yield f"data: {json.dumps({'stage': 'ai', 'status': ai_status})}\\n\\n"

        # ── Stage 5: PDF Report ───────────────────────────────────────────────────
        try:
            report = await asyncio.to_thread(generate_report, inspection_id)
            create_or_update_inspection(
                db, inspection_id,
                report_path=report.report_path,
                completed_at=datetime.utcnow(),
                pipeline_status="complete",
            )
            report_status = "ok"
        except Exception as exc:
            logger.exception("Report stage failed")
            report_status = f"error: {exc}"
            
        yield f"data: {json.dumps({'stage': 'report', 'status': report_status})}\\n\\n"

        # Final Payload
        final_payload = {
            "stage": "complete",
            "result": {
                "inspection_id": inspection_id,
                "vision_status": vision_status,
                "ocr_status": ocr_status,
                "comparison_status": comparison_status,
                "ai_status": ai_status,
                "report_status": report_status,
                "fraud_score": ai.fraud_score if ai else None,
                "verdict": ai.verdict if ai else None,
                "report_path": report.report_path if report else None,
                "overall_quality_ok": vision.overall_quality_ok if vision else None,
                "service_tag": f.service_tag if f else None,
                "model_name": f.model_name if f else None,
            }
        }
        yield f"data: {json.dumps(final_payload)}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
