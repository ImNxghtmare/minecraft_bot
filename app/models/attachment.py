from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer, String, Text, ForeignKey
from enum import Enum as PyEnum

from app.models.base import Base, TimestampMixin


class AttachmentType(PyEnum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    STICKER = "STICKER"
    VOICE = "VOICE"
    LOCATION = "LOCATION"
    CONTACT = "CONTACT"


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )

    attachment_type: Mapped[AttachmentType] = mapped_column(Enum(AttachmentType))

    file_id: Mapped[str] = mapped_column(String(500))
    file_url: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    caption: Mapped[str | None] = mapped_column(Text)

    # relation
    message = relationship("Message", back_populates="attachments")
