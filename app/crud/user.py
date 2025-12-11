from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import PlatformType

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_platform_id(
            self, db: AsyncSession, *, platform: PlatformType, platform_id: str
    ) -> Optional[User]:
        result = await db.execute(
            select(User).where(
                User.platform == platform,
                User.platform_id == platform_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(
            self, db: AsyncSession, *, platform: PlatformType, platform_id: str,
            username: str = None, first_name: str = None, last_name: str = None
    ) -> User:
        user = await self.get_by_platform_id(db, platform=platform, platform_id=platform_id)

        if not user:
            user_in = UserCreate(
                platform=platform,
                platform_id=platform_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            user = await self.create(db, obj_in=user_in)

        return user

    async def update_last_active(self, db: AsyncSession, *, user_id: int) -> Optional[User]:
        from datetime import datetime
        user = await self.get(db, user_id)
        if user:
            user.last_active = datetime.now()
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

user_crud = CRUDUser(User)