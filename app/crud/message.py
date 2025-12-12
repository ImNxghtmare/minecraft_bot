# app/crud/message.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message, MessageDirection, MessageStatus
from app.schemas.message import MessageCreate, MessageUpdate


class MessageCRUD:
    # ------------------------------------
    # CREATE MESSAGE
    # ------------------------------------
    async def create(
            self,
            db: AsyncSession,
            message_in: MessageCreate,
    ) -> Message:
        """
        Создание сообщения без поля role (его нет в модели).
        direction и status приходят из MessageCreate (с дефолтами).
        """

        msg = Message(
            user_id=message_in.user_id,
            ticket_id=message_in.ticket_id,

            direction=message_in.direction,
            status=message_in.status,

            content=message_in.content,
            is_ai_response=message_in.is_ai_response,
            confidence_score=message_in.confidence_score,
            platform_message_id=message_in.platform_message_id,
        )

        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    # ------------------------------------
    # UPDATE
    # ------------------------------------
    async def update(
            self,
            db: AsyncSession,
            message_id: int,
            data: MessageUpdate,
    ) -> Message | None:
        res = await db.execute(select(Message).where(Message.id == message_id))
        msg = res.scalars().first()

        if not msg:
            return None

        # role тут тоже не трогаем — его нет в модели
        for field, value in data.model_dump(exclude_unset=True).items():
            if hasattr(msg, field):
                setattr(msg, field, value)

        await db.commit()
        await db.refresh(msg)
        return msg

    # ------------------------------------
    # GETTERS
    # ------------------------------------
    async def get(self, db: AsyncSession, msg_id: int) -> Message | None:
        res = await db.execute(select(Message).where(Message.id == msg_id))
        return res.scalars().first()

    async def get_by_ticket(self, db: AsyncSession, ticket_id: int) -> list[Message]:
        res = await db.execute(
            select(Message)
            .where(Message.ticket_id == ticket_id)
            .order_by(Message.id)
        )
        return list(res.scalars())

    async def get_last_by_user(self, db: AsyncSession, user_id: int) -> Message | None:
        res = await db.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(1)
        )
        return res.scalars().first()


message_crud = MessageCRUD()
