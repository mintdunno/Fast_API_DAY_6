from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_rebuild.core.config import settings
from fastapi_rebuild.core.db import engine
from fastapi_rebuild.features.notes.router import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(notes_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
