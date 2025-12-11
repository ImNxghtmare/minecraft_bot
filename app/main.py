# app/main.py
import asyncio
import logging
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.processor import processor
from app.core.queue import message_queue
from app.api.v1.api import api_router  # <-- важно: v1

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

# CORS — dev friendly
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

# include router
app.include_router(api_router, prefix="/api/v1")

_bg_tasks: List[asyncio.Task] = []

async def _create_db_and_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ DB tables ensured.")
    except Exception as e:
        logger.exception("DB creation error: %s", e)
        raise

async def _create_initial_admin():
    try:
        async with AsyncSessionLocal() as db:
            await agent_crud.create_initial_admin(db, settings)
            await db.commit()
        logger.info("✅ Initial admin ensured.")
    except Exception as e:
        logger.exception("Initial admin error: %s", e)

async def _start_processor_and_bots():
    t1 = asyncio.create_task(processor.start(), name="processor.start")
    _bg_tasks.append(t1)
    t2 = asyncio.create_task(message_queue.process_messages(processor), name="queue.processor")
    _bg_tasks.append(t2)
    logger.info("✅ Processor and queue background tasks started.")

async def _shutdown_bg_tasks():
    logger.info("Shutting down background tasks...")
    try:
        message_queue.stop()
    except Exception:
        logger.exception("Error stopping message_queue")
    try:
        # try graceful bot stop if they exist
        if processor:
            try:
                await processor.telegram_bot.stop()
            except Exception:
                pass
            try:
                await processor.vk_bot.stop()
            except Exception:
                pass
    except Exception:
        logger.exception("Error stopping bots")
    for task in _bg_tasks:
        try:
            if not task.done():
                task.cancel()
        except Exception:
            logger.exception("Error cancelling task")
    await asyncio.sleep(0.1)
    logger.info("Background tasks stopped.")

@app.on_event("startup")
async def on_startup():
    logger.info("Starting application...")
    await _create_db_and_tables()
    await _create_initial_admin()
    await _start_processor_and_bots()
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down application...")
    await _shutdown_bg_tasks()
    try:
        await engine.dispose()
    except Exception:
        try:
            engine.sync_engine.dispose()
        except Exception:
            pass
    logger.info("Application shutdown complete.")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
