# app/api/v1/endpoints/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import jwt_manager, verify_password
from app.crud.agent import agent_crud
from app.schemas.auth import Token, AgentResponse
from app.api.deps import get_current_active_agent

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
):
    """
    🔐 Аутентификация агента через OAuth2PasswordRequestForm
    (username = email)
    """
    # username = email
    agent = await agent_crud.get_by_email(db, email=form_data.username)

    if not agent or not verify_password(form_data.password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Агент неактивен",
        )

    await agent_crud.update_last_login(db, agent_id=agent.id)

    # Создаём токен
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt_manager.create_access_token(
        data={
            "sub": str(agent.id),
            "email": agent.email,
            "role": agent.role.value,
            "name": agent.full_name,
        },
        expires_delta=expires_delta,
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=AgentResponse)
async def read_me(current_agent=Depends(get_current_active_agent)):
    """👤 Информация о текущем пользователе"""
    return current_agent


@router.post("/refresh", response_model=Token)
async def refresh_token(current_agent=Depends(get_current_active_agent)):
    """
    ♻ Обновление токена без повторного логина
    """
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt_manager.create_access_token(
        data={
            "sub": str(current_agent.id),
            "email": current_agent.email,
            "role": current_agent.role.value,
            "name": current_agent.full_name,
        },
        expires_delta=expires_delta,
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )
