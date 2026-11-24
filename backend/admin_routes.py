"""Admin-only routes: see every user's performance and delete user data.

THE ADMIN LOGIN IS IN A FILE: create  admin_credentials.txt  in the project root folder with two lines
    username=your_admin_name
    password=your_admin_password
That file is listed in .gitignore, so it is never pushed to GitHub. On Render (where the file does not
exist) set the same two values as environment variables ADMIN_USERNAME and ADMIN_PASSWORD.
"""
import hmac
import os
import sys
import time
from contextlib import closing

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

_ADMIN_SUBJECT = "@@admin@@"          # token owner; cannot clash with a normal username

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import auth, storage  # noqa: E402

router = APIRouter(tags=["Admin"])
_bearer = HTTPBearer(auto_error=False)


def _credentials():
    """(username, password) from admin_credentials.txt in the project root, else from environment variables."""
    user = pw = None
    path = os.path.join(_ROOT, "admin_credentials.txt")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                key, sep, val = line.strip().partition("=")
                if sep and key.strip().lower() == "username":
                    user = val.strip()
                elif sep and key.strip().lower() == "password":
                    pw = val.strip()
    except OSError:
        pass
    return user or os.getenv("ADMIN_USERNAME"), pw or os.getenv("ADMIN_PASSWORD")


class AdminLogin(BaseModel):
    username: str = Field(..., max_length=60)
    password: str = Field(..., max_length=100)


@router.post("/api/admin/login")
def admin_login(req: AdminLogin):
    admin_name, admin_pw = _credentials()
    if not admin_name or not admin_pw:
        raise HTTPException(status_code=503, detail="Admin login is not set up. Create admin_credentials.txt.")
    ok_user = hmac.compare_digest(req.username.encode(), admin_name.encode())
    ok_pass = hmac.compare_digest(req.password.encode(), admin_pw.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Wrong admin username or password.")
    token = jwt.encode({"sub": _ADMIN_SUBJECT, "exp": int(time.time()) + 12 * 3600},
                       _secret(admin_name, admin_pw), algorithm="HS256")
    return {"token": token,
            "user": {"username": admin_name, "display_name": "Administrator"}}


def _secret(name: str, pw: str) -> str:
    return f"{os.getenv('JWT_SECRET', 'dev-secret')}|{name}|{pw}"


def admin_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    """Admin only. The admin token is separate from normal user tokens."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Please log in as admin.")
    name, pw = _credentials()
    try:
        data = jwt.decode(creds.credentials, _secret(name or "", pw or ""), algorithms=["HS256"])
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Your admin session expired. Please log in again.") from None
    if data.get("sub") != _ADMIN_SUBJECT:
        raise HTTPException(status_code=403, detail="Admins only.")
    return _ADMIN_SUBJECT


def _rows(conn, sql, args=()):
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    except Exception:  # table or column missing
        return []


@router.get("/api/admin/me")
def admin_me(_: str = Depends(admin_user)):
    return {"is_admin": True}


@router.get("/api/admin/users")
def admin_users(_: str = Depends(admin_user)):
    """One row per user with their totals."""
    with closing(auth._conn()) as conn:
        conn.row_factory = __import__("sqlite3").Row
        users = _rows(conn, "SELECT rowid AS rid, * FROM users")
    out = []
    with closing(storage._connect()) as conn:
        for u in users:
            name = u.get("username")
            sess = _rows(conn, "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at", (name,))
            scores = [s["performance_score"] for s in sess if s.get("performance_score") is not None]
            count = lambda t: (_rows(conn, f"SELECT COUNT(*) AS n FROM {t} WHERE user_id = ?", (name,)) or [{"n": 0}])[0]["n"]
            out.append({
                "member_id": f"GYM{u['rid']:05d}",
                "username": name,
                "name": u.get("display_name") or name,
                "sessions": len(sess),
                "total_reps": sum((s.get("reps") or 0) for s in sess),
                "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
                "best_score": max(scores) if scores else None,
                "last_session": sess[-1].get("created_at") if sess else None,
                "risk_checks": count("risk_checks"),
                "chats": count("chat_messages"),
                "meals": count("meals"),
            })
    return {"users": out}


@router.get("/api/admin/users/{username}/sessions")
def admin_user_sessions(username: str, _: str = Depends(admin_user)):
    with closing(storage._connect()) as conn:
        rows = _rows(conn, "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 200",
                     (username,))
    return {"username": username, "sessions": rows}


_USER_TABLES = ("sessions", "risk_checks", "chat_messages", "meals")


def _wipe_user_data(username: str) -> dict:
    counts = {}
    with closing(storage._connect()) as conn:
        for t in _USER_TABLES:
            try:
                counts[t] = conn.execute(f"DELETE FROM {t} WHERE user_id = ?", (username,)).rowcount
            except Exception:  # table missing
                counts[t] = 0
        conn.commit()
    return counts


@router.delete("/api/admin/users/{username}/data")
def admin_delete_user_data(username: str, _: str = Depends(admin_user)):
    """Deletes ALL of one user's saved data (sessions, risk checks, chats, meals). The account stays."""
    return {"username": username, "deleted": _wipe_user_data(username)}


@router.delete("/api/admin/users/{username}")
def admin_delete_user(username: str, _: str = Depends(admin_user)):
    """Deletes one user's account, profile and ALL their data."""
    counts = _wipe_user_data(username)
    try:
        from ai_modules import profile
        profile.delete_profile(username)
    except Exception:  # noqa: BLE001
        pass
    with closing(auth._conn()) as conn:
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
    return {"deleted_account": username, "deleted": counts}
