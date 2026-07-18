"""
File-validation utilities shared across services.

Keeping validation here (rather than inside the route or service) means
any future service can reuse the same rules without duplication.
"""

import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_image_file(file: UploadFile, field_name: str) -> None:
    """
    Validate content type and presence of an uploaded image file.

    Args:
        file:       The FastAPI UploadFile object to validate.
        field_name: Human-readable field name used in error messages
                    (e.g. "front_image").

    Raises:
        HTTPException 400: If the content type is not an allowed image type.
        HTTPException 400: If the file has no filename.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{field_name}' must have a filename.",
        )

    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"'{field_name}' has unsupported type '{content_type}'. "
                f"Allowed types: {sorted(settings.ALLOWED_CONTENT_TYPES)}."
            ),
        )

    logger.debug("File '%s' passed validation (type=%s).", file.filename, content_type)


def safe_filename(original: str, prefix: str) -> str:
    """
    Build a safe, predictable filename by combining a prefix and the
    original file's extension.

    Args:
        original: The original filename from the client (e.g. "IMG_001.JPG").
        prefix:   Semantic prefix to use (e.g. "front_image", "back_image").

    Returns:
        A sanitised filename such as "front_image.jpg".
    """
    suffix = Path(original).suffix.lower() or ".jpg"
    return f"{prefix}{suffix}"
