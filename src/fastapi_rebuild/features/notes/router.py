from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_rebuild.core.db import get_session
from fastapi_rebuild.features.notes.schema import (
    NoteCreate,
    NoteListQuery,
    NoteResponse,
    NoteUpdate,
)
from fastapi_rebuild.features.notes.service import NoteNotFound, NoteService

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_note_service(session: SessionDep) -> NoteService:
    return NoteService(session)


NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]


@router.get("", response_model=list[NoteResponse])
async def list_notes(
    service: NoteServiceDep,
    query: Annotated[NoteListQuery, Query()],
) -> list[NoteResponse]:
    notes = await service.list_notes(
        status=query.status,
        title=query.title,
        limit=query.limit,
        offset=query.offset,
    )

    return [NoteResponse.model_validate(note) for note in notes]


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, service: NoteServiceDep) -> NoteResponse:
    try:
        note = await service.get_note(note_id)
    except NoteNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        ) from exc

    return NoteResponse.model_validate(note)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: NoteCreate,
    service: NoteServiceDep,
) -> NoteResponse:
    note = await service.create_note(data)
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    service: NoteServiceDep,
) -> NoteResponse:
    try:
        note = await service.update_note(note_id, data)
    except NoteNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        ) from exc

    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note(
    note_id: int,
    service: NoteServiceDep,
) -> None:
    try:
        await service.delete_note(note_id)
    except NoteNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        ) from exc
