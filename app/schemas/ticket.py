# app/schemas/ticket.py
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.ticket import TicketStatus, TicketPriority, TicketCategory
from app.models.user import PlatformType
from app.schemas.message import MessageDB


class TicketBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.OTHER
    # флаг эскалации (например, если был /operator)
    is_escalated: bool = False


class TicketCreate(TicketBase):
    user_id: int
    platform: PlatformType  # TELEGRAM / VK / WEB


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    assigned_to: Optional[int] = None
    is_escalated: Optional[bool] = None


class TicketDB(TicketBase):
    id: int
    user_id: int
    platform: PlatformType
    status: TicketStatus
    assigned_to: Optional[int] = None
    first_response_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    messages: List[MessageDB] = []

    class Config:
        from_attributes = True
