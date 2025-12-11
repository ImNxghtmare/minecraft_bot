import asyncio
import logging

from app.core.queue import message_queue
from app.core.database import async_session_maker

from app.models.user import PlatformType

from app.crud.user import user_crud
from app.crud.ticket import ticket_crud
from app.crud.message import msg_crud
from app.crud.attachment import attachment_crud

from app.bot.telegram_bot import TelegramBot
# from app.bot.vk_bot import VkBot  # если понадобится

logger = logging.getLogger("processor")


class Processor:
    def __init__(self):
        self.bots = {
            PlatformType.TELEGRAM: TelegramBot(),
            # PlatformType.VK: VkBot(),
        }

    async def start(self):
        # запускаем polling у ботов
        for bot in self.bots.values():
            asyncio.create_task(bot.start())

        # запускаем очередь
        asyncio.create_task(message_queue.process_messages(self))
        logger.info("Processor started")

    async def process(self, platform: str, raw: dict):
        platform_type = PlatformType(platform)

        bot = self.bots.get(platform_type)
        if not bot:
            logger.error(f"No bot for platform: {platform}")
            return

        async with async_session_maker() as db:

            # 1) создать или найти пользователя
            user_data = raw.get("from_user") or raw.get("from") or {}
            platform_id = str(user_data.get("id"))

            user = await user_crud.get_by_platform(
                db, platform_type, platform_id
            )

            if not user:
                user = await user_crud.create(
                    db,
                    user_in={
                        "platform": platform_type,
                        "platform_id": platform_id,
                        "username": user_data.get("username"),
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name"),
                        "language_code": user_data.get("language_code"),
                    }
                )

            # 2) найти или создать открытый тикет
            ticket = await ticket_crud.get_open_by_user(db, user.id)

            if not ticket:
                ticket = await ticket_crud.create(
                    db,
                    data={
                        "user_id": user.id,
                        "platform": platform_type,
                        "title": "Support Ticket",
                        "description": raw.get("text") or "",
                        "priority": None,
                        "category": None,
                        "status": None,
                        "assigned_to": None,
                        "is_escalated": False,
                    }
                )

            # 3) сохранить сообщение
            msg_obj = await msg_crud.create(
                db,
                message_in={
                    "user_id": user.id,
                    "ticket_id": ticket.id,
                    "direction": "INCOMING",
                    "content": raw.get("text") or raw.get("caption"),
                    "platform_message_id": str(raw.get("message_id")),
                    "is_ai_response": False,
                    "confidence_score": None,
                    "status": None,
                }
            )

            # 4) вложения
            attachments = await bot.extract_attachments(raw)
            if attachments:
                await attachment_crud.create(
                    db,
                    message_id=msg_obj.id,
                    attachment_in=attachments
                )

            await db.commit()

            # 5) (опционально) ответить
            # await bot.send_message(user.platform_id, "Сообщение принято")

