from sqlalchemy import Column, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class PlatformType(enum.Enum):
    TELEGRAM = "telegram"
    VK = "vk"
    WEB = "web"

class User(BaseModel):
    __tablename__ = "users"

    platform = Column(Enum(PlatformType), nullable=False, index=True)
    platform_id = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="ru")
    is_banned = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    last_active = Column(DateTime, nullable=True)

    # Relationships
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.platform}:{self.platform_id}>"