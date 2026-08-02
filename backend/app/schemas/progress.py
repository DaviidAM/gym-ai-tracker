from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProgressBase(BaseModel):
    exercise_id: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    sets: Optional[int] = None


class ProgressCreate(ProgressBase):
    pass


class ProgressOut(ProgressBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True
