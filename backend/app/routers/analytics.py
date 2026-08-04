from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.database import get_db
from app.models.workout import Workout, WorkoutSet
from app.models.exercise import Exercise
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])


class VolumeDataPoint(BaseModel):
    muscle_group: str
    total_volume: float
    total_sets: int


class ProgressionDataPoint(BaseModel):
    date: str
    weight_kg: float
    reps: int
    sets: int


class FrequencyDataPoint(BaseModel):
    week: str
    workout_count: int


def period_start(period: str) -> datetime:
    now = datetime.utcnow()
    if period == "week":
        return now - timedelta(days=7)
    elif period == "month":
        return now - timedelta(days=30)
    elif period == "quarter":
        return now - timedelta(days=90)
    return now - timedelta(days=30)


@router.get("/volume", response_model=list[VolumeDataPoint])
async def get_volume(
    period: str = Query("month", enum=["week", "month", "quarter"]),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    start = period_start(period)
    result = await db.execute(
        select(
            Exercise.muscle_group,
            func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label("total_volume"),
            func.count(WorkoutSet.id).label("total_sets"),
        )
        .join(WorkoutSet, WorkoutSet.exercise_id == Exercise.id)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(
            and_(
                Workout.user_id == user_id,
                Workout.created_at >= start,
            )
        )
        .group_by(Exercise.muscle_group)
        .order_by(func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).desc())
    )
    rows = result.all()
    return [
        VolumeDataPoint(
            muscle_group=row.muscle_group or "other",
            total_volume=float(row.total_volume or 0),
            total_sets=row.total_sets,
        )
        for row in rows
    ]


@router.get("/progression", response_model=list[ProgressionDataPoint])
async def get_progression(
    exercise_id: int,
    period: str = Query("month", enum=["week", "month", "quarter"]),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    start = period_start(period)
    result = await db.execute(
        select(
            func.date(Workout.created_at).label("date"),
            func.avg(WorkoutSet.weight_kg).label("weight_kg"),
            func.sum(WorkoutSet.reps).label("reps"),
            func.count(WorkoutSet.id).label("sets"),
        )
        .join(WorkoutSet, WorkoutSet.workout_id == Workout.id)
        .where(
            and_(
                Workout.user_id == user_id,
                WorkoutSet.exercise_id == exercise_id,
                Workout.created_at >= start,
            )
        )
        .group_by(func.date(Workout.created_at))
        .order_by(func.date(Workout.created_at))
    )
    rows = result.all()
    return [
        ProgressionDataPoint(
            date=str(row.date),
            weight_kg=round(float(row.weight_kg or 0), 1),
            reps=row.reps or 0,
            sets=row.sets,
        )
        for row in rows
    ]


@router.get("/frequency", response_model=list[FrequencyDataPoint])
async def get_frequency(
    period: str = Query("month", enum=["week", "month", "quarter"]),
    user_id: int = 1,
    db: AsyncSession = Depends(get_db),
):
    start = period_start(period)
    result = await db.execute(
        select(
            func.strftime("%Y-W%W", Workout.created_at).label("week"),
            func.count(Workout.id).label("workout_count"),
        )
        .where(
            and_(
                Workout.user_id == user_id,
                Workout.created_at >= start,
            )
        )
        .group_by("week")
        .order_by("week")
    )
    rows = result.all()
    return [
        FrequencyDataPoint(week=row.week, workout_count=row.workout_count)
        for row in rows
    ]


@router.get("/summary")
async def get_analytics_summary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Return HTML summary card for the analytics page (used by HTMX)."""
    from sqlalchemy import func, and_
    from app.models.workout import Workout, WorkoutSet
    from app.models.exercise import Exercise
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total workouts
    total_result = await db.execute(
        select(func.count(Workout.id)).where(Workout.user_id == user_id)
    )
    total_workouts = total_result.scalar() or 0

    # Workouts this week
    week_result = await db.execute(
        select(func.count(Workout.id)).where(
            and_(Workout.user_id == user_id, Workout.created_at >= week_ago)
        )
    )
    workouts_this_week = week_result.scalar() or 0

    # Total exercises
    ex_result = await db.execute(
        select(func.count(WorkoutSet.id))
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
    )
    total_sets = ex_result.scalar() or 0

    # Top muscle group
    top_muscle_result = await db.execute(
        select(Exercise.muscle_group, func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label("volume"))
        .join(WorkoutSet, WorkoutSet.exercise_id == Exercise.id)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(and_(Workout.user_id == user_id, Workout.created_at >= month_ago))
        .group_by(Exercise.muscle_group)
        .order_by(func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).desc())
        .limit(1)
    )
    top_muscle_row = top_muscle_result.first()
    top_muscle = top_muscle_row.muscle_group.title() if top_muscle_row else "None yet"

    return f"""
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gray-800 rounded-xl p-4">
        <div class="text-gray-400 text-sm">Total Workouts</div>
        <div class="text-3xl font-bold text-white">{total_workouts}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4">
        <div class="text-gray-400 text-sm">This Week</div>
        <div class="text-3xl font-bold text-cyan-400">{workouts_this_week}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4">
        <div class="text-gray-400 text-sm">Total Sets</div>
        <div class="text-3xl font-bold text-white">{total_sets}</div>
      </div>
      <div class="bg-gray-800 rounded-xl p-4">
        <div class="text-gray-400 text-sm">Top Muscle Group</div>
        <div class="text-3xl font-bold text-indigo-400">{top_muscle}</div>
      </div>
    </div>
    """


@router.get("/exercises", response_model=list[dict])
async def get_exercises_for_selector(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Return exercises that have workout data for the selector dropdown."""
    result = await db.execute(
        select(Exercise.id, Exercise.name, Exercise.muscle_group)
        .join(WorkoutSet, WorkoutSet.exercise_id == Exercise.id)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
        .distinct()
        .order_by(Exercise.name)
    )
    rows = result.all()
    return [
        {"id": row.id, "name": row.name, "muscle_group": row.muscle_group}
        for row in rows
    ]
