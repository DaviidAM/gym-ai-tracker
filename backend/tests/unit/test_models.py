"""Unit tests for SQLAlchemy models."""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workout import Workout
from app.models.exercise import Exercise, ExerciseSynonym
from app.models.progress import Progress


class TestUserModel:
    async def test_create_user(self, db_session_for_app: AsyncSession):
        """User can be created with required fields."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_secret",
        )
        db_session_for_app.add(user)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password == "hashed_secret"
        assert user.created_at is not None

    async def test_user_email_unique_constraint(
        self, db_session_for_app: AsyncSession
    ):
        """Duplicate email raises error on commit."""
        user1 = User(email="dup@example.com", username="user1", hashed_password="x")
        db_session_for_app.add(user1)
        await db_session_for_app.commit()

        user2 = User(email="dup@example.com", username="user2", hashed_password="y")
        db_session_for_app.add(user2)
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            await db_session_for_app.commit()

    async def test_user_username_unique_constraint(
        self, db_session_for_app: AsyncSession
    ):
        """Duplicate username raises error on commit."""
        user1 = User(email="a@example.com", username="dupuser", hashed_password="x")
        db_session_for_app.add(user1)
        await db_session_for_app.commit()

        user2 = User(email="b@example.com", username="dupuser", hashed_password="y")
        db_session_for_app.add(user2)
        with pytest.raises(Exception):
            await db_session_for_app.commit()

    async def test_user_default_created_at(
        self, db_session_for_app: AsyncSession
    ):
        """created_at is set automatically on creation."""
        user = User(email="time@example.com", username="timeuser", hashed_password="x")
        db_session_for_app.add(user)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(user)

        assert isinstance(user.created_at, datetime)


class TestWorkoutModel:
    async def test_create_workout(self, db_session_for_app: AsyncSession):
        """Workout can be created linked to a user."""
        user = User(email="w@example.com", username="wuser", hashed_password="x")
        db_session_for_app.add(user)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(user)

        workout = Workout(
            user_id=user.id,
            name="Morning Cardio",
            notes="Light jogging",
        )
        db_session_for_app.add(workout)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(workout)

        assert workout.id is not None
        assert workout.user_id == user.id
        assert workout.name == "Morning Cardio"
        assert workout.notes == "Light jogging"
        assert workout.created_at is not None

    async def test_workout_notes_optional(self, db_session_for_app: AsyncSession):
        """Workout notes field is nullable."""
        workout = Workout(user_id=1, name="No Notes Workout")
        db_session_for_app.add(workout)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(workout)

        assert workout.notes is None


class TestExerciseModel:
    async def test_create_exercise(self, db_session_for_app: AsyncSession):
        """Exercise can be created with optional metadata."""
        exercise = Exercise(
            name="Bench Press",
            muscle_group="Chest",
            equipment="Barbell",
        )
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        assert exercise.id is not None
        assert exercise.name == "Bench Press"
        assert exercise.muscle_group == "Chest"
        assert exercise.equipment == "Barbell"

    async def test_exercise_muscle_group_optional(
        self, db_session_for_app: AsyncSession
    ):
        """muscle_group and equipment are nullable."""
        exercise = Exercise(name="Unknown Lift")
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        assert exercise.muscle_group is None
        assert exercise.equipment is None

    async def test_create_exercise_synonym(
        self, db_session_for_app: AsyncSession
    ):
        """ExerciseSynonym links alternative names to canonical exercise."""
        exercise = Exercise(name="Squat", muscle_group="Legs")
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        synonym = ExerciseSynonym(canonical_id=exercise.id, synonym="BSQ")
        db_session_for_app.add(synonym)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(synonym)

        assert synonym.id is not None
        assert synonym.canonical_id == exercise.id
        assert synonym.synonym == "BSQ"

    async def test_synonym_unique_constraint(
        self, db_session_for_app: AsyncSession
    ):
        """Duplicate synonym values raise an error."""
        exercise = Exercise(name="Deadlift")
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        db_session_for_app.add(ExerciseSynonym(canonical_id=exercise.id, synonym="DL"))
        await db_session_for_app.commit()

        dup = ExerciseSynonym(canonical_id=exercise.id, synonym="DL")
        db_session_for_app.add(dup)
        with pytest.raises(Exception):
            await db_session_for_app.commit()


class TestProgressModel:
    async def test_create_progress_record(
        self, db_session_for_app: AsyncSession
    ):
        """Progress can record weight/reps/sets for an exercise."""
        user = User(email="prog@example.com", username="proguser", hashed_password="x")
        db_session_for_app.add(user)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(user)

        exercise = Exercise(name="Squat")
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        progress = Progress(
            user_id=user.id,
            exercise_id=exercise.id,
            weight_kg=100.0,
            reps=5,
            sets=3,
        )
        db_session_for_app.add(progress)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(progress)

        assert progress.id is not None
        assert progress.weight_kg == 100.0
        assert progress.reps == 5
        assert progress.sets == 3
        assert progress.recorded_at is not None

    async def test_progress_weight_optional(
        self, db_session_for_app: AsyncSession
    ):
        """weight_kg is nullable (bodyweight exercises)."""
        user = User(email="bw@example.com", username="bwuser", hashed_password="x")
        db_session_for_app.add(user)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(user)

        exercise = Exercise(name="Pull-up")
        db_session_for_app.add(exercise)
        await db_session_for_app.commit()
        await db_session_for_app.refresh(exercise)

        progress = Progress(
            user_id=user.id,
            exercise_id=exercise.id,
            reps=10,
            sets=3,
        )
        db_session_for_app.add(progress)
        await db_session_for_app.commit()

        assert progress.weight_kg is None
