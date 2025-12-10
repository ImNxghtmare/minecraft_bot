# app/api/v1/endpoints/auth.py
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import jwt_manager, verify_password
from app.crud import agent as agent_crud
from app.schemas.auth import Token, AgentResponse
from app.api.deps import get_current_active_agent

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
        db: AsyncSession = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Аутентификация агента
    """
    agent = await agent_crud.get_by_email(db, email=form_data.username)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Агент неактивен"
        )

    # Обновляем время последнего входа
    await agent_crud.update_last_login(db, agent_id=agent.id)

    # Создаем токен
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = jwt_manager.create_access_token(
        data={
            "sub": str(agent.id),
            "email": agent.email,
            "role": agent.role.value,
            "name": agent.full_name
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@router.get("/me", response_model=AgentResponse)
async def read_me(
        current_agent = Depends(get_current_active_agent)
):
    """
    Получение информации о текущем агенте
    """
    return current_agent

@router.post("/refresh")
async def refresh_token(
        current_agent = Depends(get_current_active_agent)
):
    """
    Обновление JWT токена
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = jwt_manager.create_access_token(
        data={
            "sub": str(current_agent.id),
            "email": current_agent.email,
            "role": current_agent.role.value,
            "name": current_agent.full_name
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }