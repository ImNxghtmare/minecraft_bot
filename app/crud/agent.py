from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.models.agent import Agent, AgentRole
from app.schemas.auth import AgentCreate, AgentLogin
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AgentCRUD:

    async def get_by_id(self, db: AsyncSession, agent_id: int) -> Agent | None:
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        return res.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> Agent | None:
        res = await db.execute(select(Agent).where(Agent.email == email))
        return res.scalars().first()

    async def create(self, db: AsyncSession, agent_in: AgentCreate) -> Agent:
        hashed_pw = pwd_context.hash(agent_in.password)

        obj = Agent(
            email=agent_in.email,
            password_hash=hashed_pw,
            full_name=agent_in.full_name,
            role=agent_in.role,
            is_active=True,
        )

        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def authenticate(self, db: AsyncSession, data: AgentLogin) -> Agent | None:
        agent = await self.get_by_email(db, data.email)
        if not agent:
            return None
        if not pwd_context.verify(data.password, agent.password_hash):
            return None
        return agent

    async def create_initial_admin(self, db: AsyncSession, settings):
        if not settings.first_admin_email:
            return

        exists = await self.get_by_email(db, settings.first_admin_email)
        if exists:
            return

        admin_data = AgentCreate(
            email=settings.first_admin_email,
            password=settings.first_admin_password,
            full_name=settings.first_admin_name,
            role=AgentRole.ADMIN,
        )

        await self.create(db, admin_data)


agent_crud = AgentCRUD()
