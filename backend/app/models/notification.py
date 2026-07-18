"""
Pydantic models for notification services (WhatsApp + Vapi).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NotificationRequest(BaseModel):
    """Request body for sending a notification."""
    phone_number: str = Field(
        ...,
        description="Phone number in E.164 format (e.g. +919876543210).",
        examples=["+919876543210"],
    )


class NotificationResult(BaseModel):
    """Result of a notification dispatch attempt."""
    inspection_id: str
    channel: str = Field(..., description="whatsapp | vapi")
    phone_number: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    message_id: Optional[str] = Field(None, description="Provider message/call ID if successful.")
    error: Optional[str] = Field(None, description="Error detail if the dispatch failed.")
    status: str = Field(default="notification_sent")
