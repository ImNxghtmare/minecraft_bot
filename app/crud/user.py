# app/crud/user.py
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, PlatformType
from app.schemas.user import UserCreate


class UserCRUD:
    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        res = await db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_platform_id(
            self,
            db: AsyncSession,
            *,
            platform: PlatformType,
            platform_id: str,
    ) -> Optional[User]:
        res = await db.execute(
            select(User).where(
                User.platform == platform,
                User.platform_id == platform_id,
                )
        )
        return res.scalar_one_or_none()

    async def get_or_create(
            self,
            db: AsyncSession,
            *,
            platform: PlatformType,
            platform_id: str,
            username: str | None = None,
            first_name: str | None = None,
            last_name: str | None = None,
            language_code: str | None = None,
    ) -> User:
        """
        Основной метод: ищем пользователя по platform + platform_id,
        если нет — создаём.
        """
        user = await self.get_by_platform_id(
            db, platform=platform, platform_id=platform_id
        )
        if user:
            return user

        obj = User(
            platform=platform,
            platform_id=platform_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def create_or_get(
            self,
            db: AsyncSession,
            *,
            platform: PlatformType,
            platform_id: str,
            username: str | None = None,
            first_name: str | None = None,
            last_name: str | None = None,
            language_code: str | None = None,
    ) -> User:
        """
        Алиас под старое название, которое вызывает processor.process().
        По факту просто прокидывает в get_or_create.
        """
        return await self.get_or_create(
            db=db,
            platform=platform,
            platform_id=platform_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )

    async def update_last_active(self, db: AsyncSession, user_id: int) -> None:
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            return
        user.last_active = datetime.utcnow()
        db.add(user)
        await db.commit()

    # Для совместимости со старым кодом, который вызывал get_or_create_from_platform
    async def get_or_create_from_platform(
            self,
            db: AsyncSession,
            *,
            platform: str,
            platform_user_id: str,
            username: str | None = None,
    ) -> User:
        platform_enum = PlatformType[platform.upper()]
        return await self.get_or_create(
            db,
            platform=platform_enum,
            platform_id=platform_user_id,
            username=username,
        )


user_crud = UserCRUD()
# старое имя, если где-то используется from app.crud.user import user
user = user_crud
