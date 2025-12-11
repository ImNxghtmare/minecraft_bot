from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.message import Message
from app.models.attachment import Attachment
from app.schemas.message import MessageCreate, MessageUpdate
from app.schemas.attachment import AttachmentCreate


class MessageCRUD:
    # ------------------------------------
    # CREATE MESSAGE
    # ------------------------------------

    async def create(
            self,
            db: AsyncSession,
            message_in: MessageCreate,
            attachments: list[AttachmentCreate] | None = None,
    ) -> Message:

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
        await db.flush()  # now msg.id is available

        # Attachments
        if attachments:
            for a in attachments:
                attachment = Attachment(
                    message_id=msg.id,
                    attachment_type=a.attachment_type,
                    file_id=a.file_id,
                    file_url=a.file_url,
                    file_size=a.file_size,
                    mime_type=a.mime_type,
                    caption=a.caption,
                )
                db.add(attachment)

        await db.commit()
        await db.refresh(msg)
        return msg

    # ------------------------------------
    # UPDATE STATUS
    # ------------------------------------

    async def update(
            self,
            db: AsyncSession,
            message_id: int,
            data: MessageUpdate
    ) -> Message | None:
        res = await db.execute(select(Message).where(Message.id == message_id))
        msg = res.scalars().first()

        if not msg:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
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
            select(Message).where(Message.ticket_id == ticket_id).order_by(Message.id)
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


msg_crud = MessageCRUD()
