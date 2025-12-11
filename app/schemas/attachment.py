from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class AttachmentType(str, Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    STICKER = "STICKER"
    VOICE = "VOICE"
    LOCATION = "LOCATION"
    CONTACT = "CONTACT"


class AttachmentCreate(BaseModel):
    message_id: int
    attachment_type: AttachmentType
    file_id: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    caption: Optional[str] = None


class AttachmentDB(AttachmentCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
