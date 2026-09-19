from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.core.db import get_session
from fastapi_rebuild.features.auth.schema import UserLogin
from fastapi_rebuild.features.auth.service import (
    AuthService,
    EmailAlreadyRegistered,
    InvalidCredentials,
)
from fastapi_rebuild.features.users.schema import (
    TokenResponse,
    UserRegister,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserRegister,
    service: AuthServiceDep,
) -> UserResponse:
    try:
        user = await service.register(data)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    service: AuthServiceDep,
) -> TokenResponse:
    try:
        access_token = await service.login(data)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc

    return TokenResponse(access_token=access_token)