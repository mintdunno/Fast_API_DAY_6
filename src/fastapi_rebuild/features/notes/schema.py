from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteListQuery(BaseModel):
    status: str | None = None
    title: str | None = Field(
        default=None,
        min_length=1,
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )
    offset: int = Field(
        default=0,
        ge=0,
    )
