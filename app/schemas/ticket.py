from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.ticket import TicketStatus, TicketPriority, TicketCategory
from app.models.user import PlatformType

class TicketBase(BaseModel):
    user_id: int
    platform: PlatformType
    title: str
    description: Optional[str] = None
    category: TicketCategory = TicketCategory.OTHER

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    assigned_to: Optional[int] = None
    is_escalated: Optional[bool] = None

class TicketInDB(TicketBase):
    id: int
    status: TicketStatus
    priority: TicketPriority
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    first_response_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    is_escalated: bool = False

    class Config:
        from_attributes = True