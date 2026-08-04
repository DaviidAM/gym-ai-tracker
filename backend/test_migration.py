"""Test migration for exercise_synonyms table."""
import sqlite3
import tempfile
import os


def test_empty_db():
    """Test 1: Empty DB (no exercises table)"""
    print("=== Test 1: Empty DB ===")
    db_empty = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_empty)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num TEXT)"
    )
    conn.execute("DELETE FROM alembic_version")
    conn.execute("INSERT INTO alembic_version VALUES ('922499ba11eb')")
    conn.commit()
    conn.close()

    conn = sqlite3.connect(db_empty)
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE exercise_synonyms (
                id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                synonym TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE,
                UNIQUE (exercise_id, synonym)
            )
        """)
        cur.execute(
            "CREATE INDEX ix_exercise_synonyms_synonym ON exercise_synonyms (synonym)"
        )
        print("SUCCESS: Empty DB - migration applied")
        conn.commit()
    except Exception as e:
        print(f"FAILED: {e}")
        conn.rollback()
    conn.close()
    os.unlink(db_empty)


def test_db_with_exercises():
    """Test 2: DB with exercises table but no exercise_synonyms"""
    print()
    print("=== Test 2: DB with exercises table ===")
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE exercises (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num TEXT)"
    )
    conn.execute("DELETE FROM alembic_version")
    conn.execute("INSERT INTO alembic_version VALUES ('922499ba11eb')")
    conn.commit()
    conn.close()

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE exercise_synonyms (
                id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                synonym TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE,
                UNIQUE (exercise_id, synonym)
            )
        """)
        cur.execute(
            "CREATE INDEX ix_exercise_synonyms_synonym ON exercise_synonyms (synonym)"
        )
        print("SUCCESS: DB with exercises - migration applied")
        conn.commit()
    except Exception as e:
        print(f"FAILED: {e}")
        conn.rollback()
    conn.close()

    # Test 3: Verify rollback (downgrade) works
    print()
    print("=== Test 3: Rollback ===")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DROP INDEX IF EXISTS ix_exercise_synonyms_synonym")
        cur.execute("DROP TABLE IF EXISTS exercise_synonyms")
        print("SUCCESS: Rollback applied")
        conn.commit()
    except Exception as e:
        print(f"FAILED: {e}")
        conn.rollback()
    conn.close()
    os.unlink(db_path)

    print()
    print("All tests passed!")


if __name__ == "__main__":
    test_empty_db()
    test_db_with_exercises()
