from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from fastapi_rebuild.core.config import settings
from fastapi_rebuild.core.db import engine
from fastapi_rebuild.features.auth.router import router as auth_router
from fastapi_rebuild.features.notes.router import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()

    yield

    await app.state.http_client.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(notes_router)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
