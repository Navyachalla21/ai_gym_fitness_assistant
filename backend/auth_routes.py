"""Login routes. Other routes use `current_user` / `optional_user` to find out who is calling."""
import os
import sys
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import auth  # noqa: E402

router = APIRouter(prefix="/auth", tags=["Accounts"])
_bearer = HTTPBearer(auto_error=False)

GUEST_IDS = {"default", "demo"}   # shared, not-logged-in data (used by tests and the demo)


class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=30)
    password: str = Field(..., max_length=72)
    display_name: str = Field("", max_length=60)


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=30)
    password: str = Field(..., max_length=72)


def current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    """Login required."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Please log in.")
    username = auth.read_token(creds.credentials)
    if username is None:
        raise HTTPException(status_code=401, detail="Your session expired. Please log in again.")
    return username


def optional_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> Optional[str]:
    """No token -> None (guest). A token that is wrong or expired is still refused."""
    if creds is None:
        return None
    username = auth.read_token(creds.credentials)
    if username is None:
        raise HTTPException(status_code=401, detail="Your session expired. Please log in again.")
    return username


def resolve_user(logged_in: Optional[str], requested: str = "default") -> str:
    """Logged-in users always get their OWN data, whatever user_id they ask for.
    Guests can only reach the shared 'default' and 'demo' data."""
    if logged_in:
        return logged_in
    return requested if requested in GUEST_IDS else "default"


@router.post("/register")
def register(req: RegisterRequest):
    try:
        user = auth.create_user(req.username, req.password, req.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"token": auth.make_token(user["username"]), "user": user}


@router.post("/login")
def login(req: LoginRequest):
    user = auth.verify_user(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    return {"token": auth.make_token(user["username"]), "user": user}


@router.get("/me")
def me(username: str = Depends(current_user)):
    return auth.get_user(username)