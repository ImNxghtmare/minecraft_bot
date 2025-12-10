from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import ticket as ticket_crud, message as message_crud
from app.schemas.ticket import TicketInDB, TicketUpdate
from app.schemas.message import MessageInDB
from app.api.deps import get_current_active_agent, require_role
from app.models.ticket import TicketStatus, TicketPriority, TicketCategory
from app.models.agent import AgentRole

router = APIRouter()

@router.get("/", response_model=List[TicketInDB])
async def read_tickets(
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(get_current_active_agent),
        skip: int = 0,
        limit: int = 100,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        category: Optional[TicketCategory] = None,
        assigned_to_me: bool = Query(False),
        search: Optional[str] = None
):
    """Получение списка тикетов"""
    if assigned_to_me:
        # Только назначенные мне тикеты
        return await ticket_crud.get_by_agent(
            db, agent_id=current_agent.id, skip=skip, limit=limit
        )
    else:
        # Все тикеты (для админов и супервайзеров)
        if current_agent.role not in [AgentRole.ADMIN, AgentRole.SUPPORT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # TODO: Добавить фильтрацию по статусу, приоритету и поиск
        tickets = await ticket_crud.get_open_tickets(db, skip=skip, limit=limit)
        return tickets

@router.get("/{ticket_id}", response_model=TicketInDB)
async def read_ticket(
        ticket_id: int,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(get_current_active_agent)
):
    """Получение информации о тикете"""
    ticket = await ticket_crud.get(db, id=ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Проверяем доступ
    if (ticket.assigned_to != current_agent.id and
            current_agent.role not in [AgentRole.ADMIN, AgentRole.SUPPORT]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this ticket"
        )

    return ticket

@router.put("/{ticket_id}", response_model=TicketInDB)
async def update_ticket(
        ticket_id: int,
        ticket_update: TicketUpdate,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(require_role(AgentRole.SUPPORT))
):
    """Обновление тикета"""
    ticket = await ticket_crud.get(db, id=ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Проверяем, что тикет назначен на текущего агента
    if ticket.assigned_to != current_agent.id and current_agent.role != AgentRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this ticket"
        )

    ticket = await ticket_crud.update(db, db_obj=ticket, obj_in=ticket_update)
    return ticket

@router.post("/{ticket_id}/assign", response_model=TicketInDB)
async def assign_ticket(
        ticket_id: int,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(require_role(AgentRole.SUPPORT))
):
    """Назначение тикета на текущего агента"""
    ticket = await ticket_crud.assign_ticket(db, ticket_id=ticket_id, agent_id=current_agent.id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    return ticket

@router.post("/{ticket_id}/close", response_model=TicketInDB)
async def close_ticket(
        ticket_id: int,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(require_role(AgentRole.SUPPORT))
):
    """Закрытие тикета"""
    ticket = await ticket_crud.close_ticket(db, ticket_id=ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Проверяем, что тикет назначен на текущего агента
    if ticket.assigned_to != current_agent.id and current_agent.role != AgentRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to close this ticket"
        )

    return ticket

@router.post("/{ticket_id}/escalate", response_model=TicketInDB)
async def escalate_ticket(
        ticket_id: int,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(require_role(AgentRole.SUPPORT))
):
    """Эскалация тикета"""
    ticket = await ticket_crud.escalate_ticket(db, ticket_id=ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    return ticket

@router.get("/{ticket_id}/messages", response_model=List[MessageInDB])
async def read_ticket_messages(
        ticket_id: int,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(get_current_active_agent),
        skip: int = 0,
        limit: int = 100
):
    """Получение сообщений тикета"""
    # Проверяем существование тикета и доступ
    ticket = await ticket_crud.get(db, id=ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Проверяем доступ
    if (ticket.assigned_to != current_agent.id and
            current_agent.role not in [AgentRole.ADMIN, AgentRole.SUPPORT]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this ticket"
        )

    messages = await message_crud.get_by_ticket(
        db, ticket_id=ticket_id, skip=skip, limit=limit
    )

    return messages

@router.get("/stats/summary")
async def get_ticket_stats(
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(require_role(AgentRole.SUPPORT))
):
    """Получение статистики по тикетам"""
    stats = await ticket_crud.get_stats(db)
    return stats