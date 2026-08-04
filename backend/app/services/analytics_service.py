"""Analytics aggregation logic using Pandas for data processing."""

from datetime import datetime, timedelta, date as date_type
from typing import Optional
import pandas as pd
from sqlalchemy import select, func, distinct, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout, WorkoutSet
from app.models.exercise import Exercise


async def get_analytics_summary(db: AsyncSession, user_id: int) -> dict:
    """
    Compute analytics summary: total workouts, total volume, favorite exercise, streak.
    """
    # Total workouts
    workout_count_result = await db.execute(
        select(func.count(distinct(Workout.id))).where(Workout.user_id == user_id)
    )
    total_workouts = workout_count_result.scalar() or 0

    # Total volume from WorkoutSet (weight_kg * reps per set)
    volume_result = await db.execute(
        select(func.coalesce(func.sum(WorkoutSet.weight_kg * WorkoutSet.reps), 0))
        .select_from(WorkoutSet)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
    )
    total_volume = volume_result.scalar() or 0.0

    # Favorite exercise (most frequent by set count)
    fav_result = await db.execute(
        select(Exercise.name, func.count(WorkoutSet.id).label("cnt"))
        .select_from(WorkoutSet)
        .join(Exercise, Exercise.id == WorkoutSet.exercise_id)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
        .group_by(Exercise.id, Exercise.name)
        .order_by(func.count(WorkoutSet.id).desc())
        .limit(1)
    )
    fav_row = fav_result.first()
    favorite_exercise = fav_row[0] if fav_row else None

    # Current streak (consecutive days with at least one workout)
    streak = await _compute_streak(db, user_id)

    return {
        "total_workouts": total_workouts,
        "total_volume": round(float(total_volume), 2),
        "favorite_exercise": favorite_exercise,
        "current_streak": streak,
    }


async def _compute_streak(db: AsyncSession, user_id: int) -> int:
    """
    Compute the current consecutive-day streak.
    A streak is broken when a day passes without a workout.
    """
    # Get distinct workout dates for the user, ordered desc
    dates_result = await db.execute(
        select(func.date(Workout.created_at).label("workout_date"))
        .where(Workout.user_id == user_id)
        .group_by(func.date(Workout.created_at))
        .order_by(func.date(Workout.created_at).desc())
    )
    rows = dates_result.fetchall()
    workout_dates: list[date_type] = []
    for row in rows:
        d = row[0]
        if isinstance(d, date_type):
            workout_dates.append(d)
        elif isinstance(d, str):
            workout_dates.append(datetime.strptime(d, "%Y-%m-%d").date())
        elif isinstance(d, datetime):
            workout_dates.append(d.date())
        else:
            workout_dates.append(date_type(d))

    if not workout_dates:
        return 0

    workout_dates.sort(reverse=True)
    most_recent = workout_dates[0]
    today = datetime.now().date()

    # If most recent is not today and not yesterday, streak is 0
    if most_recent < today - timedelta(days=1):
        return 0

    # Count consecutive days backwards
    streak = 0
    expected = most_recent
    for wd in workout_dates:
        if wd == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif wd < expected:
            break

    return streak


def _period_start(period: str) -> datetime:
    """Return start datetime for a period string."""
    now = datetime.utcnow()
    if period == "week":
        delta = timedelta(days=7)
    elif period == "month":
        delta = timedelta(days=30)
    elif period == "quarter":
        delta = timedelta(days=90)
    else:
        delta = timedelta(days=7)
    return now - delta


# ── Volume by muscle group (Phase 3 spec) ────────────────────────────────────

async def get_muscle_volume_data(
    db: AsyncSession,
    user_id: int,
    period: str = "week",
) -> dict:
    """
    Volume per muscle group: sum of (reps * weight_kg) grouped by muscle_group.
    Only includes workouts in the given period.
    """
    start = _period_start(period)
    result = await db.execute(
        select(
            func.coalesce(Exercise.muscle_group, "Unknown").label("muscle_group"),
            (func.sum(WorkoutSet.reps * WorkoutSet.weight_kg)).label("total_volume_kg"),
        )
        .select_from(WorkoutSet)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .join(Exercise, Exercise.id == WorkoutSet.exercise_id)
        .where(Workout.user_id == user_id)
        .where(Workout.created_at >= start)
        .where(WorkoutSet.reps.isnot(None))
        .where(WorkoutSet.weight_kg.isnot(None))
        .group_by(Exercise.muscle_group)
        .order_by(func.sum(WorkoutSet.reps * WorkoutSet.weight_kg).desc())
    )
    rows = result.fetchall()

    total_volume = sum(float(r.total_volume_kg or 0) for r in rows)
    breakdown = [
        {"muscle_group": r.muscle_group, "total_volume_kg": round(float(r.total_volume_kg or 0), 1)}
        for r in rows
    ]

    return {
        "period": period,
        "total_volume_kg": round(total_volume, 1),
        "muscle_breakdown": breakdown,
    }


# ── Exercise progression (Phase 3 spec) ─────────────────────────────────────

async def get_exercise_progression_data(
    db: AsyncSession,
    user_id: int,
    exercise_id: int,
    period: str = "week",
) -> dict:
    """
    Max weight per workout date for a specific exercise.
    Returns history sorted by date and a simple trend.
    """
    start = _period_start(period)

    # Get exercise name
    ex_result = await db.execute(
        select(Exercise.name).where(Exercise.id == exercise_id)
    )
    ex_row = ex_result.scalar_one_or_none()
    exercise_name = ex_row if ex_row else f"Exercise #{exercise_id}"

    result = await db.execute(
        select(
            func.date(Workout.created_at).label("date"),
            func.max(WorkoutSet.weight_kg).label("max_weight_kg"),
        )
        .select_from(WorkoutSet)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
        .where(WorkoutSet.exercise_id == exercise_id)
        .where(Workout.created_at >= start)
        .where(WorkoutSet.weight_kg.isnot(None))
        .group_by(func.date(Workout.created_at))
        .order_by(func.date(Workout.created_at).asc())
    )
    rows = result.fetchall()

    history = [
        {"date": str(r.date), "max_weight_kg": round(float(r.max_weight_kg), 1)}
        for r in rows
    ]

    # Simple trend
    trend = "stable"
    if len(history) >= 2:
        first = history[0]["max_weight_kg"]
        last = history[-1]["max_weight_kg"]
        if last > first * 1.02:
            trend = "up"
        elif last < first * 0.98:
            trend = "down"

    return {
        "exercise_id": exercise_id,
        "exercise_name": exercise_name,
        "period": period,
        "trend": trend,
        "history": history,
    }


# ── Workout frequency (Phase 3 spec) ─────────────────────────────────────────

async def get_frequency_data(
    db: AsyncSession,
    user_id: int,
    period: str = "week",
) -> dict:
    """
    Number of workouts per week in the given period.
    """
    start = _period_start(period)

    result = await db.execute(
        select(
            (func.date(Workout.created_at, "weekday 0", "-6 days")).label("week_start"),
            func.count(Workout.id).label("workout_count"),
        )
        .where(Workout.user_id == user_id)
        .where(Workout.created_at >= start)
        .group_by(func.date(Workout.created_at, "weekday 0", "-6 days"))
        .order_by(func.date(Workout.created_at, "weekday 0", "-6 days").asc())
    )
    rows = result.fetchall()

    total_workouts = sum(r.workout_count for r in rows)

    return {
        "period": period,
        "total_workouts": total_workouts,
        "weekly_breakdown": [
            {"week_start": str(r.week_start), "workout_count": r.workout_count}
            for r in rows
        ],
    }


# ── Legacy time-series volume ─────────────────────────────────────────────────

def compute_volume_series(
    workout_ids: list[int],
    exercise_ids: list[int],
    dates: list[datetime],
    weights: list[float],
    reps: list[int],
    period: str = "week",
) -> list[dict]:
    """
    Compute volume (weight * reps) aggregated by day or week.
    Uses Pandas for efficient grouping.
    Returns list of {date, volume} dicts sorted by date.
    """
    if not workout_ids:
        return []

    df = pd.DataFrame({
        "workout_id": workout_ids,
        "exercise_id": exercise_ids,
        "date": pd.to_datetime(dates),
        "weight_kg": weights,
        "reps": reps,
    })

    df["volume"] = df["weight_kg"].fillna(0) * df["reps"].fillna(0)

    if period == "day":
        df["period_key"] = df["date"].dt.normalize()
    else:  # week — use start of ISO week (Monday)
        df["period_key"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    grouped = df.groupby("period_key", as_index=False)["volume"].sum()
    grouped["period_key"] = pd.to_datetime(grouped["period_key"]).dt.strftime("%Y-%m-%d")
    grouped["volume"] = grouped["volume"].round(2)
    grouped = grouped.sort_values("period_key")

    return [
        {"date": row["period_key"], "volume": row["volume"]}
        for row in grouped.to_dict(orient="records")
    ]


def compute_progress_series(
    exercise_ids: list[int],
    exercise_names: list[str],
    dates: list[datetime],
    weights: list[float],
    reps: list[int],
) -> list[dict]:
    """
    Compute per-exercise progress (weight/reps over time).
    Returns list of {exercise_id, exercise_name, data: [{date, weight_kg, reps}]}.
    """
    if not exercise_ids:
        return []

    df = pd.DataFrame({
        "exercise_id": exercise_ids,
        "exercise_name": exercise_names,
        "date": pd.to_datetime(dates),
        "weight_kg": weights,
        "reps": reps,
    })

    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    results = []
    for ex_id, group in df.groupby("exercise_id"):
        ex_name = group["exercise_name"].iloc[0]
        daily = group.groupby("date_str").agg(
            weight_kg=("weight_kg", "max"),
            reps=("reps", "sum"),
        ).reset_index()

        data = [
            {"date": row["date_str"], "weight_kg": row["weight_kg"], "reps": int(row["reps"])}
            for row in daily.to_dict(orient="records")
        ]
        data.sort(key=lambda x: x["date"])

        results.append({
            "exercise_id": int(ex_id),
            "exercise_name": ex_name,
            "data": data,
        })

    return results


async def get_volume_data(
    db: AsyncSession,
    user_id: int,
    period: str = "week",
) -> dict:
    """Return volume aggregated by day or week (legacy time-series)."""
    result = await db.execute(
        select(
            WorkoutSet.workout_id,
            WorkoutSet.exercise_id,
            Workout.created_at,
            WorkoutSet.weight_kg,
            WorkoutSet.reps,
        )
        .select_from(WorkoutSet)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .where(Workout.user_id == user_id)
    )
    rows = result.fetchall()

    if not rows:
        return {"period": period, "data": []}

    data = compute_volume_series(
        [r[0] for r in rows],
        [r[1] for r in rows],
        [r[2] for r in rows],
        [r[3] for r in rows],
        [r[4] for r in rows],
        period,
    )
    return {"period": period, "data": data}


async def get_progress_data(db: AsyncSession, user_id: int) -> dict:
    """Return per-exercise progress over time (legacy)."""
    result = await db.execute(
        select(
            WorkoutSet.exercise_id,
            Exercise.name,
            Workout.created_at,
            WorkoutSet.weight_kg,
            WorkoutSet.reps,
        )
        .select_from(WorkoutSet)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .join(Exercise, Exercise.id == WorkoutSet.exercise_id)
        .where(Workout.user_id == user_id)
        .order_by(Exercise.id, Workout.created_at)
    )
    rows = result.fetchall()

    if not rows:
        return {"exercises": []}

    exercises = compute_progress_series(
        [r[0] for r in rows],
        [r[1] for r in rows],
        [r[2] for r in rows],
        [r[3] for r in rows],
        [r[4] for r in rows],
    )
    return {"exercises": exercises}
