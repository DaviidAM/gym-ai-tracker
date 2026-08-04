from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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


@router.get("/count", response_class=HTMLResponse)
async def exercises_count(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Return plain text exercise count for HTMX stat cards."""
    from sqlalchemy import func
    result = await db.execute(select(func.count(Exercise.id)))
    count = result.scalar() or 0
    return str(count)


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


@router.get("/html/", response_class=HTMLResponse)
async def list_exercises_html(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).order_by(Exercise.name))
    exercises = result.scalars().all()
    if not exercises:
        return "<p class='text-gray-400'>No exercises in the library yet.</p>"
    html_parts = []
    for e in exercises:
        html_parts.append(f"""
        <div class='bg-gray-800 border border-gray-700 rounded-lg p-4 flex items-center justify-between'>
          <div>
            <span class='text-white font-medium'>{e.name}</span>
            <div class='flex gap-2 mt-1'>
              <span class='px-2 py-0.5 text-xs rounded-full bg-indigo-900 text-indigo-300'>{e.muscle_group or ''}</span>
              <span class='px-2 py-0.5 text-xs rounded-full bg-gray-700 text-gray-300'>{e.equipment or ''}</span>
            </div>
          </div>
        </div>
        """)
    return "".join(html_parts)


@router.get("/new", response_class=HTMLResponse)
async def new_exercise_form():
    return """
    <div class="modal-overlay active">
      <div class="modal-content">
        <form
          hx-post="/exercises/"
          hx-target="#exercise-list"
          hx-swap="innerHTML"
          hx-on::htmx-after-request="if(event.detail.successful) { document.getElementById('modal-container').innerHTML = ''; document.getElementById('modal-container').classList.remove('active'); }"
          class="space-y-4"
        >
          <div>
            <label for="name" class="block text-sm font-medium text-gray-300 mb-1">Exercise Name</label>
            <input
              type="text"
              id="name"
              name="name"
              placeholder="e.g. Bench Press"
              required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label for="muscle_group" class="block text-sm font-medium text-gray-300 mb-1">Muscle Group</label>
            <input
              type="text"
              id="muscle_group"
              name="muscle_group"
              placeholder="e.g. Chest"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label for="equipment" class="block text-sm font-medium text-gray-300 mb-1">Equipment</label>
            <input
              type="text"
              id="equipment"
              name="equipment"
              placeholder="e.g. Barbell"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
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
              Add Exercise
            </button>
          </div>
        </form>
      </div>
    </div>
    """
