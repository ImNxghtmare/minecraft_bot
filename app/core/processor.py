# app/core/processor.py

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.crud.user import user_crud
from app.crud.ticket import ticket as ticket_crud
from app.crud.message import message as msg_crud
from app.schemas.ticket import TicketCreate
from app.schemas.message import MessageCreate, MessageDirection
from app.bot.telegram_bot import TelegramBot

logger = logging.getLogger(__name__)


class Processor:
    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.vk_bot = None  # позже добавим

    async def start(self):
        await self.telegram_bot.start()
        logger.info("Processor started")

    async def process_incoming_message(self, platform: str, data: dict):
        logger.info(f"PROCESSOR: received from {platform}: {data}")

        async with AsyncSessionLocal() as db:
            # 1. User ensure
            user = await user_crud.get_or_create_from_platform(
                db,
                platform=platform,
                platform_user_id=str(data["from"]["id"]),
                username=data["from"].get("username")
            )

            # 2. Ticket ensure
            ticket = await ticket_crud.get_open_ticket_for_user(db, user.id)
            if not ticket:
                ticket = await ticket_crud.create(
                    db,
                    TicketCreate(
                        user_id=user.id,
                        platform=platform,
                        title="Вопрос пользователя",
                        description=data.get("text")
                    )
                )

            # 3. Save message
            message = await msg_crud.create(
                db,
                MessageCreate(
                    user_id=user.id,
                    ticket_id=ticket.id,
                    content=data.get("text"),
                    direction=MessageDirection.INCOMING,
                ),
            )

            # 4. Basic AI or operator routing
            reply = "Спасибо! Мы получили ваше сообщение. Оператор подключится в ближайшее время."

            if platform == "telegram":
                await self.telegram_bot.send_message(
                    user.platform_user_id,
                    reply
                )


processor = Processor()
