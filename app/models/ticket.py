from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer, String, Text, Boolean, ForeignKey, DateTime
from enum import Enum as PyEnum
from datetime import datetime

from app.models.base import Base, TimestampMixin
from app.models.user import PlatformType


class TicketStatus(PyEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    CLOSED = "CLOSED"


class TicketPriority(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketCategory(PyEnum):
    TECHNICAL = "TECHNICAL"
    GAMEPLAY = "GAMEPLAY"
    PAYMENT = "PAYMENT"
    COMPLAINT = "COMPLAINT"
    OTHER = "OTHER"


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType), nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), default=TicketStatus.OPEN
    )

    priority: Mapped[TicketPriority | None] = mapped_column(Enum(TicketPriority))
    category: Mapped[TicketCategory | None] = mapped_column(Enum(TicketCategory))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    assigned_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agents.id")
    )

    first_response_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    # relations
    user = relationship("User", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket")
