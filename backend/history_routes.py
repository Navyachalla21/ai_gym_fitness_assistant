"""History and delete routes (Step 3). Every route needs a login and only touches the caller's own rows.
Deleted rows are removed from the database for good."""
import os
import sys
from contextlib import closing

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import auth, storage  # noqa: E402
from auth_routes import current_user  # noqa: E402

router = APIRouter(tags=["History & Privacy"])

# module name used in the URL -> real table name (only these can ever be touched)
MODULES = {
    "sessions": "sessions",
    "risk-checks": "risk_checks",
    "chats": "chat_messages",
    "meals": "meals",
}


def _table(module: str) -> str:
    if module not in MODULES:
        raise HTTPException(status_code=404, detail=f"Unknown module. Use one of: {', '.join(MODULES)}")
    return MODULES[module]


@router.get("/api/history")
def history_overview(me: str = Depends(current_user)):
    """How many records you have in each module."""
    counts = {}
    with closing(storage._connect()) as conn:
        for name, table in MODULES.items():
            counts[name] = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (me,)).fetchone()[0]
    return {"user": me, "counts": counts}


@router.get("/api/history/{module}")
def history_list(module: str, limit: int = Query(200, ge=1, le=1000), me: str = Depends(current_user)):
    table = _table(module)
    with closing(storage._connect()) as conn:
        rows = conn.execute(f"SELECT * FROM {table} WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
                            (me, limit)).fetchall()
    return {"module": module, "records": [dict(r) for r in rows]}


@router.delete("/api/history/{module}/{record_id}")
def history_delete_one(module: str, record_id: int, me: str = Depends(current_user)):
    table = _table(module)
    with closing(storage._connect()) as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE id = ? AND user_id = ?", (record_id, me))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": record_id}


@router.delete("/api/history/{module}")
def history_delete_module(module: str, me: str = Depends(current_user)):
    """Deletes ALL of your records in one module."""
    table = _table(module)
    with closing(storage._connect()) as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (me,))
        conn.commit()
    return {"module": module, "deleted_count": cur.rowcount}


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., max_length=72)


@router.post("/api/account/delete")
def delete_account(req: DeleteAccountRequest, me: str = Depends(current_user)):
    """Deletes your account and ALL your data in every module. Needs your password."""
    if auth.verify_user(me, req.password) is None:
        raise HTTPException(status_code=403, detail="Wrong password. Nothing was deleted.")
    with closing(storage._connect()) as conn:
        for table in MODULES.values():
            conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (me,))
        conn.commit()
    with closing(auth._conn()) as conn:
        conn.execute("DELETE FROM users WHERE username = ?", (me,))
        conn.commit()
    return {"deleted_account": me}