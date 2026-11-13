"""Profile routes: every user sets basic details after the first login."""
import os
import sys

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import profile  # noqa: E402
from auth_routes import current_user  # noqa: E402

router = APIRouter(tags=["Profile"])


class ProfileIn(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=60)
    age: int = Field(..., ge=10, le=100)
    gender: str = Field(..., max_length=30)
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=25, le=300)
    goal: str = Field(..., max_length=40)
    fitness_level: str = Field(..., max_length=30)
    workouts_per_week: int = Field(3, ge=0, le=14)
    diet_pref: str = Field("", max_length=30)
    injuries: str = Field("", max_length=200)


def _pack(username: str, row):
    return {"user_id": username, "member_id": profile.member_id(username), "profile": row, "complete": row is not None}


@router.get("/api/profile")
def get_my_profile(me: str = Depends(current_user)):
    return _pack(me, profile.get_profile(me))


@router.put("/api/profile")
def save_my_profile(req: ProfileIn, me: str = Depends(current_user)):
    data = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return _pack(me, profile.save_profile(me, data))
