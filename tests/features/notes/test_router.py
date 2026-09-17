import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import DataError

from fastapi_rebuild.features.notes.model import Note, note_tags
from fastapi_rebuild.features.notes.schema import NoteCreate
from fastapi_rebuild.features.notes.service import NoteService
from fastapi_rebuild.features.tags.model import Tag
from tests.conftest import TestSessionFactory


def create_note(
    client: TestClient,
    title: str = "Test note",
    content: str = "Test content",
) -> dict:
    response = client.post(
        "/notes",
        json={
            "title": title,
            "content": content,
        },
    )

    assert response.status_code == 201
    return response.json()


def test_create_note(client: TestClient) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Learn FastAPI",
            "content": "Rebuild Days 1-5",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["title"] == "Learn FastAPI"
    assert body["content"] == "Rebuild Days 1-5"
    assert "created_at" in body


def test_list_notes(client: TestClient) -> None:
    create_note(client, "First", "First content")
    create_note(client, "Second", "Second content")

    response = client.get("/notes")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["id"] == 1
    assert body[0]["title"] == "First"
    assert body[0]["content"] == "First content"

    assert body[1]["id"] == 2
    assert body[1]["title"] == "Second"
    assert body[1]["content"] == "Second content"


def test_list_notes_empty(client: TestClient) -> None:
    response = client.get("/notes")

    assert response.status_code == 200
    assert response.json() == []


def test_get_note(client: TestClient) -> None:
    created = create_note(
        client,
        title="My note",
        content="My content",
    )

    response = client.get(f"/notes/{created['id']}")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created["id"]
    assert body["title"] == "My note"
    assert body["content"] == "My content"
    assert "created_at" in body


def test_get_note_not_found(client: TestClient) -> None:
    response = client.get("/notes/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }


def test_update_note_title(client: TestClient) -> None:
    created = create_note(
        client,
        title="Old title",
        content="Original content",
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": "New title",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created["id"]
    assert body["title"] == "New title"

    # PATCH must preserve fields that were not sent.
    assert body["content"] == "Original content"


def test_update_note_content(client: TestClient) -> None:
    created = create_note(
        client,
        title="Original title",
        content="Old content",
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "content": "New content",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "Original title"
    assert body["content"] == "New content"


def test_update_note_multiple_fields(client: TestClient) -> None:
    created = create_note(
        client,
        title="Old title",
        content="Old content",
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": "New title",
            "content": "New content",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "New title"
    assert body["content"] == "New content"


def test_update_note_not_found(client: TestClient) -> None:
    response = client.patch(
        "/notes/999",
        json={
            "title": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }


def test_delete_note(client: TestClient) -> None:
    created = create_note(client)

    response = client.delete(f"/notes/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""

    response = client.get(f"/notes/{created['id']}")

    assert response.status_code == 404


def test_delete_note_not_found(client: TestClient) -> None:
    response = client.delete("/notes/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }


def test_create_note_rejects_empty_title(client: TestClient) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "",
            "content": "Valid content",
        },
    )

    assert response.status_code == 422


def test_create_note_rejects_title_too_long(client: TestClient) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "a" * 101,
            "content": "Valid content",
        },
    )

    assert response.status_code == 422


def test_create_note_rejects_empty_content(client: TestClient) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Valid title",
            "content": "",
        },
    )

    assert response.status_code == 422


def test_create_note_rejects_content_too_long(client: TestClient) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Valid title",
            "content": "a" * 5001,
        },
    )

    assert response.status_code == 422


def test_update_note_rejects_null_title(client: TestClient) -> None:
    created = create_note(client)

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": None,
        },
    )

    assert response.status_code == 422


def test_update_note_rejects_null_content(client: TestClient) -> None:
    created = create_note(client)

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "content": None,
        },
    )

    assert response.status_code == 422


def test_update_note_rejects_empty_title(client: TestClient) -> None:
    created = create_note(client)

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": "",
        },
    )

    assert response.status_code == 422


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
