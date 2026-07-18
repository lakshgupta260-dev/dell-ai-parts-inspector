"""
Results Store — JSON-based persistence for pipeline stage outputs.

Each pipeline stage saves its Pydantic model output as JSON to
uploads/<inspection_id>/results/<stage_name>.json

This allows:
  1. Each stage to be run independently (for testing or re-runs).
  2. Downstream stages to load upstream results without re-processing.
  3. The full pipeline endpoint to chain all stages.
"""

import json
import logging
from pathlib import Path
from typing import Any, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

STAGE_VISION = "vision"
STAGE_OCR = "ocr"
STAGE_COMPARISON = "comparison"
STAGE_AI = "ai_analysis"
STAGE_REPORT = "report"


def save_result(inspection_id: str, stage: str, result: BaseModel) -> None:
    """
    Persist a Pydantic model to JSON for a given inspection stage.
    
    Args:
        inspection_id: UUID of the inspection.
        stage: Stage name constant (use STAGE_* constants above).
        result: Any Pydantic model instance to persist.
    """
    results_dir = settings.UPLOAD_DIR / inspection_id / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{stage}.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Saved %s result for inspection %s", stage, inspection_id)


def load_result(inspection_id: str, stage: str, model_class: Type[T]) -> T:
    """
    Load a previously saved pipeline stage result.
    
    Args:
        inspection_id: UUID of the inspection.
        stage: Stage name constant.
        model_class: Pydantic model class to deserialize into.
    
    Returns:
        Deserialized Pydantic model instance.
    
    Raises:
        HTTPException 404: If the stage result file does not exist.
        HTTPException 422: If the JSON cannot be parsed.
    """
    path = settings.UPLOAD_DIR / inspection_id / "results" / f"{stage}.json"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Stage '{stage}' has not been run for inspection '{inspection_id}'. "
                f"Run the {stage} endpoint first."
            ),
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return model_class.model_validate(data)
    except Exception as exc:
        logger.exception("Failed to parse %s result for %s", stage, inspection_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Corrupt stage result for '{stage}': {exc}",
        ) from exc


def result_exists(inspection_id: str, stage: str) -> bool:
    """Check whether a given stage result exists without raising."""
    path = settings.UPLOAD_DIR / inspection_id / "results" / f"{stage}.json"
    return path.exists()
