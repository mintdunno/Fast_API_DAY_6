from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_rebuild.core.db import Base
from fastapi_rebuild.features.notes.model import note_tags

if TYPE_CHECKING:
    from fastapi_rebuild.features.notes.model import Note


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )

    notes: Mapped[list["Note"]] = relationship(
        secondary=note_tags,
        back_populates="tags",
    )
