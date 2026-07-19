"""
Comparison Service — validates OCR-extracted Dell fields against authenticity rules.

Pipeline: Upload → Vision → OCR → [Comparison] → AI → Score → PDF

Rules applied:
  • Service Tag: must be exactly 7 alphanumeric chars
  • Express Service Code: must be 11 digits
  • Part Number: CN-XXXXXX or 0XXXXXX format
  • Model: must match a known Dell product family
  • Presence checks: critical fields must exist
  • OCR confidence: avg must be ≥ 0.80 for reliable results
"""

import logging
import re
from typing import List

import json
from pathlib import Path

from app.core.config import settings
from app.models.comparison import ComparisonResult, FieldCheck
from app.models.ocr import OCRResult
from app.models.vision import VisionResult
from app.utils.results_store import STAGE_OCR, STAGE_VISION, load_result, save_result, STAGE_COMPARISON

logger = logging.getLogger(__name__)

_KNOWN_DELL_MODELS = [
    "optiplex", "latitude", "precision", "inspiron", "vostro",
    "xps", "alienware", "poweredge", "powervault", "dimension",
]
_RE_SERVICE_TAG = re.compile(r'^[A-Z0-9]{7}$')
_RE_ESC = re.compile(r'^\d{11}$')
_RE_PART_CN = re.compile(r'^CN-[A-Z0-9]{6}-[A-Z0-9]{5}-[A-Z0-9]{3}-[A-Z0-9]{4}$', re.IGNORECASE)
_RE_PART_SHORT = re.compile(r'^[0-9A-Z]{7,12}$', re.IGNORECASE)


def run_comparison(inspection_id: str) -> ComparisonResult:
    """
    Load OCR results and run all field validation checks.
    Saves and returns a ComparisonResult.
    """
    ocr: OCRResult = load_result(inspection_id, STAGE_OCR, OCRResult)
    vision: VisionResult = load_result(inspection_id, STAGE_VISION, VisionResult)
    fields = ocr.combined_dell_fields
    checks: List[FieldCheck] = []

    # Identify model to load corresponding golden profile
    model_name_extracted = fields.model_name.lower() if fields.model_name else ""
    matched_model = "xps"  # Default fallback
    for m in _KNOWN_DELL_MODELS:
        if m in model_name_extracted:
            matched_model = m
            break
            
    # Load Golden Profile
    golden_profile = {}
    profile_path = Path("datasets/golden/profiles") / f"{matched_model}.json"
    if profile_path.exists():
        try:
            golden_profile = json.loads(profile_path.read_text())
            logger.info("Loaded golden profile for %s", matched_model)
        except Exception as e:
            logger.warning("Failed to load golden profile: %s", e)

    # OCR Checks
    checks.append(_check_service_tag(fields.service_tag))
    checks.append(_check_esc(fields.express_service_code))
    checks.append(_check_part_number(fields.part_number))
    checks.append(_check_model(fields.model_name))
    
    avg_conf = (ocr.front.avg_confidence + ocr.back.avg_confidence) / 2
    checks.append(_check_ocr_confidence(avg_conf))

    total_risk = min(100, sum(c.risk_contribution for c in checks))
    missing = [c.field_name for c in checks if not c.is_present]
    violations = [c.field_name for c in checks if c.is_present and not c.is_valid_format]

    # Calculate Vision/Anomaly Golden Metrics
    similarity_metrics = {}
    if golden_profile:
        expected_vision = golden_profile.get("vision_features", {})
        
        # We aggregate flags from both front and back
        has_qr = vision.front.has_qr_code or vision.back.has_qr_code
        has_label = vision.front.has_label or vision.back.has_label
        has_burns = vision.front.has_burn_marks or vision.back.has_burn_marks
        
        vision_match = 100
        if expected_vision.get("has_qr_code") and not has_qr:
            vision_match -= 40
            total_risk = min(100, total_risk + 30)
            missing.append("QR/DataMatrix Code (Golden Mismatch)")
            
        if expected_vision.get("has_label") and not has_label:
            vision_match -= 50
            total_risk = min(100, total_risk + 40)
            missing.append("Physical Label (Golden Mismatch)")
            
        anomaly_score = 0
        if has_burns and not expected_vision.get("has_burn_marks"):
            anomaly_score = 100
            total_risk = min(100, total_risk + 50)
            violations.append("Burn Marks Detected (Anomaly)")
            
        similarity_metrics = {
            "ocr_similarity": max(0, 100 - (len(missing) * 15) - (len(violations) * 10)),
            "vision_match": max(0, vision_match),
            "anomaly_score": anomaly_score
        }

    summary = _build_summary(total_risk, missing, violations)
    logger.info("Comparison complete for %s — risk=%d, missing=%s", inspection_id, total_risk, missing)

    result = ComparisonResult(
        inspection_id=inspection_id,
        field_checks=checks,
        total_risk_score=total_risk,
        missing_critical_fields=missing,
        format_violations=violations,
        comparison_summary=summary,
        golden_reference_used=matched_model if golden_profile else None,
        similarity_metrics=similarity_metrics,
    )
    save_result(inspection_id, STAGE_COMPARISON, result)
    return result


def _check_service_tag(value) -> FieldCheck:
    present = bool(value)
    valid = bool(value and _RE_SERVICE_TAG.match(value))
    flags = []
    risk = 0
    if not present:
        flags.append("Service Tag not found — critical missing field.")
        risk = 35
    elif not valid:
        flags.append(f"Service Tag '{value}' does not match 7-char alphanumeric format.")
        risk = 25
    return FieldCheck(
        field_name="Service Tag",
        extracted_value=value,
        is_present=present,
        is_valid_format=valid,
        expected_format="Exactly 7 uppercase alphanumeric characters (e.g. ABC1234)",
        flags=flags,
        risk_contribution=risk,
    )


def _check_esc(value) -> FieldCheck:
    present = bool(value)
    valid = bool(value and _RE_ESC.match(value))
    flags = []
    risk = 0
    if not present:
        flags.append("Express Service Code not found.")
        risk = 15
    elif not valid:
        flags.append(f"ESC '{value}' does not match 11-digit format.")
        risk = 10
    return FieldCheck(
        field_name="Express Service Code",
        extracted_value=value,
        is_present=present,
        is_valid_format=valid,
        expected_format="Exactly 11 consecutive digits",
        flags=flags,
        risk_contribution=risk,
    )


def _check_part_number(value) -> FieldCheck:
    present = bool(value)
    valid = bool(value and (_RE_PART_CN.match(value) or _RE_PART_SHORT.match(value)))
    flags = []
    risk = 0
    if not present:
        flags.append("Part Number not found.")
        risk = 20
    elif not valid:
        flags.append(f"Part Number '{value}' does not match CN-XXXXXX or 0XXXXXX format.")
        risk = 15
    return FieldCheck(
        field_name="Part Number",
        extracted_value=value,
        is_present=present,
        is_valid_format=valid,
        expected_format="CN-XXXXXX-XXXXX-XXX-XXXX or 7-12 char alphanumeric",
        flags=flags,
        risk_contribution=risk,
    )


def _check_model(value) -> FieldCheck:
    present = bool(value)
    valid = bool(value and any(m in value.lower() for m in _KNOWN_DELL_MODELS))
    flags = []
    risk = 0
    if not present:
        flags.append("Dell model name not found on label.")
        risk = 10
    elif not valid:
        flags.append(f"Model '{value}' not in known Dell product families.")
        risk = 8
    return FieldCheck(
        field_name="Model Name",
        extracted_value=value,
        is_present=present,
        is_valid_format=valid,
        expected_format="Known Dell family: OptiPlex, Latitude, Precision, XPS, etc.",
        flags=flags,
        risk_contribution=risk,
    )


def _check_ocr_confidence(avg_conf: float) -> FieldCheck:
    valid = avg_conf >= 0.80
    flags = [] if valid else [f"Low OCR confidence ({avg_conf:.2%}) — image quality may be poor."]
    return FieldCheck(
        field_name="OCR Confidence",
        extracted_value=f"{avg_conf:.4f}",
        is_present=True,
        is_valid_format=valid,
        expected_format="≥ 80% average confidence across all text blocks",
        flags=flags,
        risk_contribution=0 if valid else 12,
    )


def _build_summary(risk: int, missing: List[str], violations: List[str]) -> str:
    if risk == 0:
        return "All Dell label fields are present and correctly formatted. Low fraud risk."
    parts = []
    if missing:
        parts.append(f"Missing critical fields: {', '.join(missing)}.")
    if violations:
        parts.append(f"Format violations: {', '.join(violations)}.")
    parts.append(f"Aggregated field risk score: {risk}/100.")
    return " ".join(parts)
