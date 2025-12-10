from sqlalchemy import Column, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AgentRole(enum.Enum):
    ADMIN = "admin"
    SUPPORT = "support"
    MODERATOR = "moderator"

class Agent(BaseModel):
    __tablename__ = "agents"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(Enum(AgentRole), default=AgentRole.SUPPORT)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    telegram_id = Column(String(100), nullable=True)

    # Relationships
    assigned_tickets = relationship("Ticket", back_populates="agent")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def __repr__(self):
        return f"<Agent {self.email}: {self.role}>"