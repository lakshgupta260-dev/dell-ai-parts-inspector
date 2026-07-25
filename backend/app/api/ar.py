"""
AR 3D Model API router.

Endpoints:
  POST /api/v1/ar/generate/{inspection_id}  - Generates a 3D model via Tripo3D
  GET  /api/v1/ar/download/{inspection_id}  - Downloads the generated .glb file
  GET  /api/v1/ar/status/{inspection_id}    - Checks if a model already exists
"""
import os
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.tripo3d_service import generate_3d_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ar", tags=["AR 3D Models"])


class ARResponse(BaseModel):
    status: str
    message: str
    model_url: str | None = None


def _get_upload_base() -> str:
    """Returns the absolute path to the 'uploads' directory."""
    return os.path.join(
        os.path.dirname(  # backend/
            os.path.dirname(  # app/
                os.path.dirname(  # api/
                    os.path.abspath(__file__)
                )
            )
        ),
        "uploads",
    )


@router.post("/generate/{inspection_id}", response_model=ARResponse)
async def generate_model(inspection_id: str):
    """
    On-demand endpoint to generate a 3D model from the front image using Tripo3D AI.
    Blocks for 15-30 seconds while generation is in progress.
    """
    inspection_dir = os.path.join(_get_upload_base(), inspection_id)

    # Find the front image (try common extensions)
    front_img_path = None
    for ext in ["jpeg", "jpg", "png"]:
        path = os.path.join(inspection_dir, f"front_image.{ext}")
        if os.path.exists(path):
            front_img_path = path
            break

    if not front_img_path:
        raise HTTPException(
            status_code=404,
            detail=f"Front image not found for inspection '{inspection_id}'. "
                   "Make sure the inspection upload is complete.",
        )

    try:
        generate_3d_model(inspection_id, front_img_path, output_dir=inspection_dir)
        model_url = f"/api/v1/ar/download/{inspection_id}"
        return ARResponse(
            status="success",
            message="3D model generated successfully.",
            model_url=model_url,
        )
    except Exception as e:
        logger.error("Error generating 3D model for %s: %s", inspection_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{inspection_id}", summary="Download generated .glb 3D model")
async def download_model(inspection_id: str):
    """Returns the binary .glb file for use in the AR viewer."""
    model_path = os.path.join(_get_upload_base(), inspection_id, f"{inspection_id}.glb")
    if not os.path.exists(model_path):
        raise HTTPException(
            status_code=404,
            detail=f"3D model not found for '{inspection_id}'. Run /generate first.",
        )
    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename=f"dell_part_{inspection_id[:8]}.glb",
    )


@router.get("/status/{inspection_id}", summary="Check if 3D model exists")
async def check_model_status(inspection_id: str):
    """
    Returns whether a 3D model has already been generated for this inspection,
    so the frontend can skip the generation step if the model already exists.
    """
    model_path = os.path.join(_get_upload_base(), inspection_id, f"{inspection_id}.glb")
    if os.path.exists(model_path):
        return {"exists": True, "model_url": f"/api/v1/ar/download/{inspection_id}"}
    return {"exists": False}
