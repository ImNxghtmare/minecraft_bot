from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.schemas.attachment import AttachmentDB


class MessageDirection(str, Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class MessageStatus(str, Enum):
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    ERROR = "ERROR"


# -----------------------------------------------------
# BASE
# -----------------------------------------------------

class MessageBase(BaseModel):
    ticket_id: Optional[int] = None
    content: Optional[str] = None
    platform_message_id: Optional[str] = None


# -----------------------------------------------------
# CREATE
# -----------------------------------------------------

class MessageCreate(MessageBase):
    user_id: int

    # direction всегда должен быть INCOMING / OUTGOING
    direction: MessageDirection = MessageDirection.INCOMING

    # статус по умолчанию
    status: MessageStatus = MessageStatus.SENT

    # AI флаги
    is_ai_response: bool = False
    confidence_score: Optional[float] = None


# -----------------------------------------------------
# UPDATE
# -----------------------------------------------------

class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    confidence_score: Optional[float] = None


# -----------------------------------------------------
# DB RETURN
# -----------------------------------------------------

class MessageDB(MessageBase):
    id: int
    user_id: int
    direction: MessageDirection
    status: Optional[MessageStatus]

    is_ai_response: bool
    confidence_score: Optional[float]

    created_at: datetime
    updated_at: datetime

    attachments: List[AttachmentDB] = []

    class Config:
        from_attributes = True
