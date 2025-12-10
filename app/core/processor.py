import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.telegram_bot import TelegramBot
from app.bot.vk_bot import VKBot
from app.crud import user, ticket, message as message_crud
from app.models.user import PlatformType
from app.models.ticket import TicketStatus, TicketCategory
from app.schemas.ticket import TicketCreate
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class MessageProcessor:
    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.vk_bot = VKBot()
        self.bots = {
            PlatformType.TELEGRAM: self.telegram_bot,
            PlatformType.VK: self.vk_bot
        }

    async def start(self):
        """Запуск всех ботов"""
        tasks = []

        if self.telegram_bot:
            tasks.append(self.telegram_bot.start())

        if self.vk_bot:
            tasks.append(self.vk_bot.start())

        await asyncio.gather(*tasks)

    async def process_incoming_message(self, platform: str, data: Dict[str, Any]):
        """Обработка входящего сообщения"""
        platform_type = PlatformType(platform)
        bot = self.bots.get(platform_type)

        if not bot:
            logger.error(f"No bot for platform: {platform}")
            return

        async with AsyncSessionLocal() as db:
            try:
                # Извлекаем информацию о пользователе
                user_info = self._extract_user_info(platform_type, data)

                # Получаем или создаем пользователя
                db_user = await user.get_or_create(
                    db,
                    platform=platform_type,
                    platform_id=user_info['platform_id'],
                    username=user_info.get('username'),
                    first_name=user_info.get('first_name'),
                    last_name=user_info.get('last_name')
                )

                # Обновляем время последней активности
                await user.update_last_active(db, user_id=db_user.id)

                # Преобразуем сообщение
                message_create = await bot.process_message(data)
                message_create.user_id = db_user.id

                # Извлекаем вложения
                attachments = await bot.extract_attachments(data)

                # Проверяем, есть ли открытый тикет у пользователя
                open_ticket = await self._get_open_ticket(db, db_user.id)

                if not open_ticket:
                    # Создаем новый тикет
                    ticket_create = TicketCreate(
                        user_id=db_user.id,
                        platform=platform_type,
                        title=self._generate_ticket_title(message_create.content),
                        description=message_create.content,
                        category=self._detect_category(message_create.content)
                    )
                    open_ticket = await ticket.create(db, obj_in=ticket_create)

                message_create.ticket_id = open_ticket.id

                # Сохраняем сообщение
                db_message = await message_crud.create_with_attachments(
                    db,
                    obj_in=message_create,
                    attachments=attachments
                )

                # Обновляем attachments с правильным message_id
                for att in attachments:
                    att.message_id = db_message.id

                # Отправляем ответ
                await self._send_response(
                    bot, db_user, open_ticket, db_message, platform_type
                )

                await db.commit()
                logger.info(f"Processed message from {db_user}")

            except Exception as e:
                await db.rollback()
                logger.error(f"Error processing message: {e}")
                raise

    def _extract_user_info(self, platform: PlatformType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает информацию о пользователе из данных платформы"""
        if platform == PlatformType.TELEGRAM:
            # Для Telegram через aiogram
            from aiogram.types import Message as TgMessage
            msg = TgMessage(**data)
            return {
                'platform_id': str(msg.from_user.id),
                'username': msg.from_user.username,
                'first_name': msg.from_user.first_name,
                'last_name': msg.from_user.last_name
            }

        elif platform == PlatformType.VK:
            # Для VK
            msg = data.get('message', {})
            return {
                'platform_id': str(msg.get('from_id')),
                'username': None,  # VK не дает username в Callback API
                'first_name': None,
                'last_name': None
            }

        return {}

    async def _get_open_ticket(self, db: AsyncSession, user_id: int):
        """Получает открытый тикет пользователя"""
        user_tickets = await ticket.get_by_user(db, user_id=user_id)
        for t in user_tickets:
            if t.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING]:
                return t
        return None

    def _generate_ticket_title(self, content: Optional[str]) -> str:
        """Генерирует заголовок тикета на основе сообщения"""
        if not content:
            return "Вопрос без текста"

        # Берем первые 50 символов
        title = content[:50]
        if len(content) > 50:
            title += "..."

        return title

    def _detect_category(self, content: Optional[str]) -> TicketCategory:
        """Определяет категорию тикета на основе сообщения"""
        if not content:
            return TicketCategory.OTHER

        content_lower = content.lower()

        keywords = {
            TicketCategory.TECHNICAL: ['лаги', 'краш', 'ошибка', 'баг', 'технический', 'не работает', 'вылетает'],
            TicketCategory.GAMEPLAY: ['игра', 'сервер', 'режим', 'вайп', 'доступ', 'ip', 'коннект'],
            TicketCategory.PAYMENT: ['донат', 'оплата', 'деньги', 'покупка', 'купить', 'премиум', 'вип'],
            TicketCategory.COMPLAINT: ['жалоба', 'бан', 'кик', 'нарушение', 'правила', 'админ', 'модератор']
        }

        for category, words in keywords.items():
            if any(word in content_lower for word in words):
                return category

        return TicketCategory.OTHER

    async def _send_response(self, bot, db_user, ticket_obj, message_obj, platform: PlatformType):
        """Отправляет ответ пользователю"""
        # Пока отправляем простой ответ
        # В будущем здесь будет AI или шаблонные ответы

        response_text = (
            "✅ Ваше сообщение получено!\n"
            f"Номер заявки: #{ticket_obj.id}\n"
            "Наш оператор скоро свяжется с вами.\n\n"
            "А пока вы можете:\n"
            "• Описать проблему подробнее\n"
            "• Прикрепить скриншоты\n"
            "• Указать никнейм в игре"
        )

        await bot.send_message(
            user_id=db_user.platform_id,
            text=response_text
        )

        # Сохраняем исходящее сообщение
        async with AsyncSessionLocal() as db:
            outgoing_message = await message_crud.create(
                db,
                obj_in={
                    "ticket_id": ticket_obj.id,
                    "user_id": db_user.id,
                    "direction": "outgoing",
                    "content": response_text,
                    "is_ai_response": True
                }
            )
            await db.commit()

    async def send_message_as_agent(
            self, platform: PlatformType, user_id: str, text: str, ticket_id: int = None
    ):
        """Отправка сообщения от имени агента"""
        bot = self.bots.get(platform)
        if not bot:
            raise ValueError(f"No bot for platform: {platform}")

        # Отправляем через бота
        result = await bot.send_message(user_id, text)

        # Сохраняем в БД
        async with AsyncSessionLocal() as db:
            # Находим пользователя
            db_user = await user.get_by_platform_id(
                db, platform=platform, platform_id=user_id
            )

            if db_user:
                await message_crud.create(
                    db,
                    obj_in={
                        "ticket_id": ticket_id,
                        "user_id": db_user.id,
                        "direction": "outgoing",
                        "content": text,
                        "is_ai_response": False,
                        "platform_message_id": result.get("message_id")
                    }
                )
                await db.commit()

        return result

# Создаем глобальный процессор
processor = MessageProcessor()