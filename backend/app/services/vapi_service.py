"""
Vapi Voice Call notification service.

Initiates a Vapi outbound call that reads a spoken inspection summary.
Gracefully degrades if VAPI_API_KEY or VAPI_PHONE_NUMBER_ID is not set.

Reference: https://docs.vapi.ai/api-reference/calls/create
"""

import logging

import requests

from app.core.config import settings
from app.models.ai_analysis import AIAnalysisResult
from app.models.notification import NotificationResult
from app.models.ocr import OCRResult
from app.utils.results_store import STAGE_AI, STAGE_OCR, load_result

logger = logging.getLogger(__name__)

_VAPI_CALLS_URL = "https://api.vapi.ai/call"


def send_vapi_call(inspection_id: str, phone_number: str) -> NotificationResult:
    """
    Initiate a Vapi outbound voice call with the inspection result summary.

    Args:
        inspection_id: UUID of the completed inspection.
        phone_number:  Recipient in E.164 format.

    Returns:
        NotificationResult indicating success or failure.
    """
    if not settings.VAPI_API_KEY or not settings.VAPI_PHONE_NUMBER_ID:
        logger.warning(
            "Vapi not configured (missing VAPI_API_KEY or VAPI_PHONE_NUMBER_ID). "
            "Skipping call for inspection %s.",
            inspection_id,
        )
        return NotificationResult(
            inspection_id=inspection_id,
            channel="vapi",
            phone_number=phone_number,
            success=False,
            error="Vapi not configured. Set VAPI_API_KEY and VAPI_PHONE_NUMBER_ID in .env.",
        )

    try:
        ai: AIAnalysisResult = load_result(inspection_id, STAGE_AI, AIAnalysisResult)
        ocr: OCRResult = load_result(inspection_id, STAGE_OCR, OCRResult)
    except Exception as exc:
        return NotificationResult(
            inspection_id=inspection_id,
            channel="vapi",
            phone_number=phone_number,
            success=False,
            error=f"Could not load inspection data: {exc}",
        )

    service_tag = ocr.combined_dell_fields.service_tag or "unknown"
    model_name = ocr.combined_dell_fields.model_name or "unknown"

    spoken_script = (
        f"Hello. This is the Dell AI Parts Inspector automated alert system. "
        f"Inspection {inspection_id[:8]} for model {model_name}, "
        f"service tag {' '.join(list(service_tag))} has been completed. "
        f"The fraud score is {ai.fraud_score} out of 100. "
        f"The verdict is {ai.verdict}. "
        f"{ai.final_reasoning} "
        f"Please log in to the dashboard to view the full report. Thank you."
    )

    payload = {
        "type": "outboundPhoneCall",
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {"number": phone_number},
        "assistant": {
            "firstMessage": spoken_script,
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a Dell hardware inspection assistant. "
                            "Read the inspection summary to the caller clearly and professionally. "
                            "Answer any follow-up questions they have about the inspection."
                        ),
                    }
                ],
            },
            "voice": {"provider": "11labs", "voiceId": "burt"},
        },
    }

    try:
        response = requests.post(
            _VAPI_CALLS_URL,
            headers={
                "Authorization": f"Bearer {settings.VAPI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        call_id = response.json().get("id")
        logger.info("Vapi call initiated for inspection %s \u2014 call_id=%s", inspection_id, call_id)
        return NotificationResult(
            inspection_id=inspection_id,
            channel="vapi",
            phone_number=phone_number,
            success=True,
            message_id=call_id,
        )
    except requests.RequestException as exc:
        logger.exception("Vapi API error for inspection %s", inspection_id)
        return NotificationResult(
            inspection_id=inspection_id,
            channel="vapi",
            phone_number=phone_number,
            success=False,
            error=str(exc),
        )
