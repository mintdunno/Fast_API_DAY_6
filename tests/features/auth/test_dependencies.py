import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_rebuild.features.users.model import User


def test_protected_route_rejects_missing_token(
    client: TestClient,
) -> None:
    response = client.get("/notes")

    assert response.status_code == 401


def test_protected_route_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/notes",
        headers={
            "Authorization": "Bearer definitely-not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "detail": "Invalid or expired access token",
    }


def test_protected_route_rejects_token_for_deleted_user(
    client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "email": "deleted@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={
            "email": "deleted@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    async def delete_user() -> None:
        async with session_factory() as session:
            user = await session.get(User, user_id)

            assert user is not None

            await session.delete(user)
            await session.commit()

    asyncio.run(delete_user())

    response = client.get(
        "/notes",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "detail": "Invalid or expired access token",
    }
