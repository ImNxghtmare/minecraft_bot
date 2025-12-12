# app/core/processor.py
import asyncio
import logging
from typing import Optional, Tuple, List

from app.core.config import settings
from app.core.database import async_session_maker

from app.bot.telegram_bot import TelegramBot
from app.bot.vk_bot import VKBot

from app.models.user import PlatformType
from app.schemas.message import MessageCreate, MessageDirection
from app.schemas.attachment import AttachmentCreate
from app.schemas.ticket import TicketCreate
from app.models.ticket import TicketPriority, TicketCategory

from app.crud.user import user_crud
from app.crud.ticket import ticket_crud
from app.crud.message import message_crud
from app.crud.attachment import attachment_crud

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Центральный процессор:
    - стартует ботов (Telegram, VK)
    - принимает сырые сообщения из очереди
    - преобразует их в MessageCreate + AttachmentCreate[]
    - записывает в БД: users, tickets, messages, attachments
    """

    def __init__(self) -> None:
        self.telegram_bot = TelegramBot()
        self.vk_bot = VKBot()

        self._tg_task: Optional[asyncio.Task] = None
        self._vk_task: Optional[asyncio.Task] = None
        self._running: bool = False

    # ======================================================
    # START / STOP
    # ======================================================

    async def start(self) -> None:
        if self._running:
            logger.info("MessageProcessor already running, skipping second start().")
            return

        self._running = True
        logger.info("Starting bots...")

        # Telegram
        if settings.telegram_bot_token:
            logger.info("Telegram token found → starting telegram bot polling...")
            self._tg_task = asyncio.create_task(
                self.telegram_bot.start(),
                name="telegram-bot-polling",
            )
        else:
            logger.warning("Telegram bot token missing → Telegram bot NOT started.")

        # VK
        if (
                settings.vk_bot_token
                and settings.vk_group_id
                and settings.vk_confirmation_code
        ):
            logger.info("VK config OK → starting VK bot...")
            self._vk_task = asyncio.create_task(
                self.vk_bot.start(),
                name="vk-bot",
            )
        else:
            logger.warning("VK bot config incomplete → VK bot NOT started.")

    async def stop(self) -> None:
        logger.info("Stopping MessageProcessor and bots...")

        try:
            await self.telegram_bot.stop()
        except Exception as e:
            logger.exception(f"Error stopping Telegram bot: {e}")

        try:
            await self.vk_bot.stop()
        except Exception as e:
            logger.exception(f"Error stopping VK bot: {e}")

        for task in (self._tg_task, self._vk_task):
            if task and not task.done():
                task.cancel()

        self._running = False
        logger.info("MessageProcessor stopped.")

    # ======================================================
    # RAW → Pydantic
    # ======================================================

    async def handle_incoming(
            self,
            platform: PlatformType,
            data: dict,
    ) -> Tuple[MessageCreate, List[AttachmentCreate]]:
        """Конвертирует raw update → MessageCreate + AttachmentCreate[]."""

        if platform == PlatformType.TELEGRAM:
            msg = await self.telegram_bot.process_message(data)
            attachments = await self.telegram_bot.extract_attachments(data)

        elif platform == PlatformType.VK:
            msg = await self.vk_bot.process_message(data)
            attachments = await self.vk_bot.extract_attachments(data)

        else:
            raise ValueError(f"Unsupported platform: {platform}")

        return msg, attachments

    # ======================================================
    # FULL PROCESS
    # ======================================================

    async def process(self, platform_raw: str, data: dict) -> None:
        """Главный обработчик входящих событий."""

        # 1. Определяем платформу
        if platform_raw.lower() == "telegram":
            platform = PlatformType.TELEGRAM
        elif platform_raw.lower() == "vk":
            platform = PlatformType.VK
        else:
            raise ValueError(f"Unknown platform '{platform_raw}'")

        # 2. Преобразуем raw → внутренние модели
        msg_in, attachments_in = await self.handle_incoming(platform, data)

        # 3. Работа с БД
        async with async_session_maker() as db:

            # 3.1 Извлекаем данные пользователя
            if platform == PlatformType.TELEGRAM:
                tg_user = data.get("from_user") or data.get("from") or {}
                platform_id = str(tg_user.get("id", "unknown"))
                username = tg_user.get("username")
                first_name = tg_user.get("first_name")
                last_name = tg_user.get("last_name")
                language_code = tg_user.get("language_code")

            elif platform == PlatformType.VK:
                platform_id = str(
                    data.get("from_id")
                    or data.get("peer_id")
                    or "unknown"
                )
                username = None
                first_name = None
                last_name = None
                language_code = None

            else:
                platform_id = "unknown"
                username = first_name = last_name = language_code = None

            # 3.2 Находим или создаём пользователя
            user = await user_crud.create_or_get(
                db=db,
                platform=platform,
                platform_id=platform_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )

            await user_crud.update_last_active(db, user.id)

            # 3.3 Ищем открытый тикет
            ticket = await ticket_crud.get_open_by_user(db, user.id)

            if not ticket:
                title = (msg_in.content or "Новый тикет")[:255]

                ticket_in = TicketCreate(
                    user_id=user.id,
                    platform=platform,
                    title=title,
                    description=msg_in.content,
                    priority=TicketPriority.MEDIUM,
                    category=TicketCategory.OTHER,
                    is_escalated=bool(data.get("call_specialist")),
                )

                ticket = await ticket_crud.create(db, ticket_in)

            # ==================================================
            # 3.4 Создаём сообщение
            # ГАРАНТИРУЕМ direction != None
            # ==================================================
            direction = msg_in.direction or MessageDirection.INCOMING

            msg_to_save: MessageCreate = msg_in.model_copy(
                update={
                    "user_id": user.id,
                    "ticket_id": ticket.id,
                    "direction": direction,
                }
            )

            db_msg = await message_crud.create(db, msg_to_save)

            # 3.5 Вложения
            for att in attachments_in:
                att_to_save = att.model_copy(update={"message_id": db_msg.id})
                await attachment_crud.create(db, att_to_save, message_id=db_msg.id)

            logger.info(
                "Saved message %s for user=%s platform=%s ticket=%s attachments=%d",
                db_msg.id,
                user.id,
                platform.value,
                ticket.id,
                len(attachments_in),
            )


# Глобальный экземпляр
processor = MessageProcessor()
