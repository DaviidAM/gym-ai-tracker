"""add_raw_name_to_workout_sets

Revision ID: c8d91e2a1f04
Revises: b1c72a0d5f2e
Create Date: 2026-08-02 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8d91e2a1f04"
down_revision: Union[str, None] = "b1c72a0d5f2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workout_sets", sa.Column("raw_name", sa.String(), nullable=True))
    # Allow NULL exercise_id when a name cannot be resolved to a canonical id.
    # SQLite does not support DROP NOT NULL directly; we rebuild the column.
    _recreate_workout_sets_allow_null_exercise_id()


def downgrade() -> None:
    _recreate_workout_sets_restore_notnull()
    op.drop_column("workout_sets", "raw_name")


def _recreate_workout_sets_allow_null_exercise_id() -> None:
    """Rebuild workout_sets to make exercise_id nullable."""
    conn = op.get_bind()

    # Fetch all existing rows so we can recreate them
    result = conn.execute(sa.text("SELECT id, workout_id, exercise_id, set_number, reps, weight_kg, rpe, created_at FROM workout_sets"))
    rows = result.fetchall()

    # Drop the FK constraint (will be re-added on downgrade)
    op.execute("PRAGMA foreign_keys = OFF")
    op.drop_constraint(
        "fk_workout_sets_exercise_id", "workout_sets", type_="foreignkey"
    )

    # Rename old table
    op.execute("ALTER TABLE workout_sets RENAME TO workout_sets_old")

    # Recreate table with nullable exercise_id
    op.create_table(
        "workout_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=True),  # ← was NOT NULL
        sa.Column("raw_name", sa.String(), nullable=True),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("rpe", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Copy data back
    if rows:
        placeholders = ", ".join(["?"] * len(rows[0]))
        op.execute(
            f"INSERT INTO workout_sets (id, workout_id, exercise_id, set_number, reps, weight_kg, rpe, created_at) "
            f"VALUES ({placeholders})",
            [tuple(row) for row in rows],
        )

    # Drop old table
    op.execute("DROP TABLE workout_sets_old")

    # Recreate FK (nullable column is fine with FK referencing nullable int)
    op.create_foreign_key(
        "fk_workout_sets_exercise_id",
        "workout_sets", "exercises",
        ["exercise_id"], ["id"],
        ondelete="CASCADE",
    )
    op.execute("PRAGMA foreign_keys = ON")


def _recreate_workout_sets_restore_notnull() -> None:
    """Restore the NOT NULL constraint on exercise_id."""
    conn = op.get_bind()

    # All rows should already have non-null exercise_id at this point
    result = conn.execute(sa.text("SELECT id, workout_id, exercise_id, raw_name, set_number, reps, weight_kg, rpe, created_at FROM workout_sets"))
    rows = result.fetchall()

    op.execute("PRAGMA foreign_keys = OFF")
    op.drop_constraint(
        "fk_workout_sets_exercise_id", "workout_sets", type_="foreignkey"
    )

    op.execute("ALTER TABLE workout_sets RENAME TO workout_sets_old")

    op.create_table(
        "workout_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),  # ← NOT NULL restored
        sa.Column("raw_name", sa.String(), nullable=True),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("rpe", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    if rows:
        # rows don't include raw_name in the SELECT above for downgrade — pad with None
        rows_with_raw = [tuple(row) + (None,) for row in rows]
        placeholders = ", ".join(["?"] * len(rows_with_raw[0]))
        op.execute(
            f"INSERT INTO workout_sets (id, workout_id, exercise_id, raw_name, set_number, reps, weight_kg, rpe, created_at) "
            f"VALUES ({placeholders})",
            [tuple(row) for row in rows_with_raw],
        )

    op.execute("DROP TABLE workout_sets_old")

    op.create_foreign_key(
        "fk_workout_sets_exercise_id",
        "workout_sets", "exercises",
        ["exercise_id"], ["id"],
        ondelete="CASCADE",
    )
    op.execute("PRAGMA foreign_keys = ON")

