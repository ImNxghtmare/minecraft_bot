from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, Update, User as TgUser, PhotoSize, Document, Audio, Voice, Video, Sticker
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.bot.base import BaseBot
from app.core.config import settings
from app.models.user import PlatformType
from app.schemas.message import MessageCreate, MessageDirection
from app.schemas.attachment import AttachmentCreate
from app.models.message import AttachmentType

logger = logging.getLogger(__name__)

class TelegramBot(BaseBot):
    def __init__(self):
        super().__init__(PlatformType.TELEGRAM)
        self.bot = None
        self.dp = None
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        # Команды
        self.router.message.register(self._handle_start, Command(commands=["start", "help"]))
        self.router.message.register(self._handle_operator, Command(commands=["operator"]))

        # Обработка сообщений
        self.router.message.register(self._handle_message)

    async def start(self):
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token not configured")
            return

        self.bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.dp.include_router(self.router)

        # Проверяем вебхук или polling в зависимости от настроек
        if settings.telegram_webhook_secret:
            await self._setup_webhook()
        else:
            await self._start_polling()

        logger.info("Telegram bot started")

    async def _setup_webhook(self):
        webhook_url = f"https://your-domain.com/webhook/telegram/{settings.telegram_webhook_secret}"
        await self.bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram_webhook_secret
        )
        logger.info(f"Webhook set to: {webhook_url}")

    async def _start_polling(self):
        await self.dp.start_polling(self.bot)

    async def stop(self):
        if self.bot:
            await self.bot.session.close()

    async def send_message(self, user_id: str, text: str, **kwargs) -> Dict[str, Any]:
        try:
            message = await self.bot.send_message(
                chat_id=user_id,
                text=text,
                **kwargs
            )
            return {
                "message_id": str(message.message_id),
                "success": True
            }
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_start(self, message: Message):
        welcome_text = (
            "👋 Добро пожаловать в поддержку Minecraft сервера!\n\n"
            "Я помогу вам с вопросами по:\n"
            "• Техническим проблемам\n"
            "• Игровым вопросам\n"
            "• Оплате и донату\n"
            "• Жалобам и предложениям\n\n"
            "Просто напишите ваш вопрос, и я постараюсь помочь!\n"
            "Если нужен оператор - используйте /operator"
        )
        await message.answer(welcome_text)

    async def _handle_operator(self, message: Message):
        await message.answer(
            "👨‍💼 Ваш запрос передан оператору. "
            "Скогда с вами свяжутся в этом чате."
        )
        # Здесь будет логика создания тикета

    async def _handle_message(self, message: Message):
        # Эта функция будет вызывать основной процессор
        logger.info(f"Received message from {message.from_user.id}: {message.text}")

        # Сохраняем сообщение в очередь для обработки
        from app.core.queue import message_queue
        await message_queue.put(("telegram", message.model_dump()))

    async def process_message(self, data: Dict[str, Any]) -> MessageCreate:
        """Преобразует данные Telegram в MessageCreate"""
        message = Message(**data)

        return MessageCreate(
            user_id=0,  # Будет заполнено позже
            ticket_id=None,
            direction=MessageDirection.INCOMING,
            content=message.text or message.caption,
            platform_message_id=str(message.message_id),
            is_ai_response=False
        )

    async def extract_attachments(self, data: Dict[str, Any]) -> List[AttachmentCreate]:
        """Извлекает вложения из сообщения Telegram"""
        message = Message(**data)
        attachments = []

        # Фото
        if message.photo:
            # Берем самую большую фотографию
            largest_photo: PhotoSize = max(message.photo, key=lambda p: p.file_size or 0)
            attachments.append(AttachmentCreate(
                message_id=0,  # Будет заполнено позже
                attachment_type=AttachmentType.PHOTO,
                file_id=largest_photo.file_id,
                file_size=largest_photo.file_size,
                caption=message.caption
            ))

        # Документы
        elif message.document:
            doc: Document = message.document
            attachments.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.DOCUMENT,
                file_id=doc.file_id,
                file_url=doc.file_url,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                caption=message.caption
            ))

        # Аудио
        elif message.audio:
            audio: Audio = message.audio
            attachments.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.AUDIO,
                file_id=audio.file_id,
                file_size=audio.file_size,
                mime_type=audio.mime_type,
                caption=message.caption
            ))

        # Голосовые
        elif message.voice:
            voice: Voice = message.voice
            attachments.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.VOICE,
                file_id=voice.file_id,
                file_size=voice.file_size,
                mime_type=voice.mime_type
            ))

        # Видео
        elif message.video:
            video: Video = message.video
            attachments.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.VIDEO,
                file_id=video.file_id,
                file_size=video.file_size,
                mime_type=video.mime_type,
                caption=message.caption
            ))

        # Стикеры
        elif message.sticker:
            sticker: Sticker = message.sticker
            attachments.append(AttachmentCreate(
                message_id=0,
                attachment_type=AttachmentType.STICKER,
                file_id=sticker.file_id,
                file_size=sticker.file_size,
                mime_type=sticker.mime_type
            ))

        return attachments

    def get_aiohttp_app(self):
        """Создает aiohttp приложение для вебхука"""
        if not settings.telegram_webhook_secret:
            raise ValueError("Webhook secret not configured")

        app = web.Application()

        # Хендлер для вебхука
        webhook_handler = SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
            secret_token=settings.telegram_webhook_secret
        )

        webhook_handler.register(app, path=f"/webhook/telegram/{settings.telegram_webhook_secret}")
        return app