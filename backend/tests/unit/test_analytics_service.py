"""Unit tests for analytics aggregation functions."""
import pytest
from datetime import datetime
from app.services.analytics_service import (
    compute_volume_series,
    compute_progress_series,
)


class TestComputeVolumeSeries:
    def test_empty_input_returns_empty(self):
        result = compute_volume_series([], [], [], [], [], period="week")
        assert result == []

    def test_single_set_volume(self):
        result = compute_volume_series(
            workout_ids=[1],
            exercise_ids=[1],
            dates=[datetime(2026, 8, 1)],
            weights=[100.0],
            reps=[5],
            period="day",
        )
        assert len(result) == 1
        assert result[0]["volume"] == 500.0
        assert result[0]["date"] == "2026-08-01"

    def test_multiple_sets_same_day_accumulates(self):
        result = compute_volume_series(
            workout_ids=[1, 1],
            exercise_ids=[1, 2],
            dates=[datetime(2026, 8, 1), datetime(2026, 8, 1)],
            weights=[100.0, 50.0],
            reps=[5, 10],
            period="day",
        )
        assert len(result) == 1
        assert result[0]["volume"] == 1000.0  # 500 + 500

    def test_weekly_aggregation(self):
        # Two workouts in the same ISO week (Mon-Sun)
        result = compute_volume_series(
            workout_ids=[1, 2],
            exercise_ids=[1, 1],
            dates=[
                datetime(2026, 8, 3),  # Monday
                datetime(2026, 8, 5),  # Wednesday
            ],
            weights=[100.0, 80.0],
            reps=[5, 3],
            period="week",
        )
        assert len(result) == 1
        assert result[0]["volume"] == 740.0  # 500 + 240

    def test_volume_rounds_to_two_decimals(self):
        result = compute_volume_series(
            workout_ids=[1],
            exercise_ids=[1],
            dates=[datetime(2026, 8, 1)],
            weights=[33.33],
            reps=[3],
            period="day",
        )
        assert result[0]["volume"] == 99.99

    def test_none_weight_and_reps_treated_as_zero(self):
        result = compute_volume_series(
            workout_ids=[1],
            exercise_ids=[1],
            dates=[datetime(2026, 8, 1)],
            weights=[None],
            reps=[5],
            period="day",
        )
        assert result[0]["volume"] == 0.0


class TestComputeProgressSeries:
    def test_empty_input_returns_empty(self):
        result = compute_progress_series([], [], [], [], [])
        assert result == []

    def test_single_exercise_single_session(self):
        result = compute_progress_series(
            exercise_ids=[1],
            exercise_names=["Bench Press"],
            dates=[datetime(2026, 8, 1)],
            weights=[100.0],
            reps=[5],
        )
        assert len(result) == 1
        assert result[0]["exercise_id"] == 1
        assert result[0]["exercise_name"] == "Bench Press"
        assert len(result[0]["data"]) == 1
        assert result[0]["data"][0]["weight_kg"] == 100.0
        assert result[0]["data"][0]["reps"] == 5
        assert result[0]["data"][0]["date"] == "2026-08-01"

    def test_multiple_sessions_same_day_takes_max_weight_and_sum_reps(self):
        result = compute_progress_series(
            exercise_ids=[1, 1],
            exercise_names=["Bench Press", "Bench Press"],
            dates=[datetime(2026, 8, 1), datetime(2026, 8, 1)],
            weights=[80.0, 100.0],
            reps=[5, 3],
        )
        assert len(result) == 1
        assert result[0]["data"][0]["weight_kg"] == 100.0
        assert result[0]["data"][0]["reps"] == 8

    def test_multiple_exercises_separate_results(self):
        result = compute_progress_series(
            exercise_ids=[1, 2],
            exercise_names=["Bench Press", "Squat"],
            dates=[datetime(2026, 8, 1), datetime(2026, 8, 1)],
            weights=[100.0, 150.0],
            reps=[5, 5],
        )
        assert len(result) == 2
        ex_names = {r["exercise_name"] for r in result}
        assert ex_names == {"Bench Press", "Squat"}

    def test_data_ordered_by_date(self):
        result = compute_progress_series(
            exercise_ids=[1, 1],
            exercise_names=["Squat", "Squat"],
            dates=[datetime(2026, 8, 3), datetime(2026, 8, 1)],
            weights=[120.0, 100.0],
            reps=[5, 5],
        )
        dates_order = [d["date"] for d in result[0]["data"]]
        assert dates_order == ["2026-08-01", "2026-08-03"]
