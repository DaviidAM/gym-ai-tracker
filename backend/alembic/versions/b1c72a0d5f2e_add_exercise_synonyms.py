"""add_exercise_synonyms table

Revision ID: b1c72a0d5f2e
Revises: 922499ba11eb
Create Date: 2026-08-02 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1c72a0d5f2e"
down_revision: Union[str, None] = "922499ba11eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercise_synonyms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("synonym", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exercise_id", "synonym", name="uq_exercise_synonym_pair"),
    )
    op.create_index(
        "ix_exercise_synonyms_synonym", "exercise_synonyms", ["synonym"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_exercise_synonyms_synonym", table_name="exercise_synonyms")
    op.drop_table("exercise_synonyms")
