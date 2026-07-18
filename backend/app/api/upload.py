"""
Upload API router — HTTP layer only.

This module is intentionally thin:
  - Parse/validate HTTP inputs.
  - Delegate ALL business logic to upload_service.
  - Format and return HTTP responses.

No file I/O, no UUID generation, no path logic lives here.
"""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.models.upload import ErrorResponse, UploadResponse
from app.services.upload_service import save_inspection_images

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])


@router.post(
    "/inspection",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload inspection images",
    description=(
        "Accepts a **front** and **back** image of a Dell hardware part. "
        "Both images must be JPEG, PNG, WebP, or TIFF and under 10 MB each. "
        "Returns an `inspection_id` that is used as the key for all subsequent "
        "pipeline stages (Vision → OCR → AI Reasoning → PDF → Notifications)."
    ),
    responses={
        201: {"model": UploadResponse, "description": "Images stored successfully."},
        400: {"model": ErrorResponse, "description": "Validation error."},
        500: {"model": ErrorResponse, "description": "Server-side I/O error."},
    },
)
async def upload_inspection_images(
    front_image: UploadFile = File(
        ...,
        description="Front-facing photo of the Dell hardware part (JPEG/PNG/WebP/TIFF, max 10 MB).",
    ),
    back_image: UploadFile = File(
        ...,
        description="Rear-facing photo of the Dell hardware part (JPEG/PNG/WebP/TIFF, max 10 MB).",
    ),
) -> UploadResponse:
    """
    Upload front and back images for a new inspection session.

    - **front_image**: Required. Photo of the front of the Dell part.
    - **back_image**: Required. Photo of the back of the Dell part.

    Returns a unique `inspection_id` that tracks this part through the
    entire AI pipeline.
    """
    logger.info(
        "Received upload request — front='%s', back='%s'",
        front_image.filename,
        back_image.filename,
    )

    result: UploadResponse = await save_inspection_images(front_image, back_image)
    return result
