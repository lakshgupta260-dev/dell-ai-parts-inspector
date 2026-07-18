"""
Pydantic models for the OCR Service output.

Data flows: Vision → [OCR] → Comparison → LLM → Score → PDF
Every field extracted here becomes an input to the Comparison Engine.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    """Four-corner bounding box as returned by PaddleOCR."""

    top_left: List[float] = Field(..., description="[x, y] top-left corner.")
    top_right: List[float] = Field(..., description="[x, y] top-right corner.")
    bottom_right: List[float] = Field(..., description="[x, y] bottom-right corner.")
    bottom_left: List[float] = Field(..., description="[x, y] bottom-left corner.")


class TextBlock(BaseModel):
    """Single OCR detection: one text line with its location and confidence."""

    text: str = Field(..., description="Recognised text string.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="OCR engine confidence score (0.0–1.0).",
    )
    bounding_box: BoundingBox = Field(
        ..., description="Quadrilateral bounding box of this text line."
    )


class DellFields(BaseModel):
    """
    Structured Dell-specific fields parsed from raw OCR text.

    All fields are Optional — a missing field is itself a fraud signal
    (e.g., a Dell part with no Service Tag is suspicious).
    """

    model_config = ConfigDict(protected_namespaces=())

    service_tag: Optional[str] = Field(
        None,
        description="7-character alphanumeric Dell Service Tag (e.g. 'ABC1234').",
    )
    express_service_code: Optional[str] = Field(
        None,
        description="11-digit Express Service Code.",
    )
    part_number: Optional[str] = Field(
        None,
        description="Dell Part Number in CN-XXXXXX or 0XXXXXX format.",
    )
    model_name: Optional[str] = Field(
        None,
        description="Dell product model name (e.g. 'OptiPlex 7090', 'XPS 15').",
    )
    regulatory_info: List[str] = Field(
        default_factory=list,
        description="Any FCC IDs, CE marks, or other regulatory strings found.",
    )
    manufacture_date: Optional[str] = Field(
        None,
        description="Manufacture date if present on label (various formats).",
    )
    country_of_origin: Optional[str] = Field(
        None,
        description="Country of origin if present on label.",
    )
    raw_fields: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "All key-value pairs detected on the label using 'KEY: VALUE' or "
            "'KEY VALUE' patterns, before Dell-specific parsing."
        ),
    )


class SingleImageOCR(BaseModel):
    """Complete OCR output for one image (front or back)."""

    image_path: str = Field(..., description="Relative path to the analysed image.")
    text_blocks: List[TextBlock] = Field(
        default_factory=list,
        description="All detected text lines with bounding boxes and confidence.",
    )
    full_text: str = Field(
        ...,
        description="All recognised text concatenated in reading order.",
    )
    dell_fields: DellFields = Field(
        ...,
        description="Structured Dell-specific fields parsed from the raw text.",
    )
    avg_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mean confidence across all detected text blocks.",
    )
    text_block_count: int = Field(
        ..., description="Total number of text lines detected."
    )


class OCRResult(BaseModel):
    """Top-level response model for the OCR Service."""

    inspection_id: str = Field(..., description="UUID linking to the inspection session.")
    front: SingleImageOCR = Field(..., description="OCR results from the front image.")
    back: SingleImageOCR = Field(..., description="OCR results from the back image.")
    combined_dell_fields: DellFields = Field(
        ...,
        description=(
            "Merged Dell fields from both images. Front takes priority; "
            "back fills missing values."
        ),
    )
    status: str = Field(default="ocr_complete", description="Current pipeline stage.")
