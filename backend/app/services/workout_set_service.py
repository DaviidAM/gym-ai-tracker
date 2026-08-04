"""WorkoutSet persistence service.

Wires the exercise name normalizer into the workout-set save path.
Each incoming ``WorkoutSetCreate`` is normalised before the row is
written to the ``workout_sets`` table.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise, ExerciseSynonym
from app.models.workout import WorkoutSet
from app.schemas.workout import WorkoutSetCreate
from app.services.exercise_normalizer import LookupResult, normalize

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


async def create_workout_set(
    session: AsyncSession,
    workout_id: int,
    data: WorkoutSetCreate,
) -> WorkoutSet:
    """
    Persist a workout set, normalising the free-text exercise name.

    Logic
    -----
    1. If ``exercise_id`` is already provided, use it directly (caller already
       resolved the canonical id).
    2. If ``exercise_name`` is supplied, run it through the three-tier
       normalizer (exact → synonym → fuzzy).  Store the original text in
       ``raw_name`` so the original intent is preserved.
    3. If the normalizer returns ``None`` (no confident match) the raw name
       is still stored and a warning is emitted for later manual synonym entry.

    The caller is responsible for committing the session.
    """
    raw_name: str | None = None
    resolved_id: int | None = None

    if data.exercise_name:
        # Always store the raw name when the caller submitted a free-text name.
        # This preserves the user's exact input regardless of whether the
        # normalizer resolved it to a canonical id or not.
        raw_name = data.exercise_name

        if data.exercise_id is None:
            # Fetch all exercises and synonyms, then call normalize synchronously.
            # The normalizer itself is pure / stateless; only the lookup is async.
            ex_result = await session.execute(select(Exercise))
            syn_result = await session.execute(select(ExerciseSynonym))
            exercises: list[tuple[int, str]] = [
                (row.id, row.name) for row in ex_result.scalars().all()
            ]
            synonyms: list[tuple[int, str]] = [
                (row.exercise_id, row.synonym) for row in syn_result.scalars().all()
            ]

            def lookup() -> LookupResult:
                return LookupResult(exercises=exercises, synonyms=synonyms)

            resolved_id = normalize(data.exercise_name, lookup=lookup)
            if resolved_id is None:
                logger.warning(
                    "No exercise match for %r; preserving raw name. "
                    "Consider adding a synonym to resolve it.",
                    data.exercise_name,
                )
            # If normalized successfully, exercise_id is set; raw_name is still
            # stored (above) so we have the user's original input on record.

    # Use the caller-supplied id if available; otherwise fall back to the
    # resolved id from normalization (which may be None).
    exercise_id = data.exercise_id or resolved_id  # type: ignore[assignment]

    workout_set = WorkoutSet(
        workout_id=workout_id,
        exercise_id=exercise_id,  # type: ignore[arg-type]  # None is allowed → raw_name preserved
        raw_name=raw_name,
        set_number=data.set_number,
        reps=data.reps,
        weight_kg=data.weight_kg,
        rpe=data.rpe,
    )
    session.add(workout_set)
    await session.flush()
    return workout_set
