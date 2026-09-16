from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_rebuild.core.db import Base

if TYPE_CHECKING:
    from fastapi_rebuild.features.tags.model import Tag


note_tags = Table(
    "note_tags",
    Base.metadata,
    Column(
        "note_id",
        ForeignKey("notes.id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id"),
        primary_key=True,
    ),
)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=note_tags,
        back_populates="notes",
    )
