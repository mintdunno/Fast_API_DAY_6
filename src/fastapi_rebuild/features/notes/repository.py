from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.features.notes.model import Note


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Note]:
        result = await self.session.scalars(select(Note).order_by(Note.id))
        return list(result.all())

    async def get(self, note_id: int) -> Note | None:
        return await self.session.get(Note, note_id)

    def add(self, note: Note) -> None:
        self.session.add(note)

    async def delete(self, note: Note) -> None:
        await self.session.delete(note)
