"""
Webhook API router — Receives callbacks from external services (Meta WhatsApp, Vapi, etc.).
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from app.core.config import settings
from app.services.vapi_service import send_vapi_call

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhook", tags=["Webhooks"])

@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """
    Verify the webhook URL for Meta WhatsApp Cloud API.
    Meta will send a GET request with hub.challenge when you add the Webhook URL.
    """
    verify_token = settings.WHATSAPP_VERIFY_TOKEN
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logger.info("WhatsApp Webhook successfully verified by Meta.")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch.")
    
    raise HTTPException(status_code=400, detail="Missing mode or token.")

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Receive messages and interactive button clicks from WhatsApp.
    This enables the "One-Click" features like calling the AI Assistant.
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    # We must always return 200 OK immediately so Meta doesn't retry
    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                if messages:
                    msg = messages[0]
                    # Check if the user clicked an interactive button
                    if msg.get("type") == "interactive":
                        interactive = msg.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            button_id = interactive.get("button_reply", {}).get("id", "")
                            sender_phone = msg.get("from")
                            
                            logger.info(f"Received interactive button click: {button_id} from {sender_phone}")
                            
                            # Parse our custom button IDs (e.g. call_UUID)
                            if button_id.startswith("call_"):
                                inspection_id = button_id.replace("call_", "")
                                logger.info(f"Triggering Vapi AI Call for {inspection_id} to {sender_phone} via Webhook!")
                                
                                # Format phone number with leading + if missing (Vapi requires E.164)
                                formatted_phone = f"+{sender_phone}" if not sender_phone.startswith("+") else sender_phone
                                
                                # Trigger Vapi in the background
                                background_tasks.add_task(send_vapi_call, inspection_id, formatted_phone)
                                
                            elif button_id.startswith("view_"):
                                inspection_id = button_id.replace("view_", "")
                                logger.info(f"QA Manager requested to view report for inspection: {inspection_id}")
                                from app.services.whatsapp_service import send_whatsapp_text
                                base_url = str(request.base_url).rstrip("/")
                                pdf_url = f"{base_url}/api/v1/report/download/{inspection_id}"
                                msg = f"📄 View the full detailed PDF report here:\n{pdf_url}"
                                background_tasks.add_task(send_whatsapp_text, sender_phone, msg)
                                
                            elif button_id.startswith("esc_"):
                                inspection_id = button_id.replace("esc_", "")
                                logger.info(f"Escalation requested for inspection: {inspection_id}")
                                
                                # Update DB
                                from app.core.database import SessionLocal
                                from app.models.database import InspectionRecord
                                db = SessionLocal()
                                try:
                                    record = db.query(InspectionRecord).filter_by(inspection_id=inspection_id).first()
                                    if record:
                                        record.is_escalated = 1
                                        db.commit()
                                finally:
                                    db.close()

                                from app.services.whatsapp_service import send_whatsapp_text
                                
                                # Send confirmation to the person who escalated (Inspector)
                                msg = f"🚨 Inspection {inspection_id[:8]} has been ESCALATED.\n\nA senior QA Manager has been notified and the part has been flagged in the database."
                                background_tasks.add_task(send_whatsapp_text, sender_phone, msg)
                                
                                # Notify QA Manager
                                qa_phone = getattr(settings, 'QA_MANAGER_PHONE', sender_phone)
                                qa_msg = f"🔔 *ESCALATION ALERT*\n\nInspection {inspection_id[:8]} has been escalated for manual QA review. Please check your QA Dashboard."
                                background_tasks.add_task(send_whatsapp_text, qa_phone, qa_msg)

    return {"status": "ok"}
