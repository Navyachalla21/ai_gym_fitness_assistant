"""
Analytics, weekly-report and Phase 3 routes (recommender, nutrition tracking, live IoT) for the
AI Gym & Fitness Assistant.

Add these TWO lines to backend/app.py (after `app = FastAPI(...)`):

    from analytics_routes import router as analytics_router
    app.include_router(analytics_router)
"""
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Make `ai_modules` importable no matter where uvicorn is started from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import storage  # noqa: E402
from ai_modules import gym_recommender, nutrition_tracker, smart_gym_assistant  # noqa: E402
from ai_modules.mqtt_bridge import bridge  # noqa: E402
from ai_modules.performance_analyzer import generate_weekly_report_from_db  # noqa: E402

router = APIRouter(tags=["Analytics & Reports"])


@router.get("/api/weekly-report")
def weekly_report(user_id: str = Query("default"), days: int = Query(7, ge=1, le=90)):
    """Module 6: weekly progress report built from saved sessions."""
    return generate_weekly_report_from_db(user_id=user_id, days=days)


@router.get("/api/analytics/summary")
def analytics_summary(user_id: str = Query("default"), days: int = Query(30, ge=1, le=365)):
    """Admin dashboard headline numbers."""
    sessions = storage.get_sessions(user_id, days=days)
    risks = storage.get_risks(user_id, days=days)
    chats = [c for c in storage.get_chats(user_id, days=days) if c["role"] == "user"]

    def dist(rows, key):
        out: dict = {}
        for r in rows:
            out[r[key]] = out.get(r[key], 0) + 1
        return out

    scores = [s["performance_score"] for s in sessions if s["performance_score"] is not None]
    return {
        "user_id": user_id,
        "period_days": days,
        "total_sessions": len(sessions),
        "total_reps": sum(s["reps"] or 0 for s in sessions),
        "average_performance_score": round(sum(scores) / len(scores), 1) if scores else None,
        "risk_checks": len(risks),
        "risk_distribution": dist(risks, "risk_level"),
        "chat_messages": len(chats),
        "sentiment_distribution": dist(chats, "sentiment"),
        "rating_distribution": dist(sessions, "rating"),
    }


@router.get("/api/analytics/sessions")
def analytics_sessions(user_id: str = Query("default"), days: int = Query(30, ge=1, le=365),
                       limit: int = Query(200, ge=1, le=1000)):
    return {"user_id": user_id, "sessions": storage.get_sessions(user_id, days=days, limit=limit)}


@router.get("/api/analytics/risks")
def analytics_risks(user_id: str = Query("default"), days: int = Query(30, ge=1, le=365),
                    limit: int = Query(200, ge=1, le=1000)):
    return {"user_id": user_id, "risk_checks": storage.get_risks(user_id, days=days, limit=limit)}


@router.get("/api/analytics/mood")
def analytics_mood(user_id: str = Query("default"), limit: int = Query(50, ge=1, le=500)):
    """Module 5: emotional-state history from chat sentiment."""
    from ai_modules.gym_buddy_chat import get_mood_trend  # imported lazily: needs the Gemini key
    return get_mood_trend(user_id=user_id, limit=limit)


@router.get("/api/analytics/users")
def analytics_users():
    return {"users": storage.list_users()}


@router.post("/api/analytics/seed-demo")
def seed_demo():
    """Loads clearly-labelled DEMO history under user_id 'demo' so the dashboard has data to show."""
    return storage.seed_demo_data("demo")


# ======================================================================================
# Phase 3: Gym Recommender (location + history)
# ======================================================================================
class RecommendRequest(BaseModel):
    goal: str = "general fitness"
    current_streak_days: int = Field(0, ge=0, le=3650)
    city: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    user_id: str = "default"
    fitness_level: Optional[str] = None   # beginner / intermediate / advanced; None = work it out from history


@router.post("/api/recommend-plus", tags=["Gym Recommender"])
def recommend_plus(req: RecommendRequest):
    """Programs by goal + fitness level (from saved sessions), nearest gyms by location, challenge by streak."""
    return gym_recommender.recommend_all(
        goal=req.goal, current_streak_days=req.current_streak_days, city=req.city,
        latitude=req.latitude, longitude=req.longitude, user_id=req.user_id,
        fitness_level=req.fitness_level)


@router.get("/api/cities", tags=["Gym Recommender"])
def list_cities():
    return {"cities": list(gym_recommender.CITIES)}


# ======================================================================================
# Phase 3: Nutrition tracking (Dietician)
# ======================================================================================
class MealRequest(BaseModel):
    meal_name: str = Field(..., min_length=1, max_length=100)
    calories: float = Field(..., ge=0, le=5000)
    protein_g: float = Field(0, ge=0, le=500)
    user_id: str = "default"


@router.get("/api/calorie-target", tags=["Nutrition"])
def calorie_target(weight_kg: float = Query(..., gt=20, lt=300), height_cm: float = Query(..., gt=100, lt=250),
                   goal: str = Query("general fitness")):
    return nutrition_tracker.calorie_target(weight_kg, height_cm, goal)


@router.post("/api/meals", tags=["Nutrition"])
def log_meal(req: MealRequest):
    meal_id = storage.log_meal(req.meal_name.strip(), req.calories, req.protein_g, user_id=req.user_id)
    if meal_id is None:
        raise HTTPException(status_code=500, detail="Could not save the meal")
    return {"id": meal_id, "meal_name": req.meal_name.strip(), "calories": req.calories, "protein_g": req.protein_g}


@router.delete("/api/meals/{meal_id}", tags=["Nutrition"])
def delete_meal(meal_id: int, user_id: str = Query("default")):
    if not storage.delete_meal(meal_id, user_id):
        raise HTTPException(status_code=404, detail="Meal not found")
    return {"deleted": meal_id}


@router.get("/api/meals/summary", tags=["Nutrition"])
def meals_summary(user_id: str = Query("default"), target_calories: Optional[float] = Query(None, gt=0, le=10000),
                  days: int = Query(7, ge=1, le=90), tz_offset_min: int = Query(330, ge=-720, le=840)):
    """Today's intake vs target, plus the last `days` days. tz_offset_min defaults to India (UTC+5:30)."""
    return nutrition_tracker.summarize_intake(user_id, target_calories, days, tz_offset_min)


# ======================================================================================
# Phase 3: Smart Gym - live IoT data over MQTT
# ======================================================================================
class ResistanceCommand(BaseModel):
    resistance_level: int = Field(..., ge=1, le=10)


@router.get("/api/smart-gym-live", tags=["Smart Gym (MQTT)"])
def smart_gym_live():
    """Latest reading from the MQTT broker. If no equipment has published recently, falls back to a
    simulated reading and says so in `source`."""
    bridge.start()                      # starts the background subscriber on first use
    reading = bridge.latest()
    source = "mqtt"
    if reading is None:
        reading = smart_gym_assistant.simulate_sensor_reading()
        source = "simulated"
    return {"source": source, "reading": reading,
            "analysis": smart_gym_assistant.recommend_adjustment_detailed(reading),
            "mqtt": bridge.status()}


@router.post("/api/smart-gym-live/apply", tags=["Smart Gym (MQTT)"])
def smart_gym_apply(cmd: ResistanceCommand):
    """Sends a resistance change to the equipment over MQTT."""
    bridge.start()
    sent = bridge.publish_command(cmd.resistance_level)
    if not sent:
        raise HTTPException(status_code=503, detail="Not connected to the MQTT broker yet - try again in a few seconds")
    return {"sent": True, "resistance_level": cmd.resistance_level}
