from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.features.tags.model import Tag


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_name(self, name: str) -> Tag | None:
        statement = select(Tag).where(Tag.name == name)

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    def add(self, tag: Tag) -> None:
        self.session.add(tag)
