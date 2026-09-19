from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.features.users.model import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    def add(self, user: User) -> None:
        self.session.add(user)
