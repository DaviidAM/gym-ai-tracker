"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient


class TestRootEndpoints:
    async def test_root_returns_gymai_message(self, client: AsyncClient):
        """GET / returns status and message."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "GymAI Tracker API"
        assert data["status"] == "running"

    async def test_health_returns_ok(self, client: AsyncClient):
        """GET /health returns ok status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthEndpoints:
    async def test_register_creates_user(self, client: AsyncClient):
        """POST /auth/register creates a new user and returns UserOut."""
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email_fails(self, client: AsyncClient):
        """Registering same email twice returns 400."""
        payload = {
            "email": "dup@example.com",
            "username": "user1",
            "password": "pass123",
        }
        r1 = await client.post("/auth/register", json=payload)
        assert r1.status_code == 200

        payload["username"] = "user2"
        r2 = await client.post("/auth/register", json=payload)
        assert r2.status_code == 400
        assert "already registered" in r2.json()["detail"]

    async def test_register_duplicate_username_fails(self, client: AsyncClient):
        """Registering same username twice returns 400."""
        payload = {
            "email": "user@example.com",
            "username": "dupname",
            "password": "pass123",
        }
        r1 = await client.post("/auth/register", json=payload)
        assert r1.status_code == 200

        payload["email"] = "other@example.com"
        r2 = await client.post("/auth/register", json=payload)
        assert r2.status_code == 400

    @pytest.mark.parametrize(
        "invalid_payload,missing_field",
        [
            ({"username": "user", "password": "pass"}, "email"),
            ({"email": "a@b.com", "password": "pass"}, "username"),
            ({"email": "a@b.com", "username": "user"}, "password"),
        ],
    )
    async def test_register_missing_field_fails(
        self, client: AsyncClient, invalid_payload: dict, missing_field: str
    ):
        """Registering with a missing field returns 422."""
        response = await client.post("/auth/register", json=invalid_payload)
        assert response.status_code == 422

    async def test_register_invalid_email_fails(self, client: AsyncClient):
        """Registering with invalid email format returns 422."""
        payload = {
            "email": "not-an-email",
            "username": "user",
            "password": "pass123",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422


class TestExerciseEndpoints:
    async def test_list_exercises_empty(self, client: AsyncClient):
        """GET /exercises/ returns empty list when no exercises exist."""
        response = await client.get("/exercises/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_and_list_exercise(self, client: AsyncClient):
        """POST /exercises/ creates an exercise; GET /exercises/ returns it."""
        exercise_payload = {
            "name": "Bench Press",
            "muscle_group": "Chest",
            "equipment": "Barbell",
        }
        create_response = await client.post("/exercises/", json=exercise_payload)
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["name"] == "Bench Press"
        assert created["muscle_group"] == "Chest"
        assert created["id"] is not None

        list_response = await client.get("/exercises/")
        assert list_response.status_code == 200
        exercises = list_response.json()
        assert len(exercises) == 1
        assert exercises[0]["name"] == "Bench Press"

    async def test_create_exercise_minimal(self, client: AsyncClient):
        """Exercise can be created with only a name."""
        payload = {"name": "Push-up"}
        response = await client.post("/exercises/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Push-up"
        assert data["muscle_group"] is None
        assert data["equipment"] is None


class TestWorkoutEndpoints:
    async def test_list_workouts_empty(self, client: AsyncClient):
        """GET /workouts/ returns empty list when no workouts exist."""
        response = await client.get("/workouts/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_workout(self, client: AsyncClient):
        """POST /workouts/ creates a workout and returns WorkoutOut."""
        payload = {
            "name": "Leg Day",
            "notes": "Focus on squats",
        }
        response = await client.post("/workouts/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Leg Day"
        assert data["notes"] == "Focus on squats"
        assert data["id"] is not None

    async def test_list_workouts_after_creation(self, client: AsyncClient):
        """GET /workouts/ returns the created workout."""
        await client.post("/workouts/", json={"name": "Cardio"})
        response = await client.get("/workouts/")
        assert response.status_code == 200
        workouts = response.json()
        assert len(workouts) >= 1
        assert any(w["name"] == "Cardio" for w in workouts)


class TestAnalyticsEndpoints:
    async def test_get_summary_returns_placeholder(self, client: AsyncClient):
        """GET /analytics/summary returns the analytics placeholder response."""
        response = await client.get("/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "user_id" in data
        assert data["user_id"] == 1  # default user_id param
