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
    synonym: str


class ExerciseSynonymOut(BaseModel):
    id: int
    exercise_id: int
    synonym: str

    class Config:
        from_attributes = True
