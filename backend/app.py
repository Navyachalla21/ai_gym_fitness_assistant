import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_modules.diet_coach import generate_diet_plan
from ai_modules.behavior_predictor import predict_skip_risk
from ai_modules.gym_buddy_chat import chat_with_buddy
from ai_modules.performance_analyzer import analyze_session, generate_weekly_report
from ai_modules.gym_recommender import recommend_programs, recommend_nearby_gyms, recommend_challenge
from ai_modules.smart_gym_assistant import simulate_sensor_reading, recommend_adjustment
from auth_routes import router as auth_router, optional_user, resolve_user

app = FastAPI(title="AI Gym & Fitness Assistant API")

from analytics_routes import router as analytics_router
app.include_router(analytics_router)
app.include_router(auth_router)

from history_routes import router as history_router
app.include_router(history_router)

# Allow the frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request models ----------
class DietRequest(BaseModel):
    weight_kg: float
    height_cm: float
    goal: str
    preferences: str


class BehaviorRequest(BaseModel):
    days_since_last_workout: int
    weekly_avg_sessions: float
    avg_session_completion_pct: float


class ChatRequest(BaseModel):
    message: str


class SessionRequest(BaseModel):
    reps: int
    duration_seconds: int
    form_feedback_list: list[str]


class RecommendRequest(BaseModel):
    goal: str
    current_streak_days: int = 0


# ---------- Routes ----------
# Logged-in callers (Authorization: Bearer <token>) are saved under their own account.
# Callers without a token are saved under the shared "default" guest account, as before.

@app.get("/")
def root():
    return {"message": "AI Gym & Fitness Assistant API is running."}


@app.post("/api/diet-plan")
def diet_plan(req: DietRequest):
    return generate_diet_plan(req.weight_kg, req.height_cm, req.goal, req.preferences)


@app.post("/api/behavior-risk")
def behavior_risk(req: BehaviorRequest, me: Optional[str] = Depends(optional_user)):
    return predict_skip_risk(req.days_since_last_workout, req.weekly_avg_sessions,
                             req.avg_session_completion_pct, user_id=resolve_user(me))


@app.post("/api/gym-buddy-chat")
def gym_buddy(req: ChatRequest, me: Optional[str] = Depends(optional_user)):
    return chat_with_buddy(req.message, user_id=resolve_user(me))


@app.post("/api/analyze-session")
def analyze(req: SessionRequest, me: Optional[str] = Depends(optional_user)):
    return analyze_session(req.reps, req.duration_seconds, req.form_feedback_list,
                           user_id=resolve_user(me))


@app.get("/api/smart-gym-reading")
def smart_gym_reading():
    reading = simulate_sensor_reading()
    advice = recommend_adjustment(reading)
    return {"reading": reading, "advice": advice}


@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    return {
        "programs": recommend_programs(req.goal),
        "nearby_gyms": recommend_nearby_gyms(),
        "challenge": recommend_challenge(req.goal, req.current_streak_days)
    }