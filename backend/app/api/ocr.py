"""
OCR API router — HTTP layer only.

Exposes a single endpoint:
  POST /api/v1/ocr/extract/{inspection_id}

The route validates the inspection_id format, delegates all work to
ocr_service, and returns the structured OCRResult.
No PaddleOCR code lives here.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Path, status

from app.models.ocr import OCRResult
from app.models.upload import ErrorResponse
from app.services.ocr_service import extract_text
from app.utils.results_store import STAGE_OCR, save_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])


@router.post(
    "/extract/{inspection_id}",
    response_model=OCRResult,
    status_code=status.HTTP_200_OK,
    summary="Extract text from inspection images using PaddleOCR",
    description=(
        "Runs PaddleOCR on the front and back images of an inspection and "
        "extracts structured Dell label fields:\n\n"
        "- **Service Tag** — 7-character alphanumeric identifier\n"
        "- **Express Service Code** — 11-digit numeric code\n"
        "- **Part Number** — CN-XXXXXX or 0XXXXXX format\n"
        "- **Model Name** — OptiPlex, Latitude, XPS, Precision, etc.\n"
        "- **Regulatory info** — FCC ID, CE marks\n"
        "- **Raw key-value pairs** — all other label fields\n\n"
        "Returns per-image text blocks with bounding boxes and confidence scores, "
        "plus a merged `combined_dell_fields` from both images. "
        "Run the **Upload** and **Vision** endpoints first."
    ),
    responses={
        200: {"model": OCRResult, "description": "OCR extraction complete."},
        400: {"model": ErrorResponse, "description": "Invalid inspection_id format."},
        404: {"model": ErrorResponse, "description": "Inspection or images not found."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    },
)
async def extract_inspection_text(
    inspection_id: str = Path(
        ...,
        description="UUID of the inspection session returned by the Upload endpoint.",
        examples=["3f2504e0-4f89-11d3-9a0c-0305e82c3301"],
    ),
) -> OCRResult:
    """
    Extract and parse text from both inspection images.

    - **inspection_id**: Must be a valid UUID-4 returned by the Upload endpoint.

    Returns an `OCRResult` containing all recognised text blocks with their
    bounding boxes and confidence scores, plus structured Dell-specific fields
    merged from both images into `combined_dell_fields`.
    """
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{inspection_id}' is not a valid UUID.",
        )

    logger.info("OCR extraction requested for inspection_id=%s", inspection_id)
    result: OCRResult = extract_text(inspection_id)
    save_result(inspection_id, STAGE_OCR, result)
    return result
