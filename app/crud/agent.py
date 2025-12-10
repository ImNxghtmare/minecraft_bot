from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.crud.base import CRUDBase
from app.models.agent import Agent
from app.schemas.auth import AgentCreate
from app.models.agent import AgentRole

class CRUDAgent(CRUDBase[Agent, AgentCreate, AgentCreate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.email == email))
        return result.scalar_one_or_none()

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[Agent]:
        agent = await self.get_by_email(db, email=email)
        if not agent:
            return None
        if not agent.verify_password(password):
            return None
        return agent

    async def update_last_login(self, db: AsyncSession, *, agent_id: int) -> Optional[Agent]:
        from datetime import datetime
        agent = await self.get(db, agent_id)
        if agent:
            agent.last_login = datetime.now()
            db.add(agent)
            await db.commit()
            await db.refresh(agent)
        return agent

    async def create_initial_admin(self, db: AsyncSession, settings) -> Optional[Agent]:
        # Проверяем, есть ли уже администратор
        admin = await self.get_by_email(db, email=settings.first_admin_email)
        if admin:
            return admin

        # Создаем администратора
        admin_in = AgentCreate(
            email=settings.first_admin_email,
            password=settings.first_admin_password,
            full_name=settings.first_admin_name,
            role=AgentRole.ADMIN.value
        )
        admin_data = admin_in.dict()
        admin_data["password_hash"] = Agent.hash_password(admin_data.pop("password"))
        admin = Agent(**admin_data)

        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin

agent = CRUDAgent(Agent)