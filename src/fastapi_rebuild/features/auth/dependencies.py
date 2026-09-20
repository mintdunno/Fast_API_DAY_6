from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.core.db import get_session
from fastapi_rebuild.core.security import (
    InvalidAccessToken,
    decode_access_token,
)
from fastapi_rebuild.features.users.model import User
from fastapi_rebuild.features.users.repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_session),
    ],
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidAccessToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await UserRepository(session).get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
