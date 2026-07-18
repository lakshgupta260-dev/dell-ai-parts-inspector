"""
Image loading utilities shared across services.

Centralising image I/O here means:
  - Vision, OCR, and Comparison services all load images the same way.
  - Error messages are consistent.
  - Switching from disk to object storage later requires changing ONE file.
"""

import logging
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def load_image_bgr(relative_path: str) -> np.ndarray:
    """
    Load an image from a relative path (relative to backend root) into a
    BGR NumPy array suitable for OpenCV processing.

    Args:
        relative_path: Path relative to the backend root directory,
                       e.g. "uploads/<uuid>/front_image.jpg".

    Returns:
        NumPy ndarray in BGR colour order, shape (H, W, C).

    Raises:
        HTTPException 404: If the file does not exist.
        HTTPException 422: If OpenCV cannot decode the file.
    """
    # Resolve relative to the backend root (two levels above app/)
    backend_root = Path(__file__).resolve().parents[2]
    abs_path = backend_root / relative_path

    if not abs_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file not found: '{relative_path}'.",
        )

    image = cv2.imread(str(abs_path))
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not decode image at '{relative_path}'. File may be corrupt.",
        )

    logger.debug("Loaded image %s — shape=%s", relative_path, image.shape)
    return image


def get_inspection_image_paths(inspection_id: str) -> Tuple[str, str]:
    """
    Resolve front and back image relative paths for a given inspection_id.

    Searches the uploads/<inspection_id>/ directory for files whose
    stem starts with 'front_image' and 'back_image' respectively.

    Args:
        inspection_id: UUID string of the inspection session.

    Returns:
        Tuple of (front_relative_path, back_relative_path).

    Raises:
        HTTPException 404: If the inspection directory or either image is missing.
    """
    inspection_dir = settings.UPLOAD_DIR / inspection_id

    if not inspection_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found. Upload images first.",
        )

    front_files = list(inspection_dir.glob("front_image.*"))
    back_files = list(inspection_dir.glob("back_image.*"))

    if not front_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Front image missing for inspection '{inspection_id}'.",
        )
    if not back_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Back image missing for inspection '{inspection_id}'.",
        )

    # Return paths relative to the backend root for portability
    backend_root = Path(__file__).resolve().parents[2]
    front_rel = str(front_files[0].relative_to(backend_root))
    back_rel = str(back_files[0].relative_to(backend_root))

    logger.debug(
        "Resolved paths for inspection %s — front=%s, back=%s",
        inspection_id,
        front_rel,
        back_rel,
    )
    return front_rel, back_rel
