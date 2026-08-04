#!/usr/bin/env python3
"""
Seed database with sample data for GymAI Tracker.
Run from the backend directory:
    python -m scripts.seed_db

Requires the app package to be on the PYTHONPATH or run via:
    cd backend && python -m scripts.seed_db
"""

import asyncio
import sys
from pathlib import Path

# Ensure backend/app is importable
_BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(_BACKEND_PATH))

from app.database import async_session_maker, engine, Base
from app.models.user import User
from app.models.exercise import Exercise, ExerciseSynonym
from app.models.workout import Workout, WorkoutSet
from sqlalchemy import select


EXERCISES = [
    {"name": "Barbell Bench Press", "muscle_group": "Chest", "equipment": "Barbell"},
    {"name": "Incline Dumbbell Press", "muscle_group": "Chest", "equipment": "Dumbbell"},
    {"name": "Barbell Back Squat", "muscle_group": "Quadriceps", "equipment": "Barbell"},
    {"name": "Romanian Deadlift", "muscle_group": "Hamstrings", "equipment": "Barbell"},
    {"name": "Conventional Deadlift", "muscle_group": "Back", "equipment": "Barbell"},
    {"name": "Pull-Up", "muscle_group": "Lats", "equipment": "Bodyweight"},
    {"name": "Lat Pulldown", "muscle_group": "Lats", "equipment": "Cable"},
    {"name": "Barbell Overhead Press", "muscle_group": "Shoulders", "equipment": "Barbell"},
    {"name": "Dumbbell Lateral Raise", "muscle_group": "Shoulders", "equipment": "Dumbbell"},
    {"name": "Barbell Row", "muscle_group": "Back", "equipment": "Barbell"},
    {"name": "Dumbbell Curl", "muscle_group": "Biceps", "equipment": "Dumbbell"},
    {"name": "Tricep Pushdown", "muscle_group": "Triceps", "equipment": "Cable"},
    {"name": "Leg Press", "muscle_group": "Quadriceps", "equipment": "Machine"},
    {"name": "Leg Curl", "muscle_group": "Hamstrings", "equipment": "Machine"},
    {"name": "Calf Raise", "muscle_group": "Calves", "equipment": "Machine"},
    {"name": "Plank", "muscle_group": "Core", "equipment": "Bodyweight"},
    {"name": "Cable Crunch", "muscle_group": "Core", "equipment": "Cable"},
    {"name": "Face Pull", "muscle_group": "Shoulders", "equipment": "Cable"},
    {"name": "Dumbbell Fly", "muscle_group": "Chest", "equipment": "Dumbbell"},
    {"name": "T-Bar Row", "muscle_group": "Back", "equipment": "Barbell"},
]

WORKOUTS = [
    {
        "name": "Push Day A",
        "notes": "Heavy chest and shoulders",
        "sets": [
            {"exercise_name": "Barbell Bench Press", "set_number": 1, "reps": 8, "weight_kg": 80.0, "rpe": 8},
            {"exercise_name": "Incline Dumbbell Press", "set_number": 2, "reps": 10, "weight_kg": 30.0, "rpe": 7},
            {"exercise_name": "Barbell Overhead Press", "set_number": 3, "reps": 6, "weight_kg": 50.0, "rpe": 8},
            {"exercise_name": "Dumbbell Lateral Raise", "set_number": 4, "reps": 12, "weight_kg": 10.0, "rpe": 7},
            {"exercise_name": "Tricep Pushdown", "set_number": 5, "reps": 12, "weight_kg": 25.0, "rpe": 6},
        ],
    },
    {
        "name": "Pull Day A",
        "notes": "Back and biceps focus",
        "sets": [
            {"exercise_name": "Conventional Deadlift", "set_number": 1, "reps": 5, "weight_kg": 120.0, "rpe": 8},
            {"exercise_name": "Barbell Row", "set_number": 2, "reps": 8, "weight_kg": 70.0, "rpe": 7},
            {"exercise_name": "Pull-Up", "set_number": 3, "reps": 8, "weight_kg": 0.0, "rpe": 8},
            {"exercise_name": "Lat Pulldown", "set_number": 4, "reps": 10, "weight_kg": 55.0, "rpe": 7},
            {"exercise_name": "Face Pull", "set_number": 5, "reps": 15, "weight_kg": 20.0, "rpe": 6},
            {"exercise_name": "Dumbbell Curl", "set_number": 6, "reps": 12, "weight_kg": 14.0, "rpe": 7},
        ],
    },
    {
        "name": "Leg Day A",
        "notes": "Quadriceps and hamstrings",
        "sets": [
            {"exercise_name": "Barbell Back Squat", "set_number": 1, "reps": 6, "weight_kg": 100.0, "rpe": 8},
            {"exercise_name": "Romanian Deadlift", "set_number": 2, "reps": 8, "weight_kg": 80.0, "rpe": 7},
            {"exercise_name": "Leg Press", "set_number": 3, "reps": 10, "weight_kg": 150.0, "rpe": 7},
            {"exercise_name": "Leg Curl", "set_number": 4, "reps": 12, "weight_kg": 40.0, "rpe": 6},
            {"exercise_name": "Calf Raise", "set_number": 5, "reps": 15, "weight_kg": 60.0, "rpe": 6},
        ],
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        # Check if already seeded
        result = await db.execute(select(User))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Create demo user
        user = User(
            email="demo@gymai.app",
            username="demo",
            hashed_password="hashed_demo_password",  # Not a real hash — demo only
        )
        db.add(user)
        await db.flush()

        # Create exercises
        exercise_map = {}
        for ex_data in EXERCISES:
            exercise = Exercise(**ex_data)
            db.add(exercise)
            await db.flush()
            exercise_map[ex_data["name"]] = exercise.id

        # Add synonyms
        synonyms = [
            ("Barbell Bench Press", "Flat Bench"),
            ("Barbell Bench Press", "Bench Press"),
            ("Barbell Back Squat", "Squat"),
            ("Barbell Back Squat", "Back Squat"),
            ("Romanian Deadlift", "RDL"),
            ("Conventional Deadlift", "Deadlift"),
            ("Pull-Up", "Chin-Up"),
            ("Barbell Overhead Press", "OHP"),
            ("Barbell Overhead Press", "Shoulder Press"),
        ]
        for ex_name, syn in synonyms:
            if ex_name in exercise_map:
                db.add(ExerciseSynonym(exercise_id=exercise_map[ex_name], synonym=syn))

        # Create workouts with sets
        for w_data in WORKOUTS:
            workout = Workout(
                user_id=user.id,
                name=w_data["name"],
                notes=w_data["notes"],
            )
            db.add(workout)
            await db.flush()

            for set_data in w_data["sets"]:
                exercise_id = exercise_map.get(set_data["exercise_name"])
                ws = WorkoutSet(
                    workout_id=workout.id,
                    exercise_id=exercise_id,
                    raw_name=set_data["exercise_name"] if not exercise_id else None,
                    set_number=set_data["set_number"],
                    reps=set_data["reps"],
                    weight_kg=set_data["weight_kg"],
                    rpe=set_data.get("rpe"),
                )
                db.add(ws)

        await db.commit()
        print("Database seeded successfully.")
        print(f"  - 1 demo user (demo@gymai.app)")
        print(f"  - {len(EXERCISES)} exercises")
        print(f"  - {len(synonyms)} exercise synonyms")
        print(f"  - {len(WORKOUTS)} workouts with sets")


if __name__ == "__main__":
    asyncio.run(seed())
