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


class TestExerciseSynonymEndpoints:
    """Tests for POST/DELETE /exercises/{id}/synonyms endpoints."""

    async def test_add_synonym_creates_row(self, client: AsyncClient):
        """POST /exercises/{id}/synonyms returns 201 and the created row."""
        # Create an exercise first
        ex = await client.post("/exercises/", json={"name": "Bench Press"})
        exercise_id = ex.json()["id"]

        response = await client.post(
            f"/exercises/{exercise_id}/synonyms",
            json={"synonym": "press de banca"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == exercise_id
        assert data["synonym"] == "press de banca"
        assert "id" in data

    async def test_add_synonym_nonexistent_exercise_returns_404(self, client: AsyncClient):
        """POST /exercises/{id}/synonyms returns 404 when exercise does not exist."""
        response = await client.post(
            "/exercises/9999/synonyms",
            json={"synonym": "some synonym"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_add_synonym_duplicate_returns_409(self, client: AsyncClient):
        """POST /exercises/{id}/synonyms returns 409 when duplicate (exercise_id, synonym)."""
        ex = await client.post("/exercises/", json={"name": "Squat"})
        exercise_id = ex.json()["id"]

        await client.post(
            f"/exercises/{exercise_id}/synonyms",
            json={"synonym": "sentadilla"},
        )
        response = await client.post(
            f"/exercises/{exercise_id}/synonyms",
            json={"synonym": "sentadilla"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_delete_synonym_returns_204(self, client: AsyncClient):
        """DELETE /exercises/{id}/synonyms/{synonym_id} returns 204 on success."""
        ex = await client.post("/exercises/", json={"name": "Deadlift"})
        exercise_id = ex.json()["id"]

        create_resp = await client.post(
            f"/exercises/{exercise_id}/synonyms",
            json={"synonym": "peso muerto"},
        )
        synonym_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/exercises/{exercise_id}/synonyms/{synonym_id}"
        )
        assert del_resp.status_code == 204

    async def test_delete_synonym_wrong_exercise_returns_404(self, client: AsyncClient):
        """DELETE /exercises/{id}/synonyms/{synonym_id} returns 404 when exercise_id does not match."""
        ex1 = await client.post("/exercises/", json={"name": "Rowing"})
        ex2 = await client.post("/exercises/", json={"name": "Pull-up"})
        exercise_id_1 = ex1.json()["id"]
        exercise_id_2 = ex2.json()["id"]

        # Create synonym on ex1
        create_resp = await client.post(
            f"/exercises/{exercise_id_1}/synonyms",
            json={"synonym": "remo"},
        )
        synonym_id = create_resp.json()["id"]

        # Try to delete with ex2's exercise_id — should 404
        response = await client.delete(
            f"/exercises/{exercise_id_2}/synonyms/{synonym_id}"
        )
        assert response.status_code == 404

    async def test_delete_synonym_nonexistent_returns_404(self, client: AsyncClient):
        """DELETE /exercises/{id}/synonyms/{synonym_id} returns 404 when synonym does not exist."""
        ex = await client.post("/exercises/", json={"name": "Curl"})
        exercise_id = ex.json()["id"]

        response = await client.delete(
            f"/exercises/{exercise_id}/synonyms/9999"
        )
        assert response.status_code == 404


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


class TestWorkoutSetNormalization:
    """Integration tests for exercise name normalization in workout set persistence."""

    async def test_exercise_name_resolved_via_synonym(self, client: AsyncClient):
        """Sending exercise_name='press de banca' resolves to Bench Press via synonym."""
        # Create the canonical exercise
        ex = await client.post("/exercises/", json={"name": "Bench Press"})
        bench_id = ex.json()["id"]

        # Add a Spanish synonym
        await client.post(
            f"/exercises/{bench_id}/synonyms",
            json={"synonym": "press de banca"},
        )

        # Create workout and add a set using the Spanish name
        workout = await client.post("/workouts/", json={"name": "Push Day"})
        workout_id = workout.json()["id"]

        response = await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_name": "press de banca", "set_number": 1, "weight_kg": 80.0, "reps": 5},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == bench_id
        assert data["raw_name"] == "press de banca"

    async def test_unknown_exercise_name_preserved_as_raw_name(self, client: AsyncClient):
        """Sending an unrecognized exercise_name stores raw_name and leaves exercise_id null."""
        # Create any exercise so the workout can be created
        ex = await client.post("/exercises/", json={"name": "Squat"})
        _ = ex.json()["id"]

        workout = await client.post("/workouts/", json={"name": "Mix Day"})
        workout_id = workout.json()["id"]

        response = await client.post(
            f"/workouts/{workout_id}/sets",
            json={
                "exercise_name": "some totally unknown exercise xyz",
                "set_number": 1,
                "reps": 10,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] is None
        assert data["raw_name"] == "some totally unknown exercise xyz"

    async def test_exercise_id_still_works_without_exercise_name(self, client: AsyncClient):
        """Providing exercise_id directly (no exercise_name) behaves as before."""
        ex = await client.post("/exercises/", json={"name": "Deadlift"})
        deadlift_id = ex.json()["id"]

        workout = await client.post("/workouts/", json={"name": "Back Day"})
        workout_id = workout.json()["id"]

        response = await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_id": deadlift_id, "set_number": 1, "weight_kg": 120.0, "reps": 3},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == deadlift_id
        assert data["raw_name"] is None

    async def test_exercise_id_and_exercise_name_both_set(self, client: AsyncClient):
        """When both exercise_id and exercise_name are provided, id is used and raw_name stored."""
        ex = await client.post("/exercises/", json={"name": "Overhead Press"})
        ohp_id = ex.json()["id"]

        workout = await client.post("/workouts/", json={"name": "Shoulder Day"})
        workout_id = workout.json()["id"]

        response = await client.post(
            f"/workouts/{workout_id}/sets",
            json={
                "exercise_id": ohp_id,
                "exercise_name": "OHP",
                "set_number": 1,
                "reps": 8,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == ohp_id
        assert data["raw_name"] == "OHP"

    async def test_exercise_name_exact_match_resolved(self, client: AsyncClient):
        """exercise_name matching an existing exercise name is resolved to its id."""
        ex = await client.post("/exercises/", json={"name": "Pull-Up"})
        pullup_id = ex.json()["id"]

        workout = await client.post("/workouts/", json={"name": "Upper Body"})
        workout_id = workout.json()["id"]

        response = await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_name": "Pull-Up", "set_number": 1, "reps": 12},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == pullup_id
        # raw_name is always stored when exercise_name is submitted (preserves user input)
        assert data["raw_name"] == "Pull-Up"

    async def test_workout_set_detail_shows_raw_name(self, client: AsyncClient):
        """GET /workouts/{id} returns raw_name in the set details."""
        ex = await client.post("/exercises/", json={"name": "Squat"})
        _ = ex.json()["id"]

        workout = await client.post("/workouts/", json={"name": "Leg Day"})
        workout_id = workout.json()["id"]

        await client.post(
            f"/workouts/{workout_id}/sets",
            json={
                "exercise_name": "unrecognized move",
                "set_number": 1,
                "reps": 5,
            },
        )

        detail = await client.get(f"/workouts/{workout_id}")
        assert detail.status_code == 200
        sets = detail.json()["sets"]
        assert len(sets) == 1
        assert sets[0]["raw_name"] == "unrecognized move"
        assert sets[0]["exercise_id"] is None


class TestAnalyticsEndpoints:
    async def test_analytics_summary_returns_correct_schema(self, client: AsyncClient):
        """GET /analytics/summary returns correct schema with analytics fields."""
        response = await client.get("/analytics/summary", params={"user_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert "total_workouts" in data
        assert "total_volume" in data
        assert "favorite_exercise" in data
        assert "current_streak" in data


class TestAnalyticsIntegration:
    """Integration tests for /analytics/* endpoints."""

    async def test_analytics_summary_empty_user(self, client: AsyncClient):
        """GET /analytics/summary returns zeros for user with no data."""
        response = await client.get("/analytics/summary", params={"user_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert data["total_workouts"] == 0
        assert data["total_volume"] == 0.0
        assert data["favorite_exercise"] is None
        assert data["current_streak"] == 0

    async def test_analytics_summary_with_data(self, client: AsyncClient):
        """GET /analytics/summary returns correct stats after creating workout data."""
        # Create an exercise
        ex_resp = await client.post("/exercises/", json={"name": "Squat", "muscle_group": "Legs"})
        assert ex_resp.status_code == 200
        exercise_id = ex_resp.json()["id"]

        # Create a workout
        workout_resp = await client.post("/workouts/", json={"name": "Leg Day"})
        assert workout_resp.status_code == 201
        workout_id = workout_resp.json()["id"]

        # Add workout sets
        await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_id": exercise_id, "set_number": 1, "weight_kg": 100.0, "reps": 5},
        )
        await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_id": exercise_id, "set_number": 2, "weight_kg": 100.0, "reps": 5},
        )

        response = await client.get("/analytics/summary", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["total_workouts"] == 1
        assert data["total_volume"] == 1000.0  # 500 + 500
        assert data["favorite_exercise"] == "Squat"
        assert data["current_streak"] >= 1

    async def test_analytics_volume_empty(self, client: AsyncClient):
        """GET /analytics/volume returns empty data for user with no sets."""
        response = await client.get("/analytics/volume", params={"user_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
        assert data["data"] == []

    async def test_analytics_volume_day_period(self, client: AsyncClient):
        """GET /analytics/volume?period=day returns daily volume data."""
        ex_resp = await client.post("/exercises/", json={"name": "Deadlift"})
        exercise_id = ex_resp.json()["id"]
        w_resp = await client.post("/workouts/", json={"name": "Back Day"})
        workout_id = w_resp.json()["id"]

        await client.post(
            f"/workouts/{workout_id}/sets",
            json={"exercise_id": exercise_id, "set_number": 1, "weight_kg": 140.0, "reps": 3},
        )

        response = await client.get("/analytics/volume", params={"user_id": 1, "period": "day"})
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "day"
        assert len(data["data"]) >= 1
        assert data["data"][0]["volume"] == 420.0  # 140 * 3

    async def test_analytics_volume_invalid_period(self, client: AsyncClient):
        """GET /analytics/volume with invalid period returns 422."""
        response = await client.get("/analytics/volume", params={"period": "month"})
        assert response.status_code == 422

    async def test_analytics_progress_empty(self, client: AsyncClient):
        """GET /analytics/progress returns empty exercises for user with no data."""
        response = await client.get("/analytics/progress", params={"user_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert data["exercises"] == []

    async def test_analytics_progress_with_sets(self, client: AsyncClient):
        """GET /analytics/progress returns per-exercise progress data."""
        ex_resp = await client.post("/exercises/", json={"name": "Bench Press"})
        exercise_id = ex_resp.json()["id"]

        w1_resp = await client.post("/workouts/", json={"name": "Push A"})
        w1_id = w1_resp.json()["id"]
        w2_resp = await client.post("/workouts/", json={"name": "Push B"})
        w2_id = w2_resp.json()["id"]

        await client.post(
            f"/workouts/{w1_id}/sets",
            json={"exercise_id": exercise_id, "set_number": 1, "weight_kg": 80.0, "reps": 8},
        )
        await client.post(
            f"/workouts/{w2_id}/sets",
            json={"exercise_id": exercise_id, "set_number": 1, "weight_kg": 85.0, "reps": 8},
        )

        response = await client.get("/analytics/progress", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data["exercises"]) == 1
        assert data["exercises"][0]["exercise_name"] == "Bench Press"
        assert len(data["exercises"][0]["data"]) >= 1
