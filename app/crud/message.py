from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.crud.base import CRUDBase
from app.models.message import Message, Attachment
from app.schemas.message import MessageCreate, MessageUpdate
from app.schemas.attachment import AttachmentCreate
from app.models.message import MessageDirection

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_by_ticket(
            self, db: AsyncSession, *, ticket_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.ticket_id == ticket_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_user(
            self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(desc(Message.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_last_user_message(
            self, db: AsyncSession, *, user_id: int
    ) -> Optional[Message]:
        result = await db.execute(
            select(Message)
            .where(
                Message.user_id == user_id,
                Message.direction == MessageDirection.INCOMING
            )
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_with_attachments(
            self, db: AsyncSession, *, obj_in: MessageCreate, attachments: List[AttachmentCreate] = None
    ) -> Message:
        message = await self.create(db, obj_in=obj_in)

        if attachments:
            for attachment_in in attachments:
                attachment = Attachment(**attachment_in.dict())
                message.attachments.append(attachment)

            db.add(message)
            await db.commit()
            await db.refresh(message)

        return message

message = CRUDMessage(Message)