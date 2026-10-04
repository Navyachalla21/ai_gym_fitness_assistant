"""Module 7: Gym Recommender & Planner — programs by goal + fitness level, nearby gyms by location,
challenges by streak. Fitness level can come from the user's saved workout history."""
import math

try:
    from ai_modules import storage
except ImportError:  # pragma: no cover
    import storage

LEVELS = ("beginner", "intermediate", "advanced")

# Programs per goal and fitness level (plain-language names so beginners know what they are getting)
_WORKOUT_PROGRAMS = {
    "weight loss": {
        "beginner": ["Walk + Light Strength Starter (3 days/week)", "Low-Impact Cardio Intro", "21-Day Habit Builder"],
        "intermediate": ["HIIT Circuit Training", "Cardio + Strength Combo", "30-Day Fat Burn Challenge"],
        "advanced": ["Advanced HIIT + Strength Split", "Metabolic Conditioning Block", "Tabata Ladder Challenge"],
    },
    "muscle gain": {
        "beginner": ["Full Body 3-Day Starter", "Machine-Based Strength Intro", "Form-First Foundation Block"],
        "intermediate": ["Progressive Overload Strength Program", "Push-Pull-Legs Split", "Hypertrophy Block"],
        "advanced": ["Heavy Upper/Lower Split", "Powerbuilding Block", "Periodized Hypertrophy Cycle"],
    },
    "endurance": {
        "beginner": ["Run-Walk Starter Plan", "Easy Cardio Base Builder", "2K-to-5K Starter"],
        "intermediate": ["5K Training Plan", "Interval Running Program", "Cardio Endurance Builder"],
        "advanced": ["10K Tempo Plan", "Long-Run + Intervals Block", "Threshold Training Program"],
    },
    "general fitness": {
        "beginner": ["Full Body Beginner Program", "3-Day Balanced Routine", "Functional Fitness Basics"],
        "intermediate": ["Balanced Strength + Cardio Week", "4-Day Functional Plan", "Mobility + Core Add-on"],
        "advanced": ["Athletic Conditioning Program", "Strength + Skills Block", "Hybrid Training Plan"],
    },
}

# DEMO gym data: invented gyms placed around real city centres (a production system would use
# the Google Places API). Each gym: (name, lat offset, lon offset, rating).
CITIES = {
    "Bengaluru": (12.9716, 77.5946),
    "Mysuru": (12.2958, 76.6394),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Delhi": (28.6139, 77.2090),
}
_DEMO_GYM_TEMPLATES = [
    ("FitZone Elite", +0.012, +0.008, 4.5),
    ("PowerHouse Gym", -0.018, +0.015, 4.2),
    ("CoreFit Studio", +0.030, -0.022, 4.7),
    ("IronWorks Fitness", -0.035, -0.030, 4.0),
]
_DEMO_GYMS = [
    {"name": name, "city": city, "latitude": round(lat + dlat, 5), "longitude": round(lon + dlon, 5), "rating": rating}
    for city, (lat, lon) in CITIES.items()
    for name, dlat, dlon, rating in _DEMO_GYM_TEMPLATES
]

# kept for backward compatibility with the old no-argument call
_NEARBY_GYMS_DEMO = [
    {"name": "FitZone Elite", "distance_km": 1.2, "rating": 4.5},
    {"name": "PowerHouse Gym", "distance_km": 2.1, "rating": 4.2},
    {"name": "CoreFit Studio", "distance_km": 3.4, "rating": 4.7},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def resolve_location(city: str | None = None, latitude: float | None = None, longitude: float | None = None):
    """Returns (lat, lon, label) from coordinates or a city name, or (None, None, None)."""
    if latitude is not None and longitude is not None:
        return latitude, longitude, f"{latitude:.4f}, {longitude:.4f}"
    if city:
        for name, (lat, lon) in CITIES.items():
            if name.lower() == city.strip().lower():
                return lat, lon, name
    return None, None, None


def recommend_nearby_gyms(latitude: float | None = None, longitude: float | None = None, limit: int = 3) -> list:
    """Nearest demo gyms to a location. With no location, returns the old fixed demo list."""
    if latitude is None or longitude is None:
        return sorted(_NEARBY_GYMS_DEMO, key=lambda g: g["distance_km"])
    ranked = sorted(
        ({"name": g["name"], "city": g["city"], "rating": g["rating"],
          "distance_km": round(haversine_km(latitude, longitude, g["latitude"], g["longitude"]), 1)}
         for g in _DEMO_GYMS),
        key=lambda g: g["distance_km"])
    return ranked[:limit]


def fitness_level_from_history(user_id: str = "default", days: int = 30) -> dict:
    """Infers beginner / intermediate / advanced from saved workout sessions."""
    sessions = storage.get_sessions(user_id=user_id, days=days)
    n = len(sessions)
    scores = [s["performance_score"] for s in sessions if s["performance_score"] is not None]
    avg = sum(scores) / len(scores) if scores else 0
    if n >= 8 and avg >= 65:
        level = "advanced"
    elif n >= 3 and avg >= 45:
        level = "intermediate"
    else:
        level = "beginner"
    reason = (f"{n} session(s) in the last {days} days, average score {avg:.1f}" if n
              else f"no sessions saved in the last {days} days yet")
    return {"level": level, "reason": reason, "sessions": n, "average_score": round(avg, 1)}


def recommend_programs(goal: str, level: str = "intermediate") -> list:
    """Workout programs for the goal and fitness level."""
    goal_key = goal.lower().strip()
    programs = _WORKOUT_PROGRAMS.get(goal_key, _WORKOUT_PROGRAMS["general fitness"])
    return programs.get(level, programs["intermediate"])


def recommend_challenge(goal: str, current_streak_days: int) -> str:
    """Suggests a fitness challenge based on goal and current engagement."""
    if current_streak_days < 3:
        return "3-Day Kickstart Challenge — build your first habit streak!"
    elif current_streak_days < 14:
        return f"14-Day {goal.title()} Challenge — you're building real momentum!"
    else:
        return f"30-Day {goal.title()} Mastery Challenge — you're ready for the next level!"


def recommend_all(goal: str, current_streak_days: int = 0, city: str | None = None,
                  latitude: float | None = None, longitude: float | None = None,
                  user_id: str = "default", fitness_level: str | None = None) -> dict:
    """Full recommendation using goal, location and workout history."""
    if fitness_level in LEVELS:
        level_info = {"level": fitness_level, "reason": "chosen by you"}
    else:
        level_info = fitness_level_from_history(user_id)

    lat, lon, label = resolve_location(city, latitude, longitude)
    gyms = recommend_nearby_gyms(lat, lon)
    result = {
        "goal": goal,
        "fitness_level": level_info["level"],
        "fitness_level_reason": level_info["reason"],
        "programs": recommend_programs(goal, level_info["level"]),
        "nearby_gyms": gyms,
        "challenge": recommend_challenge(goal, current_streak_days),
        "location_used": label,
    }
    if lat is None:
        result["location_note"] = "No location given — showing sample distances. Choose a city or enter coordinates."
    elif gyms and gyms[0]["distance_km"] > 100:
        result["location_note"] = "No demo gyms near this location — showing the nearest sample gyms."
    return result
