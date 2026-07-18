"""
Report API router.
Endpoints:
  POST /api/v1/report/generate/{inspection_id}
  GET  /api/v1/report/download/{inspection_id}
"""
import logging, uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Path as FPath, status
from fastapi.responses import FileResponse
from app.core.config import settings
from app.models.report import ReportResult
from app.services.report_service import generate_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/report", tags=["Report"])

@router.post(
    "/generate/{inspection_id}",
    response_model=ReportResult,
    summary="Generate PDF inspection report",
    description="Generates a 3-page PDF report from all upstream pipeline results. Run Vision, OCR, Comparison, and AI first.",
)
async def generate(
    inspection_id: str = FPath(..., description="UUID from the Upload endpoint.")
) -> ReportResult:
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")
    logger.info("Report generation requested for %s", inspection_id)
    return generate_report(inspection_id)


@router.get(
    "/download/{inspection_id}",
    summary="Download the generated PDF report",
    description="Returns the PDF file. Run the generate endpoint first.",
)
async def download(
    inspection_id: str = FPath(..., description="UUID from the Upload endpoint.")
) -> FileResponse:
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")
    pdf_path = settings.UPLOAD_DIR / inspection_id / "reports" / "inspection_report.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report not found for inspection '{inspection_id}'. Run /generate first."
        )
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"dell_inspection_{inspection_id[:8]}.pdf",
    )
