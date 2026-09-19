from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_rebuild.core.db import Base
from fastapi_rebuild.features.notes.model import note_tags

if TYPE_CHECKING:
    from fastapi_rebuild.features.notes.model import Note


class Tag(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[EmailStr] = mapped_column(
        String(50),
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    notes: Mapped[list["Note"]] = relationship(
        secondary=note_tags,
        back_populates="tags",
    )
