# app/core/database.py

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ============================================================
# Base ORM
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# ENGINE
# ============================================================

DATABASE_URL = settings.database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=False,              # можешь включить True для дебага SQL
    future=True
)


# ============================================================
# SESSION FACTORY
# ============================================================

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ============================================================
# DEPENDENCY
# ============================================================

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


# ============================================================
# DATABASE INIT (CREATE TABLES)
# ============================================================

async def init_models():
    """
    Создаёт таблицы, если их нет. Вызывается при старте FastAPI.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

