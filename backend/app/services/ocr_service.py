"""
OCR Service — text extraction using PaddleOCR v3.

Pipeline position: Upload → Vision → [OCR] → Comparison → LLM → Score → PDF

Responsibilities:
  1. Load front and back images for a given inspection_id.
  2. Run PaddleOCR v3 on each image to get text blocks (bbox + text + confidence).
  3. Reconstruct full text in reading order.
  4. Parse Dell-specific fields using dell_parser.
  5. Merge fields from both images into a single combined result.
  6. Return a structured OCRResult.

Design notes:
  - PaddleOCR is initialised ONCE as a module-level singleton to avoid
    reloading model weights (~300 MB) on every request.
  - The engine is initialised lazily on first use, not at import time,
    so the server starts fast even before the first request.
  - PaddleOCR v3 API uses engine.ocr(image) which returns a list of
    dict-like OCRResult objects with keys: rec_texts, rec_scores, rec_polys.
  - This service is pure Python — no FastAPI / HTTP imports.
"""

import logging
from statistics import mean
from typing import List, Optional

import numpy as np

from app.models.ocr import BoundingBox, OCRResult, SingleImageOCR, TextBlock
from app.utils.dell_parser import merge_dell_fields, parse_dell_fields
from app.utils.image_utils import get_inspection_image_paths, load_image_bgr

logger = logging.getLogger(__name__)

# ── PaddleOCR singleton ────────────────────────────────────────────────────────
# Initialised lazily on first call to avoid blocking server startup.
_ocr_engine = None


def _get_ocr_engine():
    """
    Return the shared PaddleOCR v3 engine, initialising it on first call.

    PaddleOCR v3 (paddleocr >= 3.0) changed its API significantly:
      - No show_log / use_angle_cls arguments.
      - use_textline_orientation replaces use_angle_cls.
      - use_doc_orientation_classify and use_doc_unwarping are new switches.
      - engine.ocr(image) returns a list of dict-like OCRResult objects.
    """
    global _ocr_engine
    if _ocr_engine is None:
        logger.info("Initialising PaddleOCR v3 engine (first call — downloads model weights)...")
        from paddleocr import PaddleOCR  # deferred import keeps server startup fast

        _ocr_engine = PaddleOCR(
            use_doc_orientation_classify=False,  # skip document-level orientation (hardware labels are usually upright)
            use_doc_unwarping=False,             # skip geometric unwarping
            use_textline_orientation=False,      # disable rotated line checking to improve performance
            lang="en",
            enable_mkldnn=False,                 # FIX: Disable OneDNN to prevent PIR attribute conversion crash on PaddlePaddle 3.x
        )
        logger.info("PaddleOCR v3 engine ready (MKLDNN disabled).")
    return _ocr_engine


# ── Public entry point ────────────────────────────────────────────────────────

def extract_text(inspection_id: str) -> OCRResult:
    """
    Run OCR on both images of an inspection and extract structured Dell fields.

    Args:
        inspection_id: UUID string identifying the upload session.

    Returns:
        OCRResult with per-image text blocks, Dell fields, and merged combined fields.

    Raises:
        HTTPException 404: Propagated from image_utils if files are missing.
    """
    front_rel, back_rel = get_inspection_image_paths(inspection_id)
    logger.info("OCR extraction started for inspection %s", inspection_id)

    front_img = load_image_bgr(front_rel)
    back_img = load_image_bgr(back_rel)

    front_ocr = _process_single_image(front_img, front_rel)
    back_ocr = _process_single_image(back_img, back_rel)

    combined = merge_dell_fields(front_ocr.dell_fields, back_ocr.dell_fields)

    logger.info(
        "OCR complete for %s — front_blocks=%d, back_blocks=%d",
        inspection_id,
        front_ocr.text_block_count,
        back_ocr.text_block_count,
    )

    return OCRResult(
        inspection_id=inspection_id,
        front=front_ocr,
        back=back_ocr,
        combined_dell_fields=combined,
        status="ocr_complete",
    )


# ── Per-image processing ──────────────────────────────────────────────────────

def _process_single_image(image: np.ndarray, image_path: str) -> SingleImageOCR:
    """
    Run PaddleOCR v3 on one image, parse raw results, and extract Dell fields.

    Args:
        image:      BGR NumPy array.
        image_path: Relative path (for record-keeping only).

    Returns:
        SingleImageOCR with text_blocks, full_text, dell_fields, and statistics.
    """
    engine = _get_ocr_engine()
    raw_results = engine.ocr(image)  # returns List[OCRResult dict-like]

    text_blocks: List[TextBlock] = _parse_paddle_v3_output(raw_results)
    full_text = _reconstruct_text(text_blocks)
    dell_fields = parse_dell_fields(full_text)

    confidences = [b.confidence for b in text_blocks] if text_blocks else [0.0]
    avg_conf = round(mean(confidences), 4)

    return SingleImageOCR(
        image_path=image_path,
        text_blocks=text_blocks,
        full_text=full_text,
        dell_fields=dell_fields,
        avg_confidence=avg_conf,
        text_block_count=len(text_blocks),
    )


# ── PaddleOCR v3 output parsing ───────────────────────────────────────────────

def _parse_paddle_v3_output(raw: Optional[list]) -> List[TextBlock]:
    """
    Convert PaddleOCR v3's dict-like OCRResult list into clean TextBlock objects.

    PaddleOCR v3 returns:
        [ OCRResult{rec_texts: [...], rec_scores: [...], rec_polys: [...]} ]
        where rec_polys is a list of 4-point polygon arrays: shape (4, 2).

    Args:
        raw: Raw return value from engine.ocr().

    Returns:
        Flat list of TextBlock objects sorted top-to-bottom, left-to-right.
    """
    blocks: List[TextBlock] = []

    if not raw:
        logger.warning("PaddleOCR returned empty results for this image.")
        return blocks

    for page_result in raw:
        if page_result is None:
            continue

        # PaddleOCR v3 result is a dict-like object with these keys:
        # rec_texts, rec_scores, rec_polys (4-point polygons)
        try:
            texts = page_result.get("rec_texts", [])
            scores = page_result.get("rec_scores", [])
            polys = page_result.get("rec_polys", [])
        except (AttributeError, TypeError):
            logger.warning("Unexpected PaddleOCR result type: %s", type(page_result))
            continue

        if not texts:
            logger.info("No text detected in this image.")
            continue

        for text, score, poly in zip(texts, scores, polys):
            text = str(text).strip()
            if not text:
                continue

            # poly shape: (4, 2) — TL, TR, BR, BL in pixel coordinates
            try:
                poly_list = poly.tolist() if hasattr(poly, "tolist") else list(poly)
                tl, tr, br, bl = poly_list[0], poly_list[1], poly_list[2], poly_list[3]
            except (IndexError, TypeError, ValueError) as exc:
                logger.warning("Malformed polygon for text '%s': %s", text, exc)
                tl = tr = br = bl = [0.0, 0.0]

            blocks.append(
                TextBlock(
                    text=text,
                    confidence=round(float(score), 4),
                    bounding_box=BoundingBox(
                        top_left=tl,
                        top_right=tr,
                        bottom_right=br,
                        bottom_left=bl,
                    ),
                )
            )

    # Sort by vertical position (top-left y) then horizontal (top-left x)
    blocks.sort(key=lambda b: (b.bounding_box.top_left[1], b.bounding_box.top_left[0]))
    logger.debug("Parsed %d text blocks from PaddleOCR v3 output.", len(blocks))
    return blocks


def _reconstruct_text(blocks: List[TextBlock]) -> str:
    """
    Reconstruct full document text from sorted TextBlock list.

    Adjacent blocks are joined with spaces; blocks with a large vertical
    gap between them get a newline to preserve label structure.

    Args:
        blocks: Text blocks sorted in reading order.

    Returns:
        Single string representing the full text of the image.
    """
    if not blocks:
        return ""

    lines: List[str] = []
    prev_y: float = blocks[0].bounding_box.top_left[1]

    for block in blocks:
        curr_y = block.bounding_box.top_left[1]
        # New line if vertical gap > 15 pixels
        if curr_y - prev_y > 15:
            lines.append("\n")
        lines.append(block.text)
        prev_y = curr_y

    return " ".join(lines)
