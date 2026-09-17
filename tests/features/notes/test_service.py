# tests/features/notes/test_service.py

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DataError

from fastapi_rebuild.features.notes.model import Note, note_tags
from fastapi_rebuild.features.notes.schema import NoteCreate
from fastapi_rebuild.features.notes.service import NoteService
from fastapi_rebuild.features.tags.model import Tag
from tests.conftest import TestSessionFactory


def test_create_note_with_tags() -> None:
    async def run_test() -> None:
        async with TestSessionFactory() as session:
            service = NoteService(session)

            note = await service.create_note_with_tags(
                NoteCreate(
                    title="Learn transactions",
                    content="Atomic writes",
                ),
                [
                    "python",
                    "database",
                ],
            )

            assert note.id is not None

            tags_result = await session.scalars(select(Tag).order_by(Tag.name))
            tags = list(tags_result.all())

            assert [tag.name for tag in tags] == [
                "database",
                "python",
            ]

            relationship_result = await session.execute(
                select(
                    note_tags.c.note_id,
                    note_tags.c.tag_id,
                ).where(
                    note_tags.c.note_id == note.id,
                )
            )

            relationships = relationship_result.all()

            assert len(relationships) == 2

    asyncio.run(run_test())


def test_create_note_with_tags_rolls_back_on_failure() -> None:
    async def run_test() -> None:
        async with TestSessionFactory() as session:
            service = NoteService(session)

            data = NoteCreate(
                title="This must rollback",
                content="Transaction test",
            )

            invalid_tag_name = "x" * 51

            with pytest.raises(DataError):
                await service.create_note_with_tags(
                    data,
                    [
                        "python",
                        invalid_tag_name,
                    ],
                )

            note = await session.scalar(
                select(Note).where(Note.title == "This must rollback")
            )

            python_tag = await session.scalar(select(Tag).where(Tag.name == "python"))

            relationship_result = await session.execute(select(note_tags))

            relationships = relationship_result.all()

            assert note is None
            assert python_tag is None
            assert relationships == []

    asyncio.run(run_test())
