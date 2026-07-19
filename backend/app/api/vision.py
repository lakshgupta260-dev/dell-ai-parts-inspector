"""
Vision API router — HTTP layer only.

Exposes a single endpoint:
  POST /api/v1/vision/analyze/{inspection_id}

The route validates the inspection_id format, delegates to vision_service,
and returns the structured VisionResult.  No OpenCV code lives here.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Path, status

from app.models.upload import ErrorResponse
from app.models.vision import VisionResult
from app.services.vision_service import analyze_inspection
from app.utils.results_store import STAGE_VISION, save_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vision", tags=["Vision"])


@router.post(
    "/analyze/{inspection_id}",
    response_model=VisionResult,
    status_code=status.HTTP_200_OK,
    summary="Run computer vision analysis on uploaded images",
    description=(
        "Runs a 5-step OpenCV pipeline on the front and back images "
        "associated with the given `inspection_id`:\n\n"
        "1. **Image quality** — blur score (Laplacian), brightness, contrast\n"
        "2. **Colour analysis** — per-channel stats, dominant colour (k-means)\n"
        "3. **Label region detection** — rectangular sticker/label bounding boxes\n"
        "4. **Edge density** — Canny edge fraction (authentic labels > 0.05)\n"
        "5. **Quality flags** — human-readable warnings if image quality is poor\n\n"
        "The returned `VisionResult` feeds directly into the OCR stage."
    ),
    responses={
        200: {"model": VisionResult, "description": "Vision analysis complete."},
        400: {"model": ErrorResponse, "description": "Invalid inspection_id format."},
        404: {"model": ErrorResponse, "description": "Inspection or images not found."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
def analyze_inspection_images(
    inspection_id: str = Path(
        ...,
        description="UUID of the inspection session returned by the Upload endpoint.",
        examples=["3f2504e0-4f89-11d3-9a0c-0305e82c3301"],
    ),
) -> VisionResult:
    """
    Trigger computer vision analysis for an existing inspection session.

    - **inspection_id**: Must be a valid UUID-4 returned by the upload endpoint.

    Returns a `VisionResult` with per-image quality metrics, label regions,
    colour statistics, and an `overall_quality_ok` flag that indicates whether
    the images are good enough for the OCR stage.
    """
    # Validate UUID format
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{inspection_id}' is not a valid UUID.",
        )

    logger.info("Vision analysis requested for inspection_id=%s", inspection_id)

    result: VisionResult = analyze_inspection(inspection_id)
    save_result(inspection_id, STAGE_VISION, result)
    return result
