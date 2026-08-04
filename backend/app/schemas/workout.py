from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WorkoutSetBase(BaseModel):
    exercise_id: int | None = None  # canonical id; resolved from exercise_name if not provided
    exercise_name: str | None = None  # raw free-text name; run through normalizer when present
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    rpe: Optional[float] = None


class WorkoutSetCreate(WorkoutSetBase):
    pass


class WorkoutSetOut(WorkoutSetBase):
    id: int
    workout_id: int
    raw_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutBase(BaseModel):
    name: str
    notes: Optional[str] = None


class WorkoutCreate(WorkoutBase):
    pass


class WorkoutOut(WorkoutBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutDetailOut(WorkoutOut):
    sets: list[WorkoutSetOut] = []

    class Config:
        from_attributes = True
