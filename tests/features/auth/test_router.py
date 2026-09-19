import httpx
import jwt
from fastapi.testclient import TestClient

from fastapi_rebuild.core.config import settings

EMAIL = "alice@example.com"
PASSWORD = "correct horse battery staple"
MINIMUM_PASSWORD = "8chrpass"
SHORT_PASSWORD = "7chrpas"


def register_user(
    client: TestClient,
    email: str = EMAIL,
    password: str = PASSWORD,
) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    return response.json()


def login(
    client: TestClient,
    email: str = EMAIL,
    password: str = PASSWORD,
) -> httpx.Response:
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["email"] == EMAIL


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": "another-password",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email already registered",
    }


def test_register_response_contains_no_password_or_hash(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 201

    body = response.json()

    # The exact key set is the load-bearing assertion: it proves no extra
    # field, such as a password or hash alias, can appear in the response.
    assert set(body.keys()) == {
        "id",
        "email",
    }

    assert PASSWORD not in response.text
    assert "$argon2" not in response.text


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": SHORT_PASSWORD,
        },
    )

    assert response.status_code == 422


def test_register_accepts_password_at_minimum_length(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": MINIMUM_PASSWORD,
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == EMAIL


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": PASSWORD,
        },
    )

    assert response.status_code == 422


def test_register_rejects_missing_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
        },
    )

    assert response.status_code == 422


def test_register_rejects_non_string_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": EMAIL,
            "password": 12345678,
        },
    )

    assert response.status_code == 422


def test_login_returns_access_token(client: TestClient) -> None:
    created = register_user(client)

    response = login(client)

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"

    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(created["id"])
    assert "exp" in payload


def test_login_response_contains_no_password_or_hash(
    client: TestClient,
) -> None:
    register_user(client)

    response = login(client)

    assert response.status_code == 200

    body = response.json()

    assert set(body.keys()) == {
        "access_token",
        "token_type",
    }

    assert PASSWORD not in response.text
    assert "$argon2" not in response.text


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register_user(client)

    response = login(client, password="wrong-password")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = login(client)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_login_failures_are_indistinguishable(client: TestClient) -> None:
    register_user(client)

    wrong_password = login(client, password="wrong-password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401

    # Byte-identical responses: a caller must not be able to tell a wrong
    # password from an account that does not exist.
    assert wrong_password.content == unknown_email.content
    assert (
        wrong_password.headers["content-type"]
        == unknown_email.headers["content-type"]
    )


def test_login_rejects_invalid_email(client: TestClient) -> None:
    response = login(client, email="not-an-email")

    assert response.status_code == 422


def test_login_rejects_missing_password(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": EMAIL,
        },
    )

    assert response.status_code == 422