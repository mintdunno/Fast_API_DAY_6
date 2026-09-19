from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.core.security import (
    create_access_token,
    dummy_password_hash,
    hash_password,
    verify_password,
)
from fastapi_rebuild.features.auth.schema import UserLogin
from fastapi_rebuild.features.users.model import User
from fastapi_rebuild.features.users.repository import UserRepository
from fastapi_rebuild.features.users.schema import UserRegister


class EmailAlreadyRegistered(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} is already registered")


class InvalidCredentials(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def register(self, data: UserRegister) -> User:
        email = str(data.email)

        if await self.repository.get_by_email(email) is not None:
            raise EmailAlreadyRegistered(email)

        user = User(
            email=email,
            password_hash=hash_password(data.password),
        )

        self.repository.add(user)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            # The unique constraint is the only reliable guard when two
            # registrations for the same email race past the check above.
            await self.session.rollback()
            raise EmailAlreadyRegistered(email) from exc

        await self.session.refresh(user)

        return user

    async def login(self, data: UserLogin) -> str:
        user = await self.repository.get_by_email(str(data.email))

        password_matches = verify_password(
            data.password,
            user.password_hash if user is not None else dummy_password_hash,
        )

        # The unknown account is checked separately: the dummy hash is a real
        # hash of a known value, so it verifies successfully on its own.
        if user is None or not password_matches:
            raise InvalidCredentials

        return create_access_token(user.id)