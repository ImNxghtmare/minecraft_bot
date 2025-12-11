from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketCRUD:
    # ------------------------------------
    # CREATE TICKET
    # ------------------------------------

    async def create(
            self,
            db: AsyncSession,
            data: TicketCreate
    ) -> Ticket:

        ticket = Ticket(
            user_id=data.user_id,
            platform=data.platform,
            status=data.status,
            priority=data.priority,
            category=data.category,
            title=data.title,
            description=data.description,
            assigned_to=data.assigned_to,
            is_escalated=data.is_escalated,
        )

        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        return ticket

    # ------------------------------------
    # UPDATE
    # ------------------------------------

    async def update(
            self,
            db: AsyncSession,
            ticket_id: int,
            data: TicketUpdate
    ) -> Ticket | None:

        res = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = res.scalars().first()

        if not ticket:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ticket, field, value)

        await db.commit()
        await db.refresh(ticket)
        return ticket

    # ------------------------------------
    # GETTERS
    # ------------------------------------

    async def get(self, db: AsyncSession, ticket_id: int) -> Ticket | None:
        res = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        return res.scalars().first()

    async def get_open_by_user(self, db: AsyncSession, user_id: int) -> Ticket | None:
        """Возвращает открытый тикет пользователя — если он есть."""
        res = await db.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .where(Ticket.status.in_([
                TicketStatus.OPEN,
                TicketStatus.IN_PROGRESS,
                TicketStatus.PENDING,
            ]))
            .order_by(Ticket.id.desc())
        )
        return res.scalars().first()

    async def get_all_by_user(self, db: AsyncSession, user_id: int) -> list[Ticket]:
        res = await db.execute(
            select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.id)
        )
        return list(res.scalars())


ticket_crud = TicketCRUD()
