from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from fastapi_rebuild.core.config import settings

password_hash = PasswordHash.recommended()

# A real hash of a throwaway value. Login verifies against this when the
# requested account does not exist, so a failed attempt costs the same whether
# or not the email is registered.
dummy_password_hash = password_hash.hash("dummy-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
