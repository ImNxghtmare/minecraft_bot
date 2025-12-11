from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.agent import AgentRole


# --------------------------
# TOKEN SCHEMAS
# --------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
