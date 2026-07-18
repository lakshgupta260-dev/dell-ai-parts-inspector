"""
Pydantic models for the Image Upload feature.

These schemas define the API contract — what the client sends and what
the server guarantees to return.  They are intentionally separate from
any database models (added in a later milestone).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Successful response after uploading inspection images."""

    inspection_id: str = Field(
        ...,
        description="Unique identifier for this inspection session (UUID-4).",
        examples=["3f2504e0-4f89-11d3-9a0c-0305e82c3301"],
    )
    front_image_path: str = Field(
        ...,
        description="Relative path to the stored front image.",
        examples=["uploads/3f2504e0.../front_image.jpg"],
    )
    back_image_path: str = Field(
        ...,
        description="Relative path to the stored back image.",
        examples=["uploads/3f2504e0.../back_image.jpg"],
    )
    uploaded_at: datetime = Field(
        ...,
        description="UTC timestamp when the images were received.",
    )
    status: str = Field(
        default="uploaded",
        description="Current pipeline stage for this inspection.",
    )
    message: str = Field(
        default="Images uploaded successfully. Ready for inspection.",
        description="Human-readable status message.",
    )


class ErrorResponse(BaseModel):
    """Standardised error envelope returned for all 4xx / 5xx responses."""

    detail: str = Field(..., description="Machine-readable error message.")
    status_code: int = Field(..., description="HTTP status code.")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the error.",
    )
