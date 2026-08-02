from pydantic import BaseModel
from typing import Optional


class ExerciseBase(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseOut(ExerciseBase):
    id: int

    class Config:
        from_attributes = True


class ExerciseSynonymCreate(BaseModel):
    canonical_id: int
    synonym: str
