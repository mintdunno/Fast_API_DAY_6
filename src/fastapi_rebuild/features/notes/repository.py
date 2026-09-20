from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_rebuild.features.notes.model import Note


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        status: str | None = None,
        title: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Note]:
        statement = (
            select(Note).options(selectinload(Note.tags)).where(Note.user_id == user_id)
        )

        if status is not None:
            statement = statement.where(Note.status == status)

        if title is not None:
            statement = statement.where(Note.title.ilike(f"%{title}%"))

        statement = (
            statement.order_by(
                Note.created_at.desc(),
                Note.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(statement)

        return list(result.all())

    async def get(self, note_id: int) -> Note | None:
        return await self.session.get(Note, note_id)

    def add(self, note: Note) -> None:
        self.session.add(note)

    async def delete(self, note: Note) -> None:
        await self.session.delete(note)
