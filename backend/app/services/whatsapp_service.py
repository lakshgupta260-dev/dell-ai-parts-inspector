"""
WhatsApp Cloud API notification service.

Sends an inspection summary message via the WhatsApp Business Cloud API.
Gracefully degrades (logs a warning) if WHATSAPP_TOKEN or WHATSAPP_PHONE_ID
is not configured — the rest of the pipeline is unaffected.

Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/messages
"""

import logging
from datetime import datetime

import requests

from app.core.config import settings
from app.models.ai_analysis import AIAnalysisResult
from app.models.notification import NotificationResult
from app.models.ocr import OCRResult
from app.utils.results_store import STAGE_AI, STAGE_OCR, load_result

logger = logging.getLogger(__name__)

_WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/{phone_id}/messages"


def send_whatsapp_notification(
    inspection_id: str, phone_number: str
) -> NotificationResult:
    """
    Send an inspection summary WhatsApp message to the given phone number.

    Args:
        inspection_id: UUID of the completed inspection.
        phone_number:  Recipient in E.164 format (e.g. +919876543210).

    Returns:
        NotificationResult indicating success or failure.
    """
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
        logger.warning(
            "WhatsApp not configured (missing WHATSAPP_TOKEN or WHATSAPP_PHONE_ID). "
            "Skipping notification for inspection %s.",
            inspection_id,
        )
        return NotificationResult(
            inspection_id=inspection_id,
            channel="whatsapp",
            phone_number=phone_number,
            success=False,
            error="WhatsApp not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_ID in .env.",
        )

    try:
        ai: AIAnalysisResult = load_result(inspection_id, STAGE_AI, AIAnalysisResult)
        ocr: OCRResult = load_result(inspection_id, STAGE_OCR, OCRResult)
    except Exception as exc:
        return NotificationResult(
            inspection_id=inspection_id,
            channel="whatsapp",
            phone_number=phone_number,
            success=False,
            error=f"Could not load inspection data: {exc}",
        )

    service_tag = ocr.combined_dell_fields.service_tag or "Unknown"
    model_name = ocr.combined_dell_fields.model_name or "Unknown"
    verdict_emoji = {"AUTHENTIC": "✅", "SUSPICIOUS": "⚠️", "COUNTERFEIT": "🚨"}.get(
        ai.verdict, "❓"
    )

    message_body = (
        f"🔍 *Dell AI Parts Inspector Report*\n\n"
        f"Inspection ID: `{inspection_id[:8]}...`\n"
        f"Model: {model_name}\n"
        f"Service Tag: {service_tag}\n"
        f"Fraud Score: *{ai.fraud_score}/100*\n"
        f"Verdict: {verdict_emoji} *{ai.verdict}*\n\n"
        f"📋 {ai.final_reasoning}\n\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number.replace(" ", "").replace("-", ""),
        "type": "text",
        "text": {"body": message_body},
    }

    try:
        url = _WHATSAPP_API_URL.format(phone_id=settings.WHATSAPP_PHONE_ID)
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        msg_id = data.get("messages", [{}])[0].get("id")
        logger.info("WhatsApp sent for inspection %s \u2014 msg_id=%s", inspection_id, msg_id)
        return NotificationResult(
            inspection_id=inspection_id,
            channel="whatsapp",
            phone_number=phone_number,
            success=True,
            message_id=msg_id,
        )
    except requests.RequestException as exc:
        logger.exception("WhatsApp API error for inspection %s", inspection_id)
        return NotificationResult(
            inspection_id=inspection_id,
            channel="whatsapp",
            phone_number=phone_number,
            success=False,
            error=str(exc),
        )
