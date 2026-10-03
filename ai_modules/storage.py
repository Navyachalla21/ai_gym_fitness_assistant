"""
Lightweight SQLite storage for the AI Gym & Fitness Assistant.

Persists workout sessions, skip-risk checks and gym-buddy chat messages so the
weekly report and the admin analytics dashboard have real history to work with.

SQLite is built into Python (no extra install). The schema is deliberately plain
SQL so it can be moved to PostgreSQL later without redesign.

NOTE: on free hosting (e.g. Render free tier) the disk is reset on every
redeploy/restart, so data is not permanent there. Set GYM_DB_PATH to a
persistent-disk location, or switch to a hosted database, for production.
"""
import os
import random
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gym_data.db")
DB_PATH = os.path.abspath(os.getenv("GYM_DB_PATH", _DEFAULT_PATH))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    reps INTEGER,
    duration_seconds INTEGER,
    form_quality_pct REAL,
    pace_reps_per_min REAL,
    performance_score REAL,
    rating TEXT
);
CREATE TABLE IF NOT EXISTS risk_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    days_since_last_workout INTEGER,
    weekly_avg_sessions REAL,
    avg_session_completion_pct REAL,
    skip_probability REAL,
    risk_level TEXT
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'user' or 'buddy'
    message TEXT NOT NULL,
    sentiment TEXT               -- only set for user messages
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_risk_user_time ON risk_checks(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_user_time ON chat_messages(user_id, created_at);
"""

_ready = False


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect() -> sqlite3.Connection:
    """Open a connection, creating the database/schema on first use.
    Falls back to the system temp dir if the configured location is read-only."""
    global DB_PATH, _ready
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
    except (sqlite3.OperationalError, OSError):
        DB_PATH = os.path.join(tempfile.gettempdir(), "gym_data.db")
        conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    if not _ready:
        conn.executescript(_SCHEMA)
        conn.commit()
        _ready = True
    return conn


def _insert(sql: str, params: tuple) -> bool:
    """Insert a row. Storage must never break the main feature, so errors are swallowed."""
    try:
        with closing(_connect()) as conn:
            conn.execute(sql, params)
            conn.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[storage] write failed: {exc}")
        return False


# ---------------------------------------------------------------- writes
def log_session(result: dict, user_id: str = "default", created_at: str | None = None) -> bool:
    return _insert(
        "INSERT INTO sessions (user_id, created_at, reps, duration_seconds, form_quality_pct,"
        " pace_reps_per_min, performance_score, rating) VALUES (?,?,?,?,?,?,?,?)",
        (user_id, created_at or _now(), result.get("reps"), result.get("duration_seconds"),
         result.get("form_quality_pct"), result.get("pace_reps_per_min"),
         result.get("performance_score"), result.get("rating")),
    )


def log_risk(inputs: dict, result: dict, user_id: str = "default", created_at: str | None = None) -> bool:
    return _insert(
        "INSERT INTO risk_checks (user_id, created_at, days_since_last_workout, weekly_avg_sessions,"
        " avg_session_completion_pct, skip_probability, risk_level) VALUES (?,?,?,?,?,?,?)",
        (user_id, created_at or _now(), inputs.get("days_since_last_workout"),
         inputs.get("weekly_avg_sessions"), inputs.get("avg_session_completion_pct"),
         result.get("skip_probability"), result.get("risk_level")),
    )


def log_chat(role: str, message: str, sentiment: str | None = None,
             user_id: str = "default", created_at: str | None = None) -> bool:
    return _insert(
        "INSERT INTO chat_messages (user_id, created_at, role, message, sentiment) VALUES (?,?,?,?,?)",
        (user_id, created_at or _now(), role, message, sentiment),
    )


# ----------------------------------------------------------------- reads
def _fetch(table: str, user_id: str, days: int | None, limit: int | None) -> list:
    """Return rows oldest-first. `limit` keeps the most recent N rows."""
    sql = f"SELECT * FROM {table} WHERE user_id = ?"  # table name is internal, never user input
    params: list = [user_id]
    if days is not None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()
        sql += " AND created_at >= ?"
        params.append(cutoff)
    sql += " ORDER BY created_at DESC, id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))
    try:
        with closing(_connect()) as conn:
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception as exc:  # noqa: BLE001
        print(f"[storage] read failed: {exc}")
        return []
    return list(reversed(rows))


def get_sessions(user_id: str = "default", days: int | None = None, limit: int | None = None) -> list:
    return _fetch("sessions", user_id, days, limit)


def get_risks(user_id: str = "default", days: int | None = None, limit: int | None = None) -> list:
    return _fetch("risk_checks", user_id, days, limit)


def get_chats(user_id: str = "default", days: int | None = None, limit: int | None = None) -> list:
    return _fetch("chat_messages", user_id, days, limit)


def list_users() -> list:
    try:
        with closing(_connect()) as conn:
            q = ("SELECT user_id FROM sessions UNION SELECT user_id FROM risk_checks "
                 "UNION SELECT user_id FROM chat_messages ORDER BY user_id")
            return [r[0] for r in conn.execute(q).fetchall()]
    except Exception as exc:  # noqa: BLE001
        print(f"[storage] list_users failed: {exc}")
        return []


# ------------------------------------------------------------ demo data
def seed_demo_data(user_id: str = "demo", days: int = 14) -> dict:
    """Fill the database with clearly-labelled DEMO history (stored under user_id 'demo')
    so the analytics dashboard can be shown even when the real history is empty.
    Re-running replaces the previous demo rows."""
    rng = random.Random(7)  # fixed seed -> same demo data every time
    try:
        with closing(_connect()) as conn:
            for table in ("sessions", "risk_checks", "chat_messages"):
                conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"[storage] seed cleanup failed: {exc}")

    now = datetime.now(timezone.utc)
    sessions = risks = chats = 0
    for d in range(days, 0, -1):
        when = (now - timedelta(days=d)).replace(microsecond=0)
        if rng.random() < 0.7:  # trains on ~70% of days
            progress = (days - d) / days            # gradual improvement over time
            form = round(min(98, 55 + progress * 30 + rng.uniform(-6, 6)), 1)
            duration = rng.randint(90, 240)
            reps = rng.randint(8, 18)
            pace = round(reps / max(duration / 60, 0.1), 1)
            score = round(form * 0.6 + min(pace / 15, 1) * 100 * 0.4, 1)
            rating = "Excellent" if score >= 80 else "Good" if score >= 60 else "Needs Improvement"
            if log_session({"reps": reps, "duration_seconds": duration, "form_quality_pct": form,
                            "pace_reps_per_min": pace, "performance_score": score, "rating": rating},
                           user_id, when.isoformat()):
                sessions += 1
        if d % 2 == 0:
            days_since = rng.randint(0, 9)
            prob = round(min(0.99, max(0.01, days_since / 10 + rng.uniform(-0.15, 0.15))), 2)
            level = "High" if prob > 0.6 else "Medium" if prob > 0.3 else "Low"
            if log_risk({"days_since_last_workout": days_since, "weekly_avg_sessions": 3.5,
                         "avg_session_completion_pct": 80}, {"skip_probability": prob, "risk_level": level},
                        user_id, when.isoformat()):
                risks += 1
        if d % 3 == 0:
            sentiment = rng.choice(["positive", "positive", "neutral", "negative"])
            if log_chat("user", f"(demo message, {sentiment})", sentiment, user_id, when.isoformat()):
                chats += 1
    return {"user_id": user_id, "sessions": sessions, "risk_checks": risks, "chat_messages": chats}
