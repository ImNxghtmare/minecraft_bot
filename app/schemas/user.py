from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class PlatformType(str, Enum):
    TELEGRAM = "TELEGRAM"
    VK = "VK"
    WEB = "WEB"


class UserBase(BaseModel):
    platform: PlatformType
    platform_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_banned: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserDB(UserBase):
    id: int
    is_banned: bool
    is_blocked: bool
    last_active: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
