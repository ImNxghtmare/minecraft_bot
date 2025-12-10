from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.message import AttachmentType

class AttachmentBase(BaseModel):
    message_id: int
    attachment_type: AttachmentType
    file_id: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    caption: Optional[str] = None

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentInDB(AttachmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True