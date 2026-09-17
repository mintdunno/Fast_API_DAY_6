import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from fastapi_rebuild.core.config import settings
from fastapi_rebuild.core.db import Base, get_session
from fastapi_rebuild.features.notes.model import Note  # noqa: F401
from fastapi_rebuild.features.tags.model import Tag  # noqa: F401
from fastapi_rebuild.main import app

test_engine = create_async_engine(
    settings.test_database_url,
    poolclass=NullPool,
)

TestSessionFactory = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


async def override_get_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


async def reset_database() -> None:
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    asyncio.run(reset_database())
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
