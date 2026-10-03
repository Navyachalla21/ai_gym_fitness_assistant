"""
Analytics + weekly-report routes for the AI Gym & Fitness Assistant.

Add these TWO lines to backend/app.py (after `app = FastAPI(...)`):

    from analytics_routes import router as analytics_router
    app.include_router(analytics_router)
"""
import os
import sys

from fastapi import APIRouter, Query

# Make `ai_modules` importable no matter where uvicorn is started from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ai_modules import storage  # noqa: E402
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
