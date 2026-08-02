from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.workout import WorkoutCreate, WorkoutOut, WorkoutDetailOut, WorkoutSetCreate, WorkoutSetOut
from app.models.workout import Workout, WorkoutSet

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[WorkoutOut])
async def list_workouts(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workout).where(Workout.user_id == user_id))
    return result.scalars().all()


@router.post("/", response_model=WorkoutOut, status_code=201)
async def create_workout(workout_in: WorkoutCreate, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    workout = Workout(user_id=user_id, **workout_in.model_dump())
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


@router.get("/{workout_id}", response_model=WorkoutDetailOut)
async def get_workout(workout_id: int, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Workout.id, Workout.user_id, Workout.name, Workout.notes, Workout.created_at)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
    )
    workout_row = result.first()
    if not workout_row:
        raise HTTPException(status_code=404, detail="Workout not found")

    workout_id_val, user_id_val, name_val, notes_val, created_at_val = workout_row

    sets_result = await db.execute(
        select(WorkoutSet).where(WorkoutSet.workout_id == workout_id).order_by(WorkoutSet.set_number)
    )
    sets = [
        WorkoutSetOut(
            id=s.id,
            workout_id=s.workout_id,
            exercise_id=s.exercise_id,
            set_number=s.set_number,
            reps=s.reps,
            weight_kg=s.weight_kg,
            rpe=s.rpe,
            created_at=s.created_at,
        )
        for s in sets_result.scalars().all()
    ]
    return WorkoutDetailOut(
        id=workout_id_val,
        user_id=user_id_val,
        name=name_val,
        notes=notes_val,
        created_at=created_at_val,
        sets=sets,
    )


@router.post("/{workout_id}/sets", response_model=WorkoutSetOut, status_code=201)
async def add_workout_set(workout_id: int, set_in: WorkoutSetCreate, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    # Verify workout exists and belongs to user
    workout_result = await db.execute(
        select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id)
    )
    workout = workout_result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    workout_set = WorkoutSet(workout_id=workout_id, **set_in.model_dump())
    db.add(workout_set)
    await db.commit()
    await db.refresh(workout_set)
    return workout_set
