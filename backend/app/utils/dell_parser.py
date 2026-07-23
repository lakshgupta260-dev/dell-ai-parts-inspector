"""
Dell label field parser — regex-based extraction of structured fields.

This module contains ONLY pure string-processing functions.  It has zero
dependency on OpenCV, PaddleOCR, FastAPI, or any I/O.  Every function is
independently unit-testable with a plain string input.

Reference patterns are derived from official Dell label documentation and
community-verified Service Tag / Part Number formats.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Compiled regex patterns ────────────────────────────────────────────────────

# Service Tag: exactly 7 alphanumeric characters (uppercase)
# Preceded by "Service Tag", "S/N", "SVC TAG", or at line start
_RE_SERVICE_TAG = re.compile(
    r"(?:service\s*tag|svc\s*tag|s/?n)[:\s#]*([A-Z0-9]{7})\b",
    re.IGNORECASE,
)
# Also catch bare 7-char tokens that look like a Service Tag (require both letters and digits)
_RE_SERVICE_TAG_BARE = re.compile(r"\b((?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{7})\b")

# Express Service Code: exactly 11 consecutive digits
_RE_ESC = re.compile(
    r"(?:express\s*service\s*code|esc)[:\s]*(\d{11})\b",
    re.IGNORECASE,
)
_RE_ESC_BARE = re.compile(r"\b(\d{11})\b")

# Part Number: Dell uses two dominant formats
#   CN-XXXXXX-XXXXX-XXX-XXXX  (notebook/server parts)
#   0XXXXXX                    (desktop parts, 7 chars starting with 0)
_RE_PART_CN = re.compile(
    r"\b(CN[-–]?[A-Z0-9]{6}[-–][A-Z0-9]{5}[-–][A-Z0-9]{3}[-–][A-Z0-9]{4})\b",
    re.IGNORECASE,
)
_RE_PART_SHORT = re.compile(
    r"(?:part\s*(?:no|num|number)?|p/?n)[:\s]*([0-9A-Z]{7,12})\b",
    re.IGNORECASE,
)

# Dell product model families
_DELL_MODELS = [
    "OptiPlex", "Latitude", "Precision", "Inspiron", "Vostro",
    "XPS", "Alienware", "G Series", "PowerEdge", "PowerVault",
    "Dimension", "Studio",
]
_RE_MODEL = re.compile(
    r"\b(" + "|".join(re.escape(m) for m in _DELL_MODELS) + r")\s*([\w\-]{0,15})",
    re.IGNORECASE,
)

# Regulatory identifiers
_RE_FCC = re.compile(r"\bFCC(?:\s*ID)?[:\s]*([A-Z0-9\-]{4,20})\b", re.IGNORECASE)
_RE_CE = re.compile(r"\bCE\b")
_RE_UL = re.compile(r"\bUL\s*\d{3,6}\b", re.IGNORECASE)

# Manufacture date: MM/YYYY, MM-YYYY, YYYY-MM
_RE_DATE = re.compile(
    r"\b(?:mfg|manufactured|date)[:\s]*"
    r"(\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2})\b",
    re.IGNORECASE,
)

# Country of origin
_RE_COUNTRY = re.compile(
    r"\b(?:made\s+in|country\s+of\s+origin|assembled\s+in)[:\s]+"
    r"([A-Za-z ]{3,30})",
    re.IGNORECASE,
)

# Generic key-value pairs:  "Key: Value" or "Key  Value" (common on labels)
_RE_KV = re.compile(
    r"([A-Za-z][A-Za-z0-9 /]{1,25})[:\s]{1,3}([A-Za-z0-9][A-Za-z0-9 .\-/]{1,40})",
)


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_dell_fields(text: str) -> "DellFields":  # noqa: F821 — forward ref
    """
    Parse structured Dell fields from a blob of OCR text.

    Args:
        text: Full concatenated OCR text from one or both images.

    Returns:
        DellFields instance with all extracted values (None where not found).
    """
    from app.models.ocr import DellFields  # local import avoids circular deps

    service_tag = _extract_service_tag(text)
    esc = _extract_express_service_code(text)
    part_number = _extract_part_number(text)
    model_name = _extract_model(text)
    regulatory = _extract_regulatory(text)
    mfg_date = _extract_manufacture_date(text)
    country = _extract_country(text)
    raw_fields = _extract_raw_kv(text)

    logger.debug(
        "Parsed fields — tag=%s, esc=%s, part=%s, model=%s",
        service_tag, esc, part_number, model_name,
    )

    return DellFields(
        service_tag=service_tag,
        express_service_code=esc,
        part_number=part_number,
        model_name=model_name,
        regulatory_info=regulatory,
        manufacture_date=mfg_date,
        country_of_origin=country,
        raw_fields=raw_fields,
    )


def merge_dell_fields(primary: "DellFields", secondary: "DellFields") -> "DellFields":  # noqa: F821
    """
    Merge two DellFields objects. Primary values take precedence;
    secondary values fill any None slots.

    Args:
        primary:   Fields from the front image (higher priority).
        secondary: Fields from the back image (fills gaps).

    Returns:
        A new DellFields with the best available values from both images.
    """
    from app.models.ocr import DellFields

    merged_regulatory = list(
        dict.fromkeys(primary.regulatory_info + secondary.regulatory_info)
    )
    merged_raw = {**secondary.raw_fields, **primary.raw_fields}  # primary wins

    return DellFields(
        service_tag=primary.service_tag or secondary.service_tag,
        express_service_code=primary.express_service_code or secondary.express_service_code,
        part_number=primary.part_number or secondary.part_number,
        model_name=primary.model_name or secondary.model_name,
        regulatory_info=merged_regulatory,
        manufacture_date=primary.manufacture_date or secondary.manufacture_date,
        country_of_origin=primary.country_of_origin or secondary.country_of_origin,
        raw_fields=merged_raw,
    )


# ── Private extractors ─────────────────────────────────────────────────────────

def _extract_service_tag(text: str) -> Optional[str]:
    m = _RE_SERVICE_TAG.search(text)
    if m:
        return m.group(1).upper()
    # Fallback: bare 7-char token — less reliable, log at debug
    m = _RE_SERVICE_TAG_BARE.search(text)
    if m:
        logger.debug("Service Tag from bare pattern: %s", m.group(1))
        return m.group(1).upper()
    return None


def _extract_express_service_code(text: str) -> Optional[str]:
    m = _RE_ESC.search(text)
    if m:
        return m.group(1)
    m = _RE_ESC_BARE.search(text)
    return m.group(1) if m else None


def _extract_part_number(text: str) -> Optional[str]:
    m = _RE_PART_CN.search(text)
    if m:
        return m.group(1).upper()
    m = _RE_PART_SHORT.search(text)
    return m.group(1).upper() if m else None


def _extract_model(text: str) -> Optional[str]:
    m = _RE_MODEL.search(text)
    if m:
        family = m.group(1).strip()
        suffix = m.group(2).strip().split()[0] if m.group(2).strip() else ""
        return (family + (" " + suffix if suffix else "")).strip()
    return None


def _extract_regulatory(text: str) -> List[str]:
    results: List[str] = []
    for m in _RE_FCC.finditer(text):
        results.append(f"FCC ID: {m.group(1)}")
    if _RE_CE.search(text):
        results.append("CE")
    for m in _RE_UL.finditer(text):
        results.append(m.group(0))
    return list(dict.fromkeys(results))  # deduplicate, preserve order


def _extract_manufacture_date(text: str) -> Optional[str]:
    m = _RE_DATE.search(text)
    return m.group(1) if m else None


def _extract_country(text: str) -> Optional[str]:
    m = _RE_COUNTRY.search(text)
    return m.group(1).strip().title() if m else None


def _extract_raw_kv(text: str) -> Dict[str, str]:
    """Extract all label-style key-value pairs as a raw dictionary."""
    pairs: Dict[str, str] = {}
    for m in _RE_KV.finditer(text):
        key = m.group(1).strip().title()
        value = m.group(2).strip()
        if len(key) >= 2 and len(value) >= 1:
            pairs[key] = value
    return pairs
