import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message,
    PhotoSize,
    Document,
    Audio,
    Voice,
    Video,
    Sticker,
)
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

    # ======================================================================
    # Handlers
    # ======================================================================

    def _setup_handlers(self):
        self.router.message.register(self.handle_start, Command("start"))
        self.router.message.register(self.handle_operator, Command("operator"))
        self.router.message.register(self.handle_all)

    async def start(self):
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token not configured — bot disabled.")
            return

        self.bot = Bot(settings.telegram_bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.dp.include_router(self.router)

        logger.info("Telegram bot: starting POLLING mode...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        if self.bot:
            await self.bot.session.close()

    # ======================================================================
    #         USER-FACING COMMANDS
    # ======================================================================

    async def handle_start(self, msg: Message):
        await msg.answer(
            "👋 Привет! Я бот поддержки Minecraft сервера.\n"
            "Напиши свой вопрос — я создам тикет.\n"
            "Если хочешь позвать оператора: /operator"
        )

    async def handle_operator(self, msg: Message):
        await msg.answer("Оператор уведомлён. Опиши проблему подробнее 🙂")

        await message_queue.put((
            "telegram",
            {
                "message_id": msg.message_id,
                "user_id": msg.from_user.id,
                "text": msg.text,
                "call_specialist": True,
            }
        ))

    # ======================================================================
    #      CATCH-ALL: обычные сообщения
    # ======================================================================

    async def handle_all(self, msg: Message):
        logger.info(f"TG INCOMING: {msg.from_user.id} → {msg.text}")

        await message_queue.put((
            "telegram",
            {
                "message_id": msg.message_id,
                "user_id": msg.from_user.id,
                "text": msg.text,
                "caption": msg.caption,

                # attachments — передаём объекты aiogram
                "photo": msg.photo,
                "document": msg.document,
                "audio": msg.audio,
                "voice": msg.voice,
                "video": msg.video,
                "sticker": msg.sticker,
            }
        ))

    # ======================================================================
    #      Processor API (конвертация входящих сообщений)
    # ======================================================================

    async def process_message(self, data: dict) -> MessageCreate:
        """Convert raw telegram data → internal MessageCreate"""
        content = data.get("text") or data.get("caption")

        return MessageCreate(
            user_id=0,  # Processor подставит
            ticket_id=None,
            direction=MessageDirection.INCOMING,
            content=content,
            platform_message_id=str(data.get("message_id")),
            is_ai_response=False,
        )

    async def extract_attachments(self, data: dict):
        """Convert aiogram attachments → AttachmentCreate"""
        out = []

        # PHOTO
        if data.get("photo"):
            largest: PhotoSize = max(data["photo"], key=lambda p: p.file_size or 0)
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.PHOTO,
                file_id=largest.file_id,
                file_size=largest.file_size,
                caption=data.get("caption"),
            ))

        # DOCUMENT
        if data.get("document"):
            d: Document = data["document"]
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.DOCUMENT,
                file_id=d.file_id,
                mime_type=d.mime_type,
                file_size=d.file_size,
                caption=data.get("caption"),
            ))

        # AUDIO
        if data.get("audio"):
            a: Audio = data["audio"]
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.AUDIO,
                file_id=a.file_id,
                mime_type=a.mime_type,
                file_size=a.file_size,
            ))

        # VOICE
        if data.get("voice"):
            v: Voice = data["voice"]
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.VOICE,
                file_id=v.file_id,
                file_size=v.file_size,
                mime_type=v.mime_type,
            ))

        # VIDEO
        if data.get("video"):
            v: Video = data["video"]
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.VIDEO,
                file_id=v.file_id,
                file_size=v.file_size,
                mime_type=v.mime_type,
                caption=data.get("caption"),
            ))

        # STICKER
        if data.get("sticker"):
            s: Sticker = data["sticker"]
            out.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.STICKER,
                file_id=s.file_id,
            ))

        return out

    # ======================================================================
    #                     OUTGOING MESSAGES
    # ======================================================================

    async def send_message(self, user_id: str, text: str, **kwargs):
        """Processor вызывает это, чтобы отправить сообщение клиенту"""
        try:
            result = await self.bot.send_message(user_id, text, **kwargs)
            return {"success": True, "message_id": result.message_id}
        except Exception as e:
            logger.error(f"Telegram send_message error: {e}")
            return {"success": False, "error": str(e)}
