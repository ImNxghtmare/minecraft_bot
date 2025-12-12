from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer, Text, String, Float, ForeignKey, Boolean
from enum import Enum as PyEnum

from app.models.base import Base, TimestampMixin


class MessageDirection(PyEnum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class MessageStatus(PyEnum):
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    ERROR = "ERROR"


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE")
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE")
    )

    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection),
        nullable=False
    )

    status: Mapped[MessageStatus | None] = mapped_column(
        Enum(MessageStatus),
        nullable=True
    )

    content: Mapped[str | None] = mapped_column(Text)

    is_ai_response: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)

    platform_message_id: Mapped[str | None] = mapped_column(String(100))

    # relations
    ticket = relationship("Ticket", back_populates="messages")
    user = relationship("User", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message")
