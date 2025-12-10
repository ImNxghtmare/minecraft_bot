from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import asyncio

from app.core.config import settings
from app.core.database import engine, Base
from app.core.processor import processor
from app.core.queue import message_queue
from app.api.v1.api import api_router
from app.crud.agent import agent as agent_crud
from app.core.database import AsyncSessionLocal

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст жизненного цикла приложения"""
    # Старт
    logger.info("Starting application...")

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем администратора
    async with AsyncSessionLocal() as db:
        await agent_crud.create_initial_admin(db, settings)

    # Запускаем ботов
    bot_task = asyncio.create_task(processor.start())

    # Запускаем обработку очереди
    queue_task = asyncio.create_task(message_queue.process_messages(processor))

    yield

    # Остановка
    logger.info("Shutting down application...")

    # Останавливаем задачи
    bot_task.cancel()
    message_queue.stop()
    queue_task.cancel()

    try:
        await asyncio.gather(bot_task, queue_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass

    await processor.telegram_bot.stop()
    await processor.vk_bot.stop()

    await engine.dispose()
    logger.info("Application shutdown complete")

# Создаем приложение
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роутеры
app.include_router(api_router, prefix="/api/v1")

# Основной маршрут
@app.get("/")
async def root():
    return {
        "message": "Minecraft Support Bot API",
        "version": settings.app_version,
        "docs": "/docs",
        "openapi": "/api/v1/openapi.json"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket для реального времени
@app.websocket("/ws/tickets")
async def websocket_tickets(websocket):
    # TODO: Реализовать WebSocket для обновлений в реальном времени
    await websocket.accept()

    try:
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )