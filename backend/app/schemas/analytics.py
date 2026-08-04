from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AnalyticsSummary(BaseModel):
    total_workouts: int
    total_volume: float  # kg
    favorite_exercise: Optional[str] = None
    current_streak: int  # consecutive days with workouts


class VolumeDataPoint(BaseModel):
    date: str  # ISO date string YYYY-MM-DD
    volume: float  # kg


class VolumeResponse(BaseModel):
    period: str  # "day" or "week"
    data: list[VolumeDataPoint]


# ── Volume by muscle group (Phase 3 spec) ────────────────────────────────────

class MuscleVolumePoint(BaseModel):
    muscle_group: str
    total_volume_kg: float


class MuscleVolumeResponse(BaseModel):
    period: str  # "week" | "month" | "quarter"
    total_volume_kg: float
    muscle_breakdown: list[MuscleVolumePoint]


# ── Exercise progression (Phase 3 spec) ─────────────────────────────────────

class ProgressionDataPoint(BaseModel):
    date: str  # ISO date string YYYY-MM-DD
    max_weight_kg: float


class ProgressionResponse(BaseModel):
    exercise_id: int
    exercise_name: str
    period: str
    trend: str  # "up" | "down" | "stable"
    history: list[ProgressionDataPoint]


# ── Workout frequency (Phase 3 spec) ────────────────────────────────────────

class WeeklyFrequencyPoint(BaseModel):
    week_start: str  # ISO date string YYYY-MM-DD
    workout_count: int


class FrequencyResponse(BaseModel):
    period: str  # "week" | "month" | "quarter"
    total_workouts: int
    weekly_breakdown: list[WeeklyFrequencyPoint]


# ── Progress (legacy) ────────────────────────────────────────────────────────

class ProgressDataPoint(BaseModel):
    date: str  # ISO date string YYYY-MM-DD
    weight_kg: Optional[float] = None
    reps: Optional[int] = None


class ExerciseProgress(BaseModel):
    exercise_id: int
    exercise_name: str
    data: list[ProgressDataPoint]


class ProgressResponse(BaseModel):
    exercises: list[ExerciseProgress]
