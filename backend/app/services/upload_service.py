"""
Upload Service — business logic for image ingestion.

Responsibilities:
  1. Generate a unique inspection ID.
  2. Create a dedicated folder for the inspection.
  3. Stream-write both image files to disk safely.
  4. Return structured metadata consumed by the API layer.

This service deliberately has NO knowledge of HTTP — it receives plain
Python objects and returns plain Python objects.  This makes it trivially
unit-testable and reusable from CLI scripts, background workers, etc.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.upload import UploadResponse
from app.utils.file_utils import safe_filename, validate_image_file

logger = logging.getLogger(__name__)

# Chunk size used when streaming file bytes to disk (256 KB)
_CHUNK_SIZE: int = 256 * 1024


async def save_inspection_images(
    front_image: UploadFile,
    back_image: UploadFile,
) -> UploadResponse:
    """
    Validate, store, and record metadata for a pair of inspection images.

    Args:
        front_image: Uploaded file representing the front of the Dell part.
        back_image:  Uploaded file representing the back of the Dell part.

    Returns:
        UploadResponse with the inspection ID, file paths, and timestamp.

    Raises:
        HTTPException 400: Propagated from file_utils if validation fails.
        HTTPException 500: If an I/O error occurs while writing files.
    """
    # ── 1. Validate both files before touching the filesystem ─────────────────
    validate_image_file(front_image, "front_image")
    validate_image_file(back_image, "back_image")

    # ── 2. Create inspection directory ────────────────────────────────────────
    inspection_id: str = str(uuid.uuid4())
    inspection_dir: Path = settings.UPLOAD_DIR / inspection_id
    inspection_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Created inspection directory: %s", inspection_dir)

    # ── 3. Persist files ──────────────────────────────────────────────────────
    front_filename = safe_filename(front_image.filename, "front_image")  # type: ignore[arg-type]
    back_filename = safe_filename(back_image.filename, "back_image")  # type: ignore[arg-type]

    front_path = inspection_dir / front_filename
    back_path = inspection_dir / back_filename

    await _write_upload(front_image, front_path)
    await _write_upload(back_image, back_path)

    # ── 4. Build relative paths for the response (portable across environments)
    front_relative = str(front_path.relative_to(settings.UPLOAD_DIR.parent))
    back_relative = str(back_path.relative_to(settings.UPLOAD_DIR.parent))

    logger.info(
        "Inspection %s: saved front='%s', back='%s'",
        inspection_id,
        front_relative,
        back_relative,
    )

    return UploadResponse(
        inspection_id=inspection_id,
        front_image_path=front_relative,
        back_image_path=back_relative,
        uploaded_at=datetime.now(tz=timezone.utc),
        status="uploaded",
        message="Images uploaded successfully. Ready for inspection.",
    )


async def _write_upload(upload: UploadFile, destination: Path) -> None:
    """
    Read the UploadFile, downscale it if it exceeds 1280px on the longest side
    to save CPU/memory and API transfer time, and write it to the *destination*.
    """
    try:
        contents = await upload.read()
        import cv2
        import numpy as np

        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is not None:
            h, w = img.shape[:2]
            max_dim = 1280
            if max(h, w) > max_dim:
                if w > h:
                    new_w = max_dim
                    new_h = int(h * (max_dim / w))
                else:
                    new_h = max_dim
                    new_w = int(w * (max_dim / h))
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                logger.info("Downscaled image '%s' from %dx%d to %dx%d", destination.name, w, h, new_w, new_h)

            ext = destination.suffix.lower()
            params = []
            if ext in [".jpg", ".jpeg"]:
                params = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            elif ext == ".webp":
                params = [int(cv2.IMWRITE_WEBP_QUALITY), 85]

            success = cv2.imwrite(str(destination), img, params)
            if not success:
                logger.warning("cv2.imwrite failed, falling back to writing raw bytes for %s", destination.name)
                with destination.open("wb") as out_file:
                    out_file.write(contents)
        else:
            # Fallback if cv2 fails to decode
            with destination.open("wb") as out_file:
                out_file.write(contents)

    except Exception as exc:
        logger.exception("Failed to process and write file to %s", destination)
        from fastapi import HTTPException, status  # local import avoids circular deps
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file '{destination.name}': {exc}",
        ) from exc
    finally:
        await upload.seek(0)  # reset cursor in case the object is reused
