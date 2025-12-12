# app/crud/ticket.py
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketCRUD:
    async def get(self, db: AsyncSession, ticket_id: int) -> Optional[Ticket]:
        res = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        return res.scalar_one_or_none()

    async def get_last_active_for_user(
            self, db: AsyncSession, user_id: int
    ) -> Optional[Ticket]:
        """
        Последний незакрытый тикет пользователя:
        статус OPEN или IN_PROGRESS, самый свежий по created_at.
        """
        res = await db.execute(
            select(Ticket)
            .where(
                Ticket.user_id == user_id,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]),
                )
            .order_by(desc(Ticket.created_at))
        )
        return res.scalar_one_or_none()

    async def get_open_by_user(
            self, db: AsyncSession, user_id: int
    ) -> Optional[Ticket]:
        """
        Алиас под старое имя, которое дергает processor.process().
        По сути проксит на get_last_active_for_user.
        """
        return await self.get_last_active_for_user(db, user_id)

    async def create(self, db: AsyncSession, obj_in: TicketCreate) -> Ticket:
        """
        Создание тикета: сохраняем платформу, заголовок, описание,
        категорию, приоритет и флаг эскалации.
        Статус по умолчанию задаётся в модели (OPEN).
        """
        obj = Ticket(
            user_id=obj_in.user_id,
            platform=obj_in.platform,
            title=obj_in.title,
            description=obj_in.description,
            category=obj_in.category,
            priority=obj_in.priority,
            is_escalated=obj_in.is_escalated,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
            self, db: AsyncSession, db_obj: Ticket, obj_in: TicketUpdate
    ) -> Ticket:
        data = obj_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


ticket_crud = TicketCRUD()
# старое имя – если где-то импортировали ticket
ticket = ticket_crud
