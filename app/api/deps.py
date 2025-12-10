# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.security import jwt_manager
from app.crud import agent as agent_crud
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_agent(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    """
    Получение текущего аутентифицированного агента
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодируем токен
        payload = jwt_manager.decode_token(token)

        agent_id: int = payload.get("sub")
        if agent_id is None:
            raise credentials_exception

        # Проверяем тип токена
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена",
            )

        # Получаем агента из БД
        agent = await agent_crud.get(db, id=agent_id)
        if agent is None:
            raise credentials_exception

        if not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Агент неактивен"
            )

        return agent

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise credentials_exception

async def get_current_active_agent(
        current_agent = Depends(get_current_agent)
):
    """
    Получение текущего активного агента
    """
    if not current_agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Агент неактивен"
        )
    return current_agent

def require_role(required_role: str):
    """
    Декоратор для проверки ролей
    """
    from app.models.agent import AgentRole

    def role_checker(current_agent = Depends(get_current_active_agent)):
        if current_agent.role.value != required_role and current_agent.role != AgentRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )
        return current_agent
    return role_checker

# Дополнительные зависимости для rate limiting
async def rate_limit(
        key_prefix: str = "api",
        limit: int = 100,
        window: int = 3600  # 1 час
):
    """
    Rate limiting для API
    """
    from app.core.security import rate_limiter
    from fastapi import Request

    async def rate_limit_dep(request: Request):
        client_ip = request.client.host
        endpoint = request.url.path
        key = f"{key_prefix}:{client_ip}:{endpoint}"

        allowed = await rate_limiter.check_limit(key, limit, window)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов. Попробуйте позже.",
                headers={"Retry-After": str(window)}
            )

        return True

    return Depends(rate_limit_dep)