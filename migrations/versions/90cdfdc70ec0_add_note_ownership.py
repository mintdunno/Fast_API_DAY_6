"""add note ownership

Revision ID: 90cdfdc70ec0
Revises: 53bc058c5a13
Create Date: 2026-09-20 11:50:37.103457

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "90cdfdc70ec0"
down_revision: str | Sequence[str] | None = "53bc058c5a13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notes",
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.create_foreign_key(
        "fk_notes_user_id_users",
        "notes",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_notes_user_id_users",
        "notes",
        type_="foreignkey",
    )

    op.drop_column(
        "notes",
        "user_id",
    )
