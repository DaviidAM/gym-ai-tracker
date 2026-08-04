"""Unit tests for exercise_normalizer."""

import pytest

from app.services.exercise_normalizer import (
    LookupResult,
    normalize,
    _difflib_scorer,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_lookup(exercises, synonyms):
    """Return a lookup callable from raw (id, name) pairs."""
    def _lookup() -> LookupResult:
        return (
            [(ex["id"], ex["name"]) for ex in exercises],  # type: ignore[index]
            [(syn["ex_id"], syn["synonym"]) for syn in synonyms],  # type: ignore[index]
        )
    return _lookup


# ---------------------------------------------------------------------------
# Step 1 — exact match
# ---------------------------------------------------------------------------

def test_exact_match_returns_id():
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Bench Press"}],
        synonyms=[],
    )
    assert normalize("Bench Press", lookup=lookup) == 1


def test_exact_match_no_match():
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Bench Press"}],
        synonyms=[],
    )
    assert normalize("Squat", lookup=lookup) is None


# ---------------------------------------------------------------------------
# Step 2 — case-insensitive synonym
# ---------------------------------------------------------------------------

def test_synonym_case_insensitive_match():
    lookup = make_lookup(
        exercises=[{"id": 2, "name": "Deadlift"}],
        synonyms=[{"ex_id": 2, "synonym": "conventional deadlift"}],
    )
    # different case
    assert normalize("Conventional Deadlift", lookup=lookup) == 2


def test_synonym_exact_match():
    lookup = make_lookup(
        exercises=[{"id": 3, "name": "Overhead Press"}],
        synonyms=[{"ex_id": 3, "synonym": "OHP"}],
    )
    assert normalize("OHP", lookup=lookup) == 3


def test_synonym_no_match_falls_to_fuzzy():
    lookup = make_lookup(
        exercises=[{"id": 4, "name": "Pull-Up"}],
        synonyms=[{"ex_id": 4, "synonym": "Chin-Up"}],
    )
    # 'pullup' (0.615) doesn't exact or case-insensitively match anything.
    # With threshold=0.6 it passes; with default 0.85 it should return None.
    assert normalize("pullup", lookup=lookup, threshold=0.6) == 4
    assert normalize("pullup", lookup=lookup) is None


# ---------------------------------------------------------------------------
# Step 3 — fuzzy match
# ---------------------------------------------------------------------------

def test_fuzzy_match_above_threshold():
    lookup = make_lookup(
        exercises=[{"id": 5, "name": "Barbell Row"}],
        synonyms=[{"ex_id": 5, "synonym": "BB Row"}],
    )
    # small typo
    result = normalize("Barbel Row", lookup=lookup)
    assert result == 5


def test_fuzzy_match_returns_best_candidate():
    lookup = make_lookup(
        exercises=[
            {"id": 10, "name": "Leg Press"},
            {"id": 11, "name": "Leg Curl"},
        ],
        synonyms=[],
    )
    # closer to "Leg Press"
    result = normalize("Leg Pres", lookup=lookup)
    assert result == 10


def test_fuzzy_match_below_threshold_returns_none():
    lookup = make_lookup(
        exercises=[{"id": 20, "name": "Bench Press"}],
        synonyms=[],
    )
    # "bench" is too different from "Bench Press"
    result = normalize("bench", lookup=lookup, threshold=0.85)
    assert result is None


def test_fuzzy_match_threshold_configurable():
    lookup = make_lookup(
        exercises=[{"id": 30, "name": "Dumbbell Fly"}],
        synonyms=[],
    )
    # 'Dumbbel Fly' vs 'Dumbbell Fly' = 0.957 → passes at 0.9, fails at 1.0
    assert normalize("Dumbbel Fly", lookup=lookup, threshold=0.9) == 30
    assert normalize("Dumbbel Fly", lookup=lookup, threshold=1.0) is None


# ---------------------------------------------------------------------------
# Priority: exact > synonym > fuzzy
# ---------------------------------------------------------------------------

def test_exact_over_synonym():
    """If a name is both an exact exercise name AND a synonym for another,
    exact-match exercise_id wins (step 1 runs before step 2)."""
    lookup = make_lookup(
        exercises=[{"id": 100, "name": "Incline Press"}],
        synonyms=[{"ex_id": 200, "synonym": "Incline Press"}],
    )
    result = normalize("Incline Press", lookup=lookup)
    assert result == 100  # exact match on exercise.name wins


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_string_returns_none():
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Bench Press"}],
        synonyms=[],
    )
    assert normalize("", lookup=lookup) is None


def test_whitespace_only_returns_none():
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Bench Press"}],
        synonyms=[],
    )
    assert normalize("   ", lookup=lookup) is None


def test_no_lookup_returns_none():
    """Without a lookup callable, normalize is stateless and always None."""
    assert normalize("anything") is None
    assert normalize("Bench Press") is None


def test_name_stripped_before_matching():
    lookup = make_lookup(
        exercises=[{"id": 7, "name": "Push-Up"}],
        synonyms=[],
    )
    assert normalize("  Push-Up  ", lookup=lookup) == 7


def test_multiple_synonyms_best_score_wins():
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Squat"}],
        synonyms=[
            {"ex_id": 1, "synonym": "Air Squat"},
            {"ex_id": 2, "synonym": "Front Squat"},
        ],
    )
    # 'fron squat' vs 'Front Squat' = 0.762, vs 'Air Squat' = 0.632.
    # Both below 0.85; use threshold 0.7 to let Front Squat win.
    assert normalize("fron squat", lookup=lookup, threshold=0.7) == 2


# ---------------------------------------------------------------------------
# use_rapidfuzz flag
# ---------------------------------------------------------------------------

def test_use_rapidfuzz_false_uses_difflib():
    """When use_rapidfuzz=False, scorer must not raise even if rapidfuzz
    is installed; it uses difflib (ratio ~0.73 for these strings)."""
    lookup = make_lookup(
        exercises=[{"id": 1, "name": "Bench Press"}],
        synonyms=[],
    )
    # difflib score for "Bench Press" vs "Bench Pres" is below 0.85
    result = normalize("Bench Pres", lookup=lookup, use_rapidfuzz=False, threshold=0.7)
    assert result == 1


def test_difflib_scorer_range():
    """difflib SequenceMatcher.ratio() is in [0, 1]."""
    assert _difflib_scorer("abc", "abc") == 1.0
    assert _difflib_scorer("abc", "xyz") == 0.0
    assert 0.0 <= _difflib_scorer("Bench Press", "Bench Pres") <= 1.0
