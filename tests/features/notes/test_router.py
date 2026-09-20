from fastapi.testclient import TestClient


def create_note(
    client: TestClient,
    auth_headers: dict[str, str],
    title: str = "Test note",
    content: str = "Test content",
) -> dict:
    response = client.post(
        "/notes",
        json={
            "title": title,
            "content": content,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    return response.json()


def test_create_note(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Learn FastAPI",
            "content": "Rebuild Days 1-5",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["title"] == "Learn FastAPI"
    assert body["content"] == "Rebuild Days 1-5"
    assert "created_at" in body


def test_list_notes(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_note(
        client,
        auth_headers,
        "First",
        "First content",
    )
    create_note(
        client,
        auth_headers,
        "Second",
        "Second content",
    )

    response = client.get("/notes")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["id"] == 2
    assert body[0]["title"] == "Second"
    assert body[0]["content"] == "Second content"

    assert body[1]["id"] == 1
    assert body[1]["title"] == "First"
    assert body[1]["content"] == "First content"


def test_list_notes_empty(client: TestClient) -> None:
    response = client.get("/notes")

    assert response.status_code == 200
    assert response.json() == []


def test_get_note(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
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


def test_update_note_title(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
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
    assert body["content"] == "Original content"


def test_update_note_content(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
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


def test_update_note_multiple_fields(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
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


def test_delete_note(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
    )

    response = client.delete(
        f"/notes/{created['id']}",
    )

    assert response.status_code == 204
    assert response.content == b""

    response = client.get(
        f"/notes/{created['id']}",
    )

    assert response.status_code == 404


def test_delete_note_not_found(client: TestClient) -> None:
    response = client.delete("/notes/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }


def test_create_note_rejects_empty_title(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "",
            "content": "Valid content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_note_rejects_title_too_long(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "a" * 101,
            "content": "Valid content",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_note_rejects_empty_content(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Valid title",
            "content": "",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_note_rejects_content_too_long(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/notes",
        json={
            "title": "Valid title",
            "content": "a" * 5001,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_update_note_rejects_null_title(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": None,
        },
    )

    assert response.status_code == 422


def test_update_note_rejects_null_content(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "content": None,
        },
    )

    assert response.status_code == 422


def test_update_note_rejects_empty_title(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = create_note(
        client,
        auth_headers,
    )

    response = client.patch(
        f"/notes/{created['id']}",
        json={
            "title": "",
        },
    )

    assert response.status_code == 422


def test_list_notes_filters_by_title(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_note(
        client,
        auth_headers,
        "Learn Python",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Learn FastAPI",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Python backend",
        "Content",
    )

    response = client.get(
        "/notes",
        params={
            "title": "python",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert [note["title"] for note in body] == [
        "Python backend",
        "Learn Python",
    ]


def test_list_notes_filters_by_status(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_note(
        client,
        auth_headers,
        "First",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Second",
        "Content",
    )

    response = client.get(
        "/notes",
        params={
            "status": "active",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get(
        "/notes",
        params={
            "status": "archived",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_notes_pagination(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_note(
        client,
        auth_headers,
        "First",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Second",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Third",
        "Content",
    )
    create_note(
        client,
        auth_headers,
        "Fourth",
        "Content",
    )

    response = client.get(
        "/notes",
        params={
            "limit": 2,
            "offset": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert [note["title"] for note in body] == [
        "Third",
        "Second",
    ]


def test_list_notes_rejects_invalid_pagination(
    client: TestClient,
) -> None:
    response = client.get(
        "/notes",
        params={
            "limit": 0,
            "offset": -1,
        },
    )

    assert response.status_code == 422
