from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.models.ticket import TicketStatus, TicketPriority

class CRUDTicket(CRUDBase[Ticket, TicketCreate, TicketUpdate]):
    async def get_by_user(
            self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Ticket]:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_open_tickets(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Ticket]:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]))
            .order_by(Ticket.priority.desc(), Ticket.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_agent(
            self, db: AsyncSession, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[Ticket]:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.assigned_to == agent_id)
            .order_by(Ticket.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def assign_ticket(
            self, db: AsyncSession, *, ticket_id: int, agent_id: int
    ) -> Optional[Ticket]:
        ticket = await self.get(db, ticket_id)
        if ticket:
            ticket.assigned_to = agent_id
            ticket.status = TicketStatus.IN_PROGRESS
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
        return ticket

    async def close_ticket(self, db: AsyncSession, *, ticket_id: int) -> Optional[Ticket]:
        ticket = await self.get(db, ticket_id)
        if ticket:
            ticket.status = TicketStatus.CLOSED
            ticket.closed_at = datetime.now()
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
        return ticket

    async def escalate_ticket(self, db: AsyncSession, *, ticket_id: int) -> Optional[Ticket]:
        ticket = await self.get(db, ticket_id)
        if ticket:
            ticket.is_escalated = True
            ticket.priority = TicketPriority.HIGH
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
        return ticket

    async def get_stats(self, db: AsyncSession) -> dict:
        from sqlalchemy import func, extract

        # Общая статистика
        total_result = await db.execute(select(func.count(Ticket.id)))
        total = total_result.scalar()

        open_result = await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.OPEN)
        )
        open_count = open_result.scalar()

        # Статистика по приоритетам
        priorities_result = await db.execute(
            select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        )
        priorities = dict(priorities_result.all())

        # Среднее время ответа
        response_time_result = await db.execute(
            select(func.avg(func.timestampdiff(func.MINUTE, Ticket.created_at, Ticket.first_response_at)))
            .where(Ticket.first_response_at.isnot(None))
        )
        avg_response_time = response_time_result.scalar() or 0

        return {
            "total": total,
            "open": open_count,
            "priorities": priorities,
            "avg_response_time_minutes": round(avg_response_time, 2)
        }

ticket = CRUDTicket(Ticket)