from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenPayload(BaseModel):
    sub: int
    email: str
    role: str
    exp: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AgentCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "support"

class AgentResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True