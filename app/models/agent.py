from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, Integer, Boolean, DateTime
from enum import Enum as PyEnum
from datetime import datetime

from app.models.base import Base, TimestampMixin


class AgentRole(PyEnum):
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"
    MODERATOR = "MODERATOR"


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    role: Mapped[AgentRole] = mapped_column(Enum(AgentRole))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    last_login: Mapped[datetime | None] = mapped_column(DateTime)
    telegram_id: Mapped[str | None] = mapped_column(String(100))

    tickets = relationship("Ticket", backref="agent")
