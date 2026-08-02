from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.exercise import ExerciseCreate, ExerciseOut
from app.models.exercise import Exercise

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[ExerciseOut])
async def list_exercises(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise))
    return result.scalars().all()


@router.post("/", response_model=ExerciseOut)
async def create_exercise(exercise_in: ExerciseCreate, db: AsyncSession = Depends(get_db)):
    exercise = Exercise(**exercise_in.model_dump())
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise
