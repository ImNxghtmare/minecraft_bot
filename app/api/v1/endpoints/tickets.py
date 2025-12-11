from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_agent
from app.api.v1.endpoints.auth import router
from app.core.database import get_db
from app.core.processor import processor
from app.models.ticket import TicketStatus


class AgentReply(BaseModel):
    text: str

@router.post("/{ticket_id}/reply")
async def agent_reply(
        ticket_id: int,
        body: AgentReply,
        db: AsyncSession = Depends(get_db),
        current_agent = Depends(get_current_active_agent)
, ticket_crud=None):
    # Получаем тикет
    ticket_obj = await ticket_crud.get(db, id=ticket_id)
    if not ticket_obj:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Назначаем на текущего агента, если ещё не назначен
    if ticket_obj.assigned_to is None:
        ticket_obj.assigned_to = current_agent.id
        ticket_obj.status = TicketStatus.IN_PROGRESS
        db.add(ticket_obj)
        await db.commit()
        await db.refresh(ticket_obj)

    # Отправляем сообщение пользователю через processor
    # Определяем платформу и platform_id (юзер.platform, user.platform_id)
    user_obj = ticket_obj.user
    platform = user_obj.platform
    platform_id = user_obj.platform_id

    # Отправляем
    result = await processor.send_message_as_agent(
        platform=platform,
        user_id=platform_id,
        text=body.text,
        ticket_id=ticket_obj.id
    )

    return {"sent": result, "ticket": ticket_obj}