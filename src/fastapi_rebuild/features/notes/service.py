from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.features.notes.model import Note
from fastapi_rebuild.features.notes.repository import NoteRepository
from fastapi_rebuild.features.notes.schema import NoteCreate, NoteUpdate
from fastapi_rebuild.features.tags.model import Tag
from fastapi_rebuild.features.tags.repository import TagRepository


class NoteNotFound(Exception):
    def __init__(self, note_id: int) -> None:
        self.note_id = note_id
        super().__init__(f"Note {note_id} not found")


class NoteForbidden(Exception):
    def __init__(self, note_id: int) -> None:
        self.note_id = note_id
        super().__init__(f"Access to note {note_id} is forbidden")


class NoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = NoteRepository(session)
        self.tag_repository = TagRepository(session)

    async def list_notes(
        self,
        *,
        status: str | None = None,
        title: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Note]:
        return await self.repository.list(
            status=status,
            title=title,
            limit=limit,
            offset=offset,
        )

    async def get_note(
        self,
        note_id: int,
        *,
        user_id: int,
    ) -> Note:
        note = await self.repository.get(note_id)

        if note is None:
            raise NoteNotFound(note_id)

        if note.user_id != user_id:
            raise NoteForbidden(note_id)

        return note

    async def create_note(
        self,
        data: NoteCreate,
        *,
        user_id: int,
    ) -> Note:
        note = Note(
            **data.model_dump(),
            user_id=user_id,
        )

        self.repository.add(note)

        await self.session.commit()
        await self.session.refresh(note)

        return note

    async def create_note_with_tags(
        self,
        data: NoteCreate,
        tag_names: list[str],
        *,
        user_id: int,
    ) -> Note:
        try:
            note = Note(
                **data.model_dump(),
                user_id=user_id,
                tags=[],
            )

            self.repository.add(note)

            for name in dict.fromkeys(tag_names):
                tag = await self.tag_repository.get_by_name(name)

                if tag is None:
                    tag = Tag(name=name)
                    self.tag_repository.add(tag)

                note.tags.append(tag)

                await self.session.flush()

            await self.session.commit()

            return note

        except Exception:
            await self.session.rollback()
            raise

    async def update_note(
        self,
        note_id: int,
        data: NoteUpdate,
    ) -> Note:
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
