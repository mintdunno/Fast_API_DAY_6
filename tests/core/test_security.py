from datetime import UTC, datetime, timedelta

import jwt
import pytest

from fastapi_rebuild.core.config import settings
from fastapi_rebuild.core.security import (
    InvalidAccessToken,
    create_access_token,
    decode_access_token,
)

# Deliberately not the configured signing key, so tokens signed with it are
# rejected on signature verification.
FOREIGN_KEY = "not-the-signing-key"


def future_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=5)


def past_expiry() -> datetime:
    return datetime.now(UTC) - timedelta(minutes=1)


def encode_token(
    payload: dict,
    *,
    key: str = settings.jwt_secret,
    algorithm: str = settings.jwt_algorithm,
) -> str:
    return jwt.encode(
        payload,
        key,
        algorithm=algorithm,
    )


def test_decode_access_token_returns_user_id() -> None:
    token = create_access_token(4321)

    user_id = decode_access_token(token)

    assert user_id == 4321
    assert isinstance(user_id, int)


def test_decode_access_token_rejects_foreign_signature() -> None:
    token = encode_token(
        {
            "sub": "1",
            "exp": future_expiry(),
        },
        key=FOREIGN_KEY,
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_expired_token() -> None:
    token = encode_token(
        {
            "sub": "1",
            "exp": past_expiry(),
        }
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_other_algorithm() -> None:
    token = encode_token(
        {
            "sub": "1",
            "exp": future_expiry(),
        },
        algorithm="HS384",
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_malformed_token() -> None:
    with pytest.raises(InvalidAccessToken):
        decode_access_token("not-a-token")


def test_decode_access_token_rejects_missing_subject() -> None:
    token = encode_token(
        {
            "exp": future_expiry(),
        }
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_missing_expiry() -> None:
    token = encode_token(
        {
            "sub": "1",
        }
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_non_numeric_subject() -> None:
    token = encode_token(
        {
            "sub": "not-a-number",
            "exp": future_expiry(),
        }
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_decode_access_token_rejects_non_string_subject() -> None:
    token = encode_token(
        {
            "sub": 1,
            "exp": future_expiry(),
        }
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)