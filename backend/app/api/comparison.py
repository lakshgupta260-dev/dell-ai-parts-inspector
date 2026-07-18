"""
Comparison API router.
Endpoint: POST /api/v1/comparison/analyze/{inspection_id}
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, Path, status
from app.models.comparison import ComparisonResult
from app.services.comparison_service import run_comparison

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/comparison", tags=["Comparison"])


@router.post(
    "/analyze/{inspection_id}",
    response_model=ComparisonResult,
    status_code=status.HTTP_200_OK,
    summary="Run comparison engine on OCR results",
    description=(
        "Validates OCR-extracted Dell fields against authenticity rules. "
        "Requires the OCR stage to have been run first. "
        "Checks Service Tag (7-char), ESC (11-digit), Part Number format, "
        "Model family membership, and OCR confidence. "
        "Returns a per-field risk breakdown and total risk score."
    ),
)
async def analyze_comparison(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint.")
) -> ComparisonResult:
    """Validate Dell label fields for the given inspection."""
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"'{inspection_id}' is not a valid UUID.")
    logger.info("Comparison requested for %s", inspection_id)
    return run_comparison(inspection_id)
