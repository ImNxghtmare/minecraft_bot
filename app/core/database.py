# app/core/database.py
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

# Асинхронный движок
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_models() -> None:
    """Создание таблиц (вызывается в on_startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ DB tables ensured.")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Используй это как dependency в FastAPI (get_db)."""
    async with async_session_maker() as session:
        yield session


# Для старого кода, который импортирует get_db
get_db = get_session
