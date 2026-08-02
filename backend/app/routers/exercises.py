from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.schemas.exercise import ExerciseCreate, ExerciseOut, ExerciseSynonymCreate, ExerciseSynonymOut
from app.models.exercise import Exercise, ExerciseSynonym

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


@router.post("/{exercise_id}/synonyms", response_model=ExerciseSynonymOut, status_code=201)
async def add_synonym(
    exercise_id: int,
    synonym_in: ExerciseSynonymCreate,
    db: AsyncSession = Depends(get_db),
):
    # Validate exercise exists
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Exercise not found")

    synonym = ExerciseSynonym(exercise_id=exercise_id, synonym=synonym_in.synonym)
    db.add(synonym)
    try:
        await db.commit()
        await db.refresh(synonym)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Synonym already exists for this exercise")

    return synonym


@router.delete("/{exercise_id}/synonyms/{synonym_id}", status_code=204)
async def delete_synonym(
    exercise_id: int,
    synonym_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExerciseSynonym).where(
            ExerciseSynonym.id == synonym_id,
            ExerciseSynonym.exercise_id == exercise_id,
        )
    )
    synonym = result.scalar_one_or_none()
    if synonym is None:
        raise HTTPException(status_code=404, detail="Synonym not found")

    await db.delete(synonym)
    await db.commit()
    return None
