"""
Notifications API router — WhatsApp and Vapi.

Endpoints:
  POST /api/v1/notify/whatsapp/{inspection_id}
  POST /api/v1/notify/vapi/{inspection_id}
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Path, status

from app.models.notification import NotificationRequest, NotificationResult
from app.services.vapi_service import send_vapi_call
from app.services.whatsapp_service import send_whatsapp_notification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notify", tags=["Notifications"])


@router.post(
    "/whatsapp/{inspection_id}",
    response_model=NotificationResult,
    summary="Send WhatsApp inspection summary",
    description=(
        "Sends a formatted WhatsApp message with the inspection verdict, fraud score, "
        "and final reasoning to the specified phone number. "
        "Requires WHATSAPP_TOKEN and WHATSAPP_PHONE_ID in .env. "
        "Run the AI analysis endpoint first. "
        "If credentials are not configured, returns success=false with an informative error."
    ),
)
async def whatsapp_notify(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint."),
    body: NotificationRequest = ...,
) -> NotificationResult:
    """Send WhatsApp notification for an inspection."""
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")
    logger.info("WhatsApp notify requested for %s \u2192 %s", inspection_id, body.phone_number)
    return send_whatsapp_notification(inspection_id, body.phone_number)


@router.post(
    "/vapi/{inspection_id}",
    response_model=NotificationResult,
    summary="Initiate Vapi voice call with inspection result",
    description=(
        "Initiates an outbound AI voice call via Vapi that reads the inspection summary "
        "to the specified phone number. The AI assistant can answer follow-up questions. "
        "Requires VAPI_API_KEY and VAPI_PHONE_NUMBER_ID in .env. "
        "Run the AI analysis endpoint first."
    ),
)
async def vapi_notify(
    inspection_id: str = Path(..., description="UUID from the Upload endpoint."),
    body: NotificationRequest = ...,
) -> NotificationResult:
    """Initiate a Vapi voice call for an inspection."""
    try:
        uuid.UUID(inspection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID.")
    logger.info("Vapi call requested for %s \u2192 %s", inspection_id, body.phone_number)
    return send_vapi_call(inspection_id, body.phone_number)
