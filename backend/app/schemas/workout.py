from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WorkoutSetBase(BaseModel):
    exercise_id: int
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    rpe: Optional[float] = None


class WorkoutSetCreate(WorkoutSetBase):
    pass


class WorkoutSetOut(WorkoutSetBase):
    id: int
    workout_id: int
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
