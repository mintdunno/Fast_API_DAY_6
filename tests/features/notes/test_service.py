import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_rebuild.features.notes.model import Note, note_tags
from fastapi_rebuild.features.notes.schema import NoteCreate
from fastapi_rebuild.features.notes.service import NoteService
from fastapi_rebuild.features.tags.model import Tag
from fastapi_rebuild.features.users.model import User


async def create_user(
    session: AsyncSession,
    *,
    email: str = "owner@example.com",
) -> User:
    user = User(
        email=email,
        password_hash="test-hash",
    )

    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


def test_create_note_with_tags(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            user = await create_user(session)

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
                user_id=user.id,
            )

            note_id = note.id

            assert note_id is not None
            assert note.user_id == user.id

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
                    note_tags.c.note_id == note_id,
                )
            )

            relationships = relationship_result.all()

            assert len(relationships) == 2

    asyncio.run(run_test())


def test_create_note_with_tags_rolls_back_on_failure(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            user = await create_user(session)

            service = NoteService(session)

            call_count = 0

            async def fail_on_second_tag(
                name: str,
            ) -> Tag | None:
                nonlocal call_count

                call_count += 1

                if call_count == 2:
                    raise RuntimeError("simulated failure")

                return None

            service.tag_repository.get_by_name = fail_on_second_tag  # type: ignore[method-assign]

            with pytest.raises(
                RuntimeError,
                match="simulated failure",
            ):
                await service.create_note_with_tags(
                    NoteCreate(
                        title="This must rollback",
                        content="Transaction test",
                    ),
                    [
                        "python",
                        "database",
                    ],
                    user_id=user.id,
                )

        async with session_factory() as verify_session:
            note = await verify_session.scalar(
                select(Note).where(Note.title == "This must rollback")
            )

            python_tag = await verify_session.scalar(
                select(Tag).where(Tag.name == "python")
            )

            relationships = (await verify_session.execute(select(note_tags))).all()

            assert note is None
            assert python_tag is None
            assert relationships == []

    asyncio.run(run_test())
