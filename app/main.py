# app/main.py

import asyncio
import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, init_models, async_session_maker
from app.core.processor import processor
from app.core.queue import message_queue
from app.api.v1.api import api_router

from app.crud.agent import agent as agent_crud

logger = logging.getLogger("minecraft_support")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")

# ---------------------------------------------------------
# BACKGROUND TASKS
# ---------------------------------------------------------

_bg_tasks: List[asyncio.Task] = []


async def _create_initial_admin():
    """
    Создаём первого админа, если его нет.
    """
    try:
        async with async_session_maker() as db:
            await agent_crud.create_initial_admin(db, settings)
            await db.commit()
        logger.info("✅ Initial admin ensured.")
    except Exception as e:
        logger.exception("Initial admin error: %s", e)


async def _start_processor_and_bots():
    """
    Запускаем:
    - обработчик сообщений
    - очередь сообщений
    - ботов
    """
    t1 = asyncio.create_task(processor.start(), name="processor.start")
    _bg_tasks.append(t1)

    t2 = asyncio.create_task(message_queue.process_messages(processor), name="queue.processor")
    _bg_tasks.append(t2)

    logger.info("✅ Processor and queue started.")


async def _shutdown_bg_tasks():
    """Остановка фоновых задач и ботов."""

    logger.info("Shutting down background tasks...")

    # queue
    try:
        message_queue.stop()
    except Exception:
        logger.exception("Queue stop error")

    # bots
    try:
        if processor.telegram_bot:
            await processor.telegram_bot.stop()
    except Exception:
        logger.exception("Error stopping Telegram bot")

    try:
        if processor.vk_bot:
            await processor.vk_bot.stop()
    except Exception:
        logger.exception("Error stopping VK bot")

    # cancel tasks
    for task in _bg_tasks:
        if not task.done():
            task.cancel()

    await asyncio.sleep(0.2)
    logger.info("Background tasks stopped.")


# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    logger.info("Starting application...")

    await init_models()               # обновлённое создание таблиц
    await _create_initial_admin()
    await _start_processor_and_bots()

    logger.info("Application startup complete.")


# ---------------------------------------------------------
# SHUTDOWN
# ---------------------------------------------------------

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down...")

    await _shutdown_bg_tasks()

    try:
        await engine.dispose()
    except Exception:
        pass

    logger.info("Shutdown complete.")


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
