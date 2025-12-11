import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, PhotoSize, Document, Audio, Voice, Video, Sticker
from aiogram.enums import ParseMode
from aiogram.filters import Command

from app.core.config import settings
from app.bot.base import BaseBot
from app.core.queue import message_queue
from app.models.user import PlatformType
from app.schemas.message import MessageCreate, MessageDirection
from app.schemas.attachment import AttachmentCreate
from app.models.message import AttachmentType

logger = logging.getLogger(__name__)


class TelegramBot(BaseBot):
    def __init__(self):
        super().__init__(PlatformType.TELEGRAM)

        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.router = Router()

        self._setup_handlers()

    # ============================
    # Handlers
    # ============================
    def _setup_handlers(self):
        self.router.message.register(self.handle_start, Command("start"))
        self.router.message.register(self.handle_operator, Command("operator"))
        self.router.message.register(self.handle_any)

    async def start(self):
        """Запуск POLLING режима"""
        if not settings.telegram_bot_token:
            logger.warning("Telegram token отсутствует.")
            return

        self.bot = Bot(settings.telegram_bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.dp.include_router(self.router)

        logger.info("Telegram POLLING запущен")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        if self.bot:
            await self.bot.session.close()

    # ============================
    # Incoming handlers
    # ============================

    async def handle_start(self, msg: Message):
        await msg.answer(
            "👋 Привет!\n"
            "Я бот поддержки Minecraft.\n"
            "Просто напиши свою проблему."
        )

        # передадим в Processor как INCOMING
        await message_queue.put(("telegram", msg.model_dump()))

    async def handle_operator(self, msg: Message):
        await msg.answer("Оператор будет уведомлён, опиши проблему подробнее.")

        payload = msg.model_dump()
        payload["call_specialist"] = True

        await message_queue.put(("telegram", payload))

    async def handle_any(self, msg: Message):
        logger.info(f"[TG] INCOMING {msg.from_user.id}: {msg.text}")
        await message_queue.put(("telegram", msg.model_dump()))

    # ============================
    # Processor API
    # ============================

    async def process_message(self, data: dict) -> MessageCreate:
        """Processor вызывает это — преобразуем telegram message → MessageCreate"""
        msg = Message(**data)

        return MessageCreate(
            user_id=0,  # Processor заполнит
            ticket_id=None,
            direction=MessageDirection.INCOMING,
            content=msg.text or msg.caption or "",
            platform_message_id=str(msg.message_id),
            is_ai_response=False,
        )

    async def extract_attachments(self, data: dict):
        msg = Message(**data)
        result = []

        # PHOTO
        if msg.photo:
            largest: PhotoSize = max(msg.photo, key=lambda p: p.file_size or 0)
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.PHOTO,
                file_id=largest.file_id,
                file_size=largest.file_size,
                caption=msg.caption
            ))

        # DOCUMENT
        if msg.document:
            d: Document = msg.document
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.DOCUMENT,
                file_id=d.file_id,
                file_size=d.file_size,
                mime_type=d.mime_type,
                caption=msg.caption
            ))

        # AUDIO
        if msg.audio:
            a: Audio = msg.audio
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.AUDIO,
                file_id=a.file_id,
                mime_type=a.mime_type,
                file_size=a.file_size
            ))

        # VOICE
        if msg.voice:
            v: Voice = msg.voice
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.VOICE,
                file_id=v.file_id,
                mime_type=v.mime_type,
                file_size=v.file_size
            ))

        # VIDEO
        if msg.video:
            v: Video = msg.video
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.VIDEO,
                file_id=v.file_id,
                mime_type=v.mime_type,
                file_size=v.file_size,
                caption=msg.caption
            ))

        # STICKER
        if msg.sticker:
            s: Sticker = msg.sticker
            result.append(AttachmentCreate(
                attachment_type=AttachmentType.STICKER,
                file_id=s.file_id
            ))

        return result

    # ============================
    # Outgoing
    # ============================

    async def send_message(self, user_id: str, text: str, **kwargs):
        try:
            sent = await self.bot.send_message(user_id, text, **kwargs)
            return {"success": True, "message_id": sent.message_id}
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {"success": False, "error": str(e)}
