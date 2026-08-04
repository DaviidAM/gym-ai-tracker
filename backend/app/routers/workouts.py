from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.workout import WorkoutCreate, WorkoutOut, WorkoutDetailOut, WorkoutSetCreate, WorkoutSetOut
from app.models.workout import Workout, WorkoutSet
from app.services.workout_set_service import create_workout_set

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[WorkoutOut])
async def list_workouts(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workout).where(Workout.user_id == user_id))
    return result.scalars().all()


@router.get("/new", response_class=HTMLResponse)
async def new_workout_form():
    return """
    <div class="modal-overlay active">
      <div class="modal-content">
        <form
          hx-post="/workouts/"
          hx-target="#workout-list"
          hx-swap="innerHTML"
          hx-on::htmx-after-request="if(event.detail.successful) { document.getElementById('modal-container').innerHTML = ''; document.getElementById('modal-container').classList.remove('active'); }"
          class="space-y-4"
        >
          <div>
            <label for="name" class="block text-sm font-medium text-gray-300 mb-1">Workout Name</label>
            <input
              type="text"
              id="name"
              name="name"
              placeholder="e.g. Push Day"
              required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label for="notes" class="block text-sm font-medium text-gray-300 mb-1">Notes (optional)</label>
            <textarea
              id="notes"
              name="notes"
              placeholder="Any notes about this workout..."
              rows="3"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
            ></textarea>
          </div>
          <div class="flex gap-3 justify-end">
            <button
              type="button"
              onclick="document.getElementById('modal-container').innerHTML = ''; document.getElementById('modal-container').classList.remove('active');"
              class="px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg font-medium transition"
            >
              Create Workout
            </button>
          </div>
        </form>
      </div>
    </div>
    """


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
            raw_name=s.raw_name,
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

    workout_set = await create_workout_set(session=db, workout_id=workout_id, data=set_in)
    await db.commit()
    await db.refresh(workout_set)
    return workout_set
