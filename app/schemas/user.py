from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.user import PlatformType

class UserBase(BaseModel):
    platform: PlatformType
    platform_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    is_banned: Optional[bool] = None
    is_blocked: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True