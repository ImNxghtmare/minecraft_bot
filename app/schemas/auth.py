from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.agent import AgentRole


# --------------------------
# TOKEN SCHEMAS
# --------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # опционально можно отдавать время жизни
    expires_in: Optional[int] = None


class TokenPayload(BaseModel):
    sub: Optional[int] = None


# --------------------------
# LOGIN
# --------------------------

class AgentLogin(BaseModel):
    email: EmailStr
    password: str


# --------------------------
# CREATE AGENT (used in CRUD)
# --------------------------

class AgentCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[AgentRole] = AgentRole.SUPPORT


# --------------------------
# RESPONSE SCHEMA
# --------------------------

class AgentResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: AgentRole
    is_active: bool
    last_login: Optional[datetime] = None

    # pydantic v2: чтобы работать с ORM-моделями
    model_config = ConfigDict(from_attributes=True)
