"""
Nutrition tracking for the AI Dietician (Module 2): daily calorie target + intake summary.

The target is an ESTIMATE (Mifflin-St Jeor with an assumed age and a sex-neutral constant,
lightly-active multiplier, then adjusted for the goal). It is not medical advice.
"""
from datetime import datetime, timedelta, timezone

try:
    from ai_modules import storage
except ImportError:  # pragma: no cover
    import storage

# calories added to / removed from maintenance for each goal
_GOAL_ADJUSTMENT = {
    "weight loss": -500,
    "muscle gain": +300,
    "endurance": +150,
    "general fitness": 0,
}
_ASSUMED_AGE = 25
_ACTIVITY_FACTOR = 1.4   # lightly active
_MIN_CALORIES = 1200     # never suggest less than this


def calorie_target(weight_kg: float, height_cm: float, goal: str) -> dict:
    """Estimated daily calorie target for the user's goal."""
    # Mifflin-St Jeor: 10*kg + 6.25*cm - 5*age + s, with s = +5 (men) / -161 (women).
    # We don't ask for sex, so use the midpoint (-78).
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * _ASSUMED_AGE - 78
    maintenance = bmr * _ACTIVITY_FACTOR
    adjustment = _GOAL_ADJUSTMENT.get(goal.lower().strip(), 0)
    target = max(_MIN_CALORIES, round((maintenance + adjustment) / 10) * 10)
    return {
        "target_calories": int(target),
        "maintenance_calories": int(round(maintenance / 10) * 10),
        "goal": goal,
        "note": "Estimate only (assumes age 25, lightly active). Consult a dietitian for personal advice.",
    }


def _local_date(iso_timestamp: str, tz_offset_min: int):
    """Date of a stored UTC timestamp in the user's local time zone (default: India, +330 min)."""
    dt = datetime.fromisoformat(iso_timestamp)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt + timedelta(minutes=tz_offset_min)).date()


def summarize_intake(user_id: str = "default", target_calories: float | None = None, days: int = 7,
                     tz_offset_min: int = 330, now: datetime | None = None) -> dict:
    """Today's meals and totals, plus a per-day history for the last `days` days."""
    now = now or datetime.now(timezone.utc)
    today = (now + timedelta(minutes=tz_offset_min)).date()
    rows = storage.get_meals(user_id=user_id, days=days + 2)  # +2 days margin for time-zone edges

    per_day: dict = {}
    for r in rows:
        d = _local_date(r["created_at"], tz_offset_min)
        entry = per_day.setdefault(d, {"calories": 0.0, "protein_g": 0.0, "meals": []})
        entry["calories"] += r["calories"]
        entry["protein_g"] += r["protein_g"]
        entry["meals"].append({"id": r["id"], "meal_name": r["meal_name"],
                               "calories": r["calories"], "protein_g": r["protein_g"]})

    daily = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        e = per_day.get(d, {"calories": 0.0, "protein_g": 0.0})
        daily.append({"date": d.isoformat(), "calories": round(e["calories"]), "protein_g": round(e["protein_g"], 1)})

    t = per_day.get(today, {"calories": 0.0, "protein_g": 0.0, "meals": []})
    eaten = round(t["calories"])
    result = {
        "user_id": user_id,
        "date": today.isoformat(),
        "today": {"calories": eaten, "protein_g": round(t["protein_g"], 1), "meals": t["meals"]},
        "daily": daily,
        "target_calories": target_calories,
    }
    if target_calories:
        result["today"]["remaining"] = round(target_calories - eaten)
        result["today"]["percent_of_target"] = round(100 * eaten / target_calories, 1)
        result["today"]["status"] = ("Over target" if eaten > target_calories * 1.1
                                     else "On track" if eaten >= target_calories * 0.9
                                     else "Under target")
    return result
