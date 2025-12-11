from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, PlatformType
from app.schemas.user import UserCreate, UserUpdate


class UserCRUD:

    async def get_by_platform(
            self,
            db: AsyncSession,
            platform: PlatformType,
            platform_id: str
    ) -> User | None:
        res = await db.execute(
            select(User).where(
                User.platform == platform,
                User.platform_id == platform_id
            )
        )
        return res.scalars().first()

    async def create(
            self,
            db: AsyncSession,
            user_in: UserCreate
    ) -> User:

        obj = User(
            platform=user_in.platform,
            platform_id=user_in.platform_id,
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            language_code=user_in.language_code,
            is_banned=False,
            is_blocked=False
        )

        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
            self,
            db: AsyncSession,
            db_obj: User,
            data: UserUpdate
    ) -> User:

        for field, value in data.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user_crud = UserCRUD()
