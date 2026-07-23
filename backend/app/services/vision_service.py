"""
Vision Service — Computer Vision analysis using OpenCV.

Pipeline position: Upload → [Vision] → OCR → Comparison → LLM → Score → PDF

Responsibilities:
  1. Load front and back images for a given inspection_id.
  2. Compute image quality metrics (blur, brightness, contrast).
  3. Detect rectangular label / sticker regions via contour analysis.
  4. Analyse colour statistics per channel.
  5. Compute edge density via Canny edge detection.
  6. Aggregate quality flags and produce a structured VisionResult.

This service is pure Python — no HTTP knowledge, no FastAPI imports.
Every function is independently testable.
"""

import logging
from typing import List, Tuple

import cv2
import numpy as np

from app.models.vision import (
    ColorAnalysis,
    ImageQuality,
    LabelRegion,
    SingleImageAnalysis,
    VisionResult,
)
from app.utils.image_utils import get_inspection_image_paths, load_image_bgr

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
_BLUR_THRESHOLD: float = 100.0       # Laplacian variance below this = blurry
_DARK_THRESHOLD: float = 50.0        # Mean brightness below this = too dark
_BRIGHT_THRESHOLD: float = 200.0     # Mean brightness above this = overexposed
_MIN_LABEL_AREA: int = 2_000         # Ignore contours smaller than this (px²)
_MAX_LABEL_AREA_RATIO: float = 0.80  # Ignore contours covering > 80% of image
_CANNY_LOW: int = 50
_CANNY_HIGH: int = 150


# ── Public entry point ────────────────────────────────────────────────────────

def analyze_inspection(inspection_id: str) -> VisionResult:
    """
    Run full computer vision analysis on both images of an inspection.

    Args:
        inspection_id: UUID string identifying the upload session.

    Returns:
        VisionResult containing per-image analysis and aggregate flags.

    Raises:
        HTTPException 404: Propagated from image_utils if files are missing.
    """
    front_rel, back_rel = get_inspection_image_paths(inspection_id)

    logger.info("Vision analysis started for inspection %s", inspection_id)

    front_img = load_image_bgr(front_rel)
    back_img = load_image_bgr(back_rel)

    front_analysis = _analyze_single_image(front_img, front_rel)
    back_analysis = _analyze_single_image(back_img, back_rel)

    # Aggregate quality decision
    overall_ok = (
        not front_analysis.quality.is_blurry
        and not back_analysis.quality.is_blurry
        and len(front_analysis.quality_flags) == 0
        and len(back_analysis.quality_flags) == 0
    )

    all_flags = list(
        {f"[front] {f}" for f in front_analysis.quality_flags}
        | {f"[back] {f}" for f in back_analysis.quality_flags}
    )

    logger.info(
        "Vision analysis complete for %s — overall_ok=%s, flags=%d",
        inspection_id,
        overall_ok,
        len(all_flags),
    )

    return VisionResult(
        inspection_id=inspection_id,
        front=front_analysis,
        back=back_analysis,
        overall_quality_ok=overall_ok,
        vision_flags=sorted(all_flags),
        status="vision_complete",
    )


# ── Per-image analysis ────────────────────────────────────────────────────────

def _analyze_single_image(image: np.ndarray, image_path: str) -> SingleImageAnalysis:
    """
    Run all CV analysis steps on a single image.

    Args:
        image:      BGR NumPy array loaded by load_image_bgr().
        image_path: Relative path string (for record-keeping only).

    Returns:
        SingleImageAnalysis with quality, colour, label regions, and edge density.
    """
    quality = _compute_quality(image)
    color = _compute_color_analysis(image)
    label_regions = _detect_label_regions(image)
    edge_density = _compute_edge_density(image)
    flags = _collect_quality_flags(quality)

    has_label = len(label_regions) > 0
    has_qr_code = _detect_qr_code(image)
    has_burn_marks = _detect_burn_marks(image)

    return SingleImageAnalysis(
        image_path=image_path,
        quality=quality,
        color=color,
        label_regions=label_regions,
        has_label=has_label,
        has_qr_code=has_qr_code,
        has_burn_marks=has_burn_marks,
        edge_density=edge_density,
        quality_flags=flags,
    )


# ── Step 1: Image quality ─────────────────────────────────────────────────────

def _compute_quality(image: np.ndarray) -> ImageQuality:
    """
    Compute blur score, brightness, and contrast for one image.

    Blur detection uses the variance of the Laplacian — a fast, reliable
    single-image focus measure (Pech-Pacheco et al., 2000).
    """
    h, w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur: variance of Laplacian
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = float(laplacian.var())
    is_blurry = blur_score < _BLUR_THRESHOLD

    # Brightness and contrast from gray channel
    mean_brightness = float(gray.mean())
    contrast_score = float(gray.std())

    return ImageQuality(
        width=w,
        height=h,
        channels=channels,
        blur_score=round(blur_score, 2),
        is_blurry=is_blurry,
        mean_brightness=round(mean_brightness, 2),
        contrast_score=round(contrast_score, 2),
    )


# ── Step 2: Colour analysis ───────────────────────────────────────────────────

def _compute_color_analysis(image: np.ndarray) -> ColorAnalysis:
    """
    Compute per-channel statistics and dominant colour via k-means clustering.

    K-means with k=1 gives the global mean (dominant colour cluster centre)
    without the overhead of full palette extraction — sufficient for flag
    comparison against Dell's known label palette.
    """
    b, g, r = cv2.split(image)

    # Per-channel statistics
    mean_b, std_b = float(b.mean()), float(b.std())
    mean_g, std_g = float(g.mean()), float(g.std())
    mean_r, std_r = float(r.mean()), float(r.std())

    # Dominant colour via 1-cluster k-means on a pixel sample
    pixels = image.reshape(-1, 3).astype(np.float32)
    # Sample at most 5000 pixels for speed
    if len(pixels) > 5_000:
        idx = np.random.choice(len(pixels), 5_000, replace=False)
        pixels = pixels[idx]

    _, _, centers = cv2.kmeans(
        pixels,
        K=1,
        bestLabels=None,
        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        attempts=3,
        flags=cv2.KMEANS_RANDOM_CENTERS,
    )
    dominant_bgr = centers[0].astype(int).tolist()
    dominant_rgb = [dominant_bgr[2], dominant_bgr[1], dominant_bgr[0]]

    return ColorAnalysis(
        mean_blue=round(mean_b, 2),
        mean_green=round(mean_g, 2),
        mean_red=round(mean_r, 2),
        std_blue=round(std_b, 2),
        std_green=round(std_g, 2),
        std_red=round(std_r, 2),
        dominant_color_rgb=dominant_rgb,
    )


# ── Step 3: Label region detection ───────────────────────────────────────────

def _detect_label_regions(image: np.ndarray) -> List[LabelRegion]:
    """
    Detect rectangular label / sticker regions using adaptive thresholding
    and contour analysis.

    Strategy:
      1. Convert to grayscale and apply adaptive threshold (robust to shadows).
      2. Find external contours.
      3. Approximate each contour to a polygon.
      4. Keep quadrilaterals whose area is within the plausible label range.
      5. Score each by rectangularity (bounding-box fill ratio).

    Returns:
        List of LabelRegion, sorted by area descending (largest label first).
    """
    img_area = image.shape[0] * image.shape[1]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Adaptive threshold handles uneven lighting on parts
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,
        C=2,
    )

    # Morphological closing to join broken label borders
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions: List[LabelRegion] = []
    for cnt in contours:
        area = int(cv2.contourArea(cnt))
        if area < _MIN_LABEL_AREA:
            continue
        if area > img_area * _MAX_LABEL_AREA_RATIO:
            continue

        # Approximate to polygon
        epsilon = 0.04 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # Only keep shapes close to a rectangle (3–6 vertices)
        if not (3 <= len(approx) <= 6):
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        bounding_area = w * h
        rectangularity = area / bounding_area if bounding_area > 0 else 0.0

        regions.append(
            LabelRegion(
                x=x, y=y,
                width=w, height=h,
                area=area,
                confidence=round(rectangularity, 3),
            )
        )

    regions.sort(key=lambda r: r.area, reverse=True)
    logger.debug("Detected %d label region(s).", len(regions))
    return regions[:10]  # Return top-10 at most


# ── Step 4: Edge density ──────────────────────────────────────────────────────

def _compute_edge_density(image: np.ndarray) -> float:
    """
    Compute the fraction of pixels classified as edges by Canny.

    A high edge density (> 0.05) is typical of authentic Dell labels which
    contain dense text and logo graphics.  Very low density can indicate
    a blank or heavily altered surface.

    Returns:
        Edge density as a float in [0.0, 1.0], rounded to 4 decimal places.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, _CANNY_LOW, _CANNY_HIGH)
    density = float(np.count_nonzero(edges)) / edges.size
    return round(density, 4)


# ── Dataset Specific Heuristics ──────────────────────────────────────────────

def _detect_qr_code(image: np.ndarray) -> bool:
    """Detect if a QR code or DataMatrix code is present."""
    detector = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(image)
    return bool(retval)

def _detect_burn_marks(image: np.ndarray) -> bool:
    """
    Heuristic to detect burn marks.
    Looks for localized dark, brownish/black regions on the green motherboard.
    """
    # Convert to HSV to isolate dark regions independent of lighting
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    
    # Threshold for very dark regions (burn marks are usually very dark)
    _, dark_mask = cv2.threshold(v_channel, 30, 255, cv2.THRESH_BINARY_INV)
    
    # Clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Increase threshold significantly to prevent false positives from shadows/chips
        if area > 4500:  
            # Check rectangularity. Chips are rectangular, burns are irregular.
            x, y, w, h = cv2.boundingRect(cnt)
            bounding_area = w * h
            if bounding_area > 0 and (area / bounding_area) < 0.8:
                return True
            
    return False


# ── Step 5: Quality flag collection ──────────────────────────────────────────

def _collect_quality_flags(quality: ImageQuality) -> List[str]:
    """
    Translate numeric quality metrics into human-readable warning strings.

    Args:
        quality: ImageQuality model for one image.

    Returns:
        List of warning strings; empty list means image quality is acceptable.
    """
    flags: List[str] = []

    if quality.is_blurry:
        flags.append(
            f"Image is blurry (blur_score={quality.blur_score:.1f} < {_BLUR_THRESHOLD}). "
            "Retake with better focus for accurate OCR."
        )
    if quality.mean_brightness < _DARK_THRESHOLD:
        flags.append(
            f"Image is too dark (brightness={quality.mean_brightness:.1f}). "
            "Improve lighting before proceeding."
        )
    if quality.mean_brightness > _BRIGHT_THRESHOLD:
        flags.append(
            f"Image is overexposed (brightness={quality.mean_brightness:.1f}). "
            "Reduce direct lighting or glare."
        )

    return flags
