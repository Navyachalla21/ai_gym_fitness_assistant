"""Accounts and login tokens (Step 1). Passwords are stored only as bcrypt hashes."""
import os
import re
import secrets
import sqlite3
import tempfile
import time

import bcrypt
import jwt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_DAYS = 30
RESERVED = {"default", "demo", "admin"}
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")

# Set JWT_SECRET in Render's Environment tab. Without it, a random key is made at every start,
# which logs everybody out whenever the server restarts.
_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)


def _db_path() -> str:
    custom = os.getenv("AUTH_DB_PATH")
    if custom:
        return custom
    for folder in (os.path.join(_ROOT, "data"), tempfile.gettempdir()):
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "users.db")
            sqlite3.connect(path).close()
            return path
        except Exception:  # noqa: BLE001
            continue
    return ":memory:"


_PATH = _db_path()


def _conn():
    conn = sqlite3.connect(_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        display_name TEXT,
        created_at TEXT NOT NULL)""")
    return conn


def clean_username(name: str) -> str:
    name = (name or "").strip().lower()
    if not USERNAME_RE.match(name):
        raise ValueError("Username must be 3-30 characters: letters, numbers or underscore.")
    if name in RESERVED:
        raise ValueError("That username is reserved. Please choose another.")
    return name


def create_user(username: str, password: str, display_name: str = "") -> dict:
    username = clean_username(username)
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if len(password.encode()) > 72:
        raise ValueError("Password is too long (max 72 characters).")
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with _conn() as conn:
        try:
            conn.execute("INSERT INTO users VALUES (?,?,?,datetime('now'))",
                         (username, pw_hash, (display_name or username).strip()[:60]))
        except sqlite3.IntegrityError:
            raise ValueError("That username is already taken.") from None
    return {"username": username, "display_name": (display_name or username).strip()[:60]}


def verify_user(username: str, password: str):
    username = (username or "").strip().lower()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if row is None or len(password.encode()) > 72:
        return None
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return None
    return {"username": row["username"], "display_name": row["display_name"]}


def get_user(username: str):
    with _conn() as conn:
        row = conn.execute("SELECT username, display_name, created_at FROM users WHERE username=?",
                           (username,)).fetchone()
    return dict(row) if row else None


def make_token(username: str) -> str:
    now = int(time.time())
    return jwt.encode({"sub": username, "iat": now, "exp": now + TOKEN_DAYS * 86400}, _SECRET, algorithm="HS256")


def read_token(token: str):
    """Returns the username if the token is valid and the account still exists, else None."""
    try:
        username = jwt.decode(token, _SECRET, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        return None
    return username if username and get_user(username) else None