from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentCreate


class AttachmentCRUD:
    async def create(
            self,
            db: AsyncSession,
            attachment_in: AttachmentCreate,
            message_id: int
    ) -> Attachment:

        obj = Attachment(
            message_id=message_id,
            attachment_type=attachment_in.attachment_type,
            file_id=attachment_in.file_id,
            file_url=attachment_in.file_url,
            file_size=attachment_in.file_size,
            mime_type=attachment_in.mime_type,
            caption=attachment_in.caption,
        )

        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


attachment_crud = AttachmentCRUD()
