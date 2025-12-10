from sqlalchemy import Column, String, Enum, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    CLOSED = "closed"

class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketCategory(enum.Enum):
    TECHNICAL = "technical"
    GAMEPLAY = "gameplay"
    PAYMENT = "payment"
    COMPLAINT = "complaint"
    OTHER = "other"

class Ticket(BaseModel):
    __tablename__ = "tickets"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, index=True)
    category = Column(Enum(TicketCategory), default=TicketCategory.OTHER)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("agents.id"), nullable=True)
    first_response_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    is_escalated = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="tickets")
    agent = relationship("Agent", back_populates="assigned_tickets")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket #{self.id}: {self.title}>"