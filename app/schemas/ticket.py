from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.schemas.message import MessageDB


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketCategory(str, Enum):
    TECHNICAL = "TECHNICAL"
    GAMEPLAY = "GAMEPLAY"
    PAYMENT = "PAYMENT"
    COMPLAINT = "COMPLAINT"
    OTHER = "OTHER"


class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None


class TicketCreate(TicketBase):
    user_id: int
    platform: str  # TELEGRAM / VK / WEB
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    assigned_to: Optional[int] = None
    is_escalated: Optional[bool] = None


class TicketDB(TicketBase):
    id: int
    user_id: int
    platform: str
    status: TicketStatus
    priority: Optional[TicketPriority]
    category: Optional[TicketCategory]
    assigned_to: Optional[int]
    first_response_at: Optional[datetime]
    closed_at: Optional[datetime]
    is_escalated: bool

    created_at: datetime
    updated_at: datetime

    messages: List[MessageDB] = []

    class Config:
        from_attributes = True
