"""Exercise name normalization service.

Normalizes free-text exercise names to canonical exercise IDs using:
 1. Exact match against exercises.name
 2. Case-insensitive match against exercise_synonyms.synonym
 3. Fuzzy match (difflib.SequenceMatcher, or rapidfuzz if available)
    across exercises.name and all synonyms; threshold default 0.85.

The core ``normalize`` function is a pure callable — no FastAPI or SQLAlchemy
coupling.  A caller (e.g. a FastAPI dependency) injects the lookup logic
via the ``lookup`` parameter.
"""

from __future__ import annotations

import difflib
from typing import Callable, NamedTuple, Sequence

try:
    from rapidfuzz import fuzz as _rfuzz

    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover
    _rfuzz = None  # type: ignore[assignment]
    _HAS_RAPIDFUZZ = False


class LookupResult(NamedTuple):
    """Return type for the injected lookup callable."""
    exercises: Sequence[tuple[int, str]]
    synonyms: Sequence[tuple[int, str]]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize(
    name: str,
    *,
    lookup: Callable[[], LookupResult] | None = None,
    threshold: float = 0.85,
    use_rapidfuzz: bool | None = None,
) -> int | None:
    """
    Return the canonical ``exercise_id`` for ``name``, or ``None`` if no
    confident match exists.

    Parameters
    ----------
    name:
        Free-text exercise name supplied by the user.
    lookup:
        Callable returning ``(exercises, synonyms)`` where each is a
        sequence of ``(exercise_id, str)``.
        If omitted, the function returns ``None`` immediately (stateless
        mode for stand-alone unit testing).
    threshold:
        Minimum fuzzy score (0.0–1.0) required to accept a candidate.
        Defaults to 0.85.
    use_rapidfuzz:
        ``True`` → always use rapidfuzz (raises ``ImportError`` if not installed).
        ``False`` → always use ``difflib.SequenceMatcher``.
        ``None`` (default) → use rapidfuzz if installed, fall back to difflib.

    Strategy
    --------
    1. Exact match on ``exercises.name``.
    2. Case-insensitive exact match on ``exercise_synonyms.synonym``.
    3. Fuzzy match across every ``exercises.name`` and every synonym; the
       highest-scoring candidate above ``threshold`` wins.
    """
    if not name or not name.strip():
        return None

    name_stripped = name.strip()

    # ── No lookup supplied (testing / stateless mode) ──────────────────────
    if lookup is None:
        return None

    exercises, synonyms = lookup()

    # ── Step 1: exact match on exercise names ──────────────────────────────
    for ex_id, ex_name in exercises:
        if ex_name == name_stripped:
            return ex_id

    # ── Step 2: case-insensitive match on synonyms ─────────────────────────
    name_lower = name_stripped.lower()
    for syn_ex_id, synonym in synonyms:
        if synonym.lower() == name_lower:
            return syn_ex_id

    # ── Step 3: fuzzy match ────────────────────────────────────────────────
    scorer = _fuzzy_scorer(use_rapidfuzz)
    best_score = -1.0
    best_id: int | None = None

    for ex_id, ex_name in exercises:
        score = scorer(name_stripped, ex_name)
        if score > best_score:
            best_score = score
            best_id = ex_id

    for syn_ex_id, synonym in synonyms:
        score = scorer(name_stripped, synonym)
        if score > best_score:
            best_score = score
            best_id = syn_ex_id

    if best_score >= threshold:
        return best_id

    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fuzzy_scorer(use_rapidfuzz: bool | None) -> Callable[[str, str], float]:
    """
    Return a (name1, name2) → float scorer.
    The returned score is always in [0.0, 1.0].
    """
    if use_rapidfuzz is True and not _HAS_RAPIDFUZZ:
        raise ImportError("rapidfuzz is not installed")

    if use_rapidfuzz is False:
        return _difflib_scorer

    if _HAS_RAPIDFUZZ and use_rapidfuzz is not False:
        # Default / True: use rapidfuzz when available
        return _rapidfuzz_scorer

    return _difflib_scorer


def _difflib_scorer(a: str, b: str) -> float:
    """Return a SequenceMatcher similarity ratio in [0, 1]."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def _rapidfuzz_scorer(a: str, b: str) -> float:
    """Return a rapidfuzz token_sort_ratio in [0, 100]; we normalise to 0-1."""
    # ratio returns 0-100; _rfuzz is guaranteed non-None when this is called
    assert _rfuzz is not None
    return _rfuzz.ratio(a, b) / 100.0
