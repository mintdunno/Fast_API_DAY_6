import asyncio

import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_rebuild.core.config import settings
from fastapi_rebuild.core.security import verify_password
from fastapi_rebuild.features.auth.schema import UserLogin
from fastapi_rebuild.features.auth.service import (
    AuthService,
    EmailAlreadyRegistered,
    InvalidCredentials,
)
from fastapi_rebuild.features.users.model import User
from fastapi_rebuild.features.users.schema import UserRegister

EMAIL = "alice@example.com"
PASSWORD = "correct horse battery staple"


async def count_users(session: AsyncSession, email: str) -> int:
    result = await session.scalar(
        select(func.count()).select_from(User).where(User.email == email)
    )

    return result or 0


def test_register_persists_user_with_hashed_password(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            service = AuthService(session)

            user = await service.register(
                UserRegister(email=EMAIL, password=PASSWORD)
            )

            assert user.id is not None
            assert user.email == EMAIL
            assert user.password_hash != PASSWORD
            assert verify_password(PASSWORD, user.password_hash)

        # Verify with a new session that the row actually reached PostgreSQL.
        async with session_factory() as verify_session:
            stored = await verify_session.scalar(
                select(User).where(User.email == EMAIL)
            )

            assert stored is not None
            assert stored.password_hash != PASSWORD

    asyncio.run(run_test())


def test_register_rejects_duplicate_email(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            service = AuthService(session)

            await service.register(UserRegister(email=EMAIL, password=PASSWORD))

            with pytest.raises(EmailAlreadyRegistered):
                await service.register(
                    UserRegister(email=EMAIL, password="another-password")
                )

        async with session_factory() as verify_session:
            assert await count_users(verify_session, EMAIL) == 1

    asyncio.run(run_test())


def test_register_rejects_duplicate_email_that_races_past_the_check(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            await AuthService(session).register(
                UserRegister(email=EMAIL, password=PASSWORD)
            )

        async with session_factory() as session:
            service = AuthService(session)

            # Simulate the race: the lookup misses, so the insert is the only
            # thing that can reject the duplicate.
            async def no_existing_user(email: str) -> User | None:
                return None

            service.repository.get_by_email = no_existing_user  # type: ignore[method-assign]

            with pytest.raises(EmailAlreadyRegistered):
                await service.register(
                    UserRegister(email=EMAIL, password="another-password")
                )

            # The failed transaction must have been rolled back rather than
            # left aborted, so the session keeps working.
            assert await count_users(session, EMAIL) == 1

        async with session_factory() as verify_session:
            assert await count_users(verify_session, EMAIL) == 1

    asyncio.run(run_test())


def test_login_returns_access_token_for_valid_credentials(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            service = AuthService(session)

            user = await service.register(
                UserRegister(email=EMAIL, password=PASSWORD)
            )

            token = await service.login(UserLogin(email=EMAIL, password=PASSWORD))

            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )

            assert payload["sub"] == str(user.id)

    asyncio.run(run_test())


def test_login_rejects_unknown_email(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            service = AuthService(session)

            with pytest.raises(InvalidCredentials):
                await service.login(UserLogin(email=EMAIL, password=PASSWORD))

    asyncio.run(run_test())


def test_login_rejects_wrong_password(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def run_test() -> None:
        async with session_factory() as session:
            service = AuthService(session)

            await service.register(UserRegister(email=EMAIL, password=PASSWORD))

            with pytest.raises(InvalidCredentials):
                await service.login(
                    UserLogin(email=EMAIL, password="wrong-password")
                )

    asyncio.run(run_test())