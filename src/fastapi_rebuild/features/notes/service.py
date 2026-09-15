from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.features.notes.model import Note
from fastapi_rebuild.features.notes.repository import NoteRepository
from fastapi_rebuild.features.notes.schema import NoteCreate, NoteUpdate


class NoteNotFound(Exception):
    def __init__(self, note_id: int) -> None:
        self.note_id = note_id
        super().__init__(f"Note {note_id} not found")


class NoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = NoteRepository(session)

    async def list_notes(self) -> list[Note]:
        return await self.repository.list()

    async def get_note(self, note_id: int) -> Note:
        note = await self.repository.get(note_id)

        if note is None:
            raise NoteNotFound(note_id)

        return note

    async def create_note(self, data: NoteCreate) -> Note:
        note = Note(**data.model_dump())

        self.repository.add(note)

        await self.session.commit()
        await self.session.refresh(note)

        return note

    async def update_note(self, note_id: int, data: NoteUpdate) -> Note:
        note = await self.get_note(note_id)

        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(note, field, value)

        await self.session.commit()
        await self.session.refresh(note)

        return note

    async def delete_note(self, note_id: int) -> None:
        note = await self.get_note(note_id)

        await self.repository.delete(note)
        await self.session.commit()
