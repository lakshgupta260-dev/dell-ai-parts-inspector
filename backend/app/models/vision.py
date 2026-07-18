"""
Pydantic models for the Computer Vision analysis results.

These models define the exact shape of data that flows from the
Vision Service → OCR Service → AI Reasoning → PDF Report.
They are intentionally rich so downstream stages have everything they need.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ImageQuality(BaseModel):
    """Low-level quality metrics for a single image."""

    width: int = Field(..., description="Image width in pixels.")
    height: int = Field(..., description="Image height in pixels.")
    channels: int = Field(..., description="Number of colour channels (1=gray, 3=BGR).")
    blur_score: float = Field(
        ...,
        description=(
            "Laplacian variance — higher is sharper. "
            "< 100 → blurry, 100–500 → acceptable, > 500 → sharp."
        ),
    )
    is_blurry: bool = Field(
        ..., description="True when blur_score is below the 100-unit threshold."
    )
    mean_brightness: float = Field(
        ..., description="Mean pixel intensity (0–255). < 50 → dark, > 200 → overexposed."
    )
    contrast_score: float = Field(
        ..., description="Standard deviation of pixel intensities (0–255)."
    )


class LabelRegion(BaseModel):
    """Bounding box of a detected rectangular label / sticker region."""

    x: int = Field(..., description="Left edge of the bounding box (pixels).")
    y: int = Field(..., description="Top edge of the bounding box (pixels).")
    width: int = Field(..., description="Width of the bounding box (pixels).")
    height: int = Field(..., description="Height of the bounding box (pixels).")
    area: int = Field(..., description="Area of the bounding box in pixels².")
    confidence: float = Field(
        ...,
        description=(
            "Confidence that this is a label region (0.0–1.0), derived from "
            "the contour's rectangularity score."
        ),
    )


class ColorAnalysis(BaseModel):
    """Per-channel colour statistics for a single image."""

    mean_blue: float = Field(..., description="Mean value of the Blue channel (0–255).")
    mean_green: float = Field(..., description="Mean value of the Green channel (0–255).")
    mean_red: float = Field(..., description="Mean value of the Red channel (0–255).")
    std_blue: float = Field(..., description="Std-dev of the Blue channel.")
    std_green: float = Field(..., description="Std-dev of the Green channel.")
    std_red: float = Field(..., description="Std-dev of the Red channel.")
    dominant_color_rgb: List[int] = Field(
        ...,
        description="Most dominant colour as [R, G, B] (k-means cluster centre).",
    )


class SingleImageAnalysis(BaseModel):
    """Complete vision analysis output for one image (front or back)."""

    image_path: str = Field(..., description="Relative path to the analysed image.")
    quality: ImageQuality
    color: ColorAnalysis
    label_regions: List[LabelRegion] = Field(
        default_factory=list,
        description="All rectangular label/sticker regions detected in the image.",
    )
    edge_density: float = Field(
        ...,
        description=(
            "Fraction of edge pixels detected by Canny (0.0–1.0). "
            "Authentic parts typically score > 0.05."
        ),
    )
    quality_flags: List[str] = Field(
        default_factory=list,
        description="Human-readable warnings about image quality issues.",
    )


class VisionResult(BaseModel):
    """Top-level response model for the Vision Service."""

    inspection_id: str = Field(..., description="UUID linking to the upload session.")
    front: SingleImageAnalysis = Field(..., description="Analysis of the front image.")
    back: SingleImageAnalysis = Field(..., description="Analysis of the back image.")
    overall_quality_ok: bool = Field(
        ...,
        description=(
            "True when BOTH images are sharp enough and bright enough "
            "to proceed to OCR. False halts the pipeline early."
        ),
    )
    vision_flags: List[str] = Field(
        default_factory=list,
        description="Aggregated quality warnings from both images.",
    )
    status: str = Field(
        default="vision_complete",
        description="Current pipeline stage.",
    )
