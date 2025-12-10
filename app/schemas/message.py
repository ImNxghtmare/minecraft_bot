from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.message import MessageDirection, MessageStatus
from .attachment import AttachmentInDB

class MessageBase(BaseModel):
    ticket_id: Optional[int] = None
    user_id: int
    direction: MessageDirection
    content: Optional[str] = None
    is_ai_response: bool = False
    confidence_score: Optional[float] = None

class MessageCreate(MessageBase):
    platform_message_id: Optional[str] = None

class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None

class MessageInDB(MessageBase):
    id: int
    status: MessageStatus
    platform_message_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentInDB] = []

    class Config:
        from_attributes = True