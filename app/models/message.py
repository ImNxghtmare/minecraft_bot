from sqlalchemy import Column, String, Enum, Integer, ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class MessageDirection(enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class MessageStatus(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ERROR = "error"

class AttachmentType(enum.Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    STICKER = "STICKER"
    VOICE = "VOICE"
    LOCATION = "LOCATION"
    CONTACT = "CONTACT"

class Message(BaseModel):
    __tablename__ = "messages"

    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    direction = Column(Enum(MessageDirection), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    content = Column(Text, nullable=True)
    is_ai_response = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)
    platform_message_id = Column(String(100), nullable=True)

    user = relationship("User", back_populates="messages")
    ticket = relationship("Ticket", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message {self.direction}: {self.content[:50] if self.content else 'No content'}>"

class Attachment(BaseModel):
    __tablename__ = "attachments"

    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    attachment_type = Column(Enum(AttachmentType), nullable=False)
    file_id = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    caption = Column(Text, nullable=True)

    message = relationship("Message", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment {self.attachment_type}: {self.file_id}>"
