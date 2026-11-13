"""User profile (basic details) stored next to the accounts in users.db."""
import sqlite3
from contextlib import closing

try:
    from ai_modules import auth
except ImportError:  # pragma: no cover
    import auth

FIELDS = ("full_name", "age", "gender", "height_cm", "weight_kg", "goal",
          "fitness_level", "workouts_per_week", "diet_pref", "injuries")


def _conn():
    conn = sqlite3.connect(auth._PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY, full_name TEXT, age INTEGER, gender TEXT,
        height_cm REAL, weight_kg REAL, goal TEXT, fitness_level TEXT,
        workouts_per_week INTEGER, diet_pref TEXT, injuries TEXT, updated_at TEXT)""")
    return conn


def member_id(username: str) -> str:
    """Permanent-looking user ID such as GYM00007 (from the account's row number)."""
    with closing(auth._conn()) as conn:
        row = conn.execute("SELECT rowid FROM users WHERE username = ?", (username,)).fetchone()
    return f"GYM{(row[0] if row else 0):05d}"


def get_profile(username: str):
    with closing(_conn()) as conn:
        row = conn.execute("SELECT * FROM profiles WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def save_profile(username: str, data: dict) -> dict:
    values = [data.get(f) for f in FIELDS]
    with closing(_conn()) as conn:
        conn.execute(f"""INSERT INTO profiles (username, {', '.join(FIELDS)}, updated_at)
            VALUES (?, {', '.join('?' for _ in FIELDS)}, datetime('now'))
            ON CONFLICT(username) DO UPDATE SET
            {', '.join(f'{f}=excluded.{f}' for f in FIELDS)}, updated_at=datetime('now')""",
                     [username] + values)
        conn.commit()
    return get_profile(username)


def delete_profile(username: str):
    with closing(_conn()) as conn:
        conn.execute("DELETE FROM profiles WHERE username = ?", (username,))
        conn.commit()
