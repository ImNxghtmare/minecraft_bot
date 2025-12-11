from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Enum, Integer, DateTime
from datetime import datetime
from enum import Enum as PyEnum

from app.models.base import Base, TimestampMixin


class PlatformType(PyEnum):
    TELEGRAM = "TELEGRAM"
    VK = "VK"
    WEB = "WEB"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    platform: Mapped[PlatformType] = mapped_column(
        Enum(PlatformType), nullable=False
    )

    platform_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    username: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))

    language_code: Mapped[str | None] = mapped_column(String(10))

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    last_active: Mapped[datetime | None] = mapped_column(DateTime)

    # relations
    tickets = relationship("Ticket", back_populates="user")
    messages = relationship("Message", back_populates="user")

