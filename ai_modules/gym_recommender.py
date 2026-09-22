# Demo program/gym data — in production this would come from a real database or Places API
_WORKOUT_PROGRAMS = {
    "weight loss": ["HIIT Circuit Training", "Cardio + Strength Combo", "30-Day Fat Burn Challenge"],
    "muscle gain": ["Progressive Overload Strength Program", "Push-Pull-Legs Split", "Hypertrophy Block"],
    "endurance": ["5K Training Plan", "Interval Running Program", "Cardio Endurance Builder"],
    "general fitness": ["Full Body Beginner Program", "3-Day Balanced Routine", "Functional Fitness Basics"],
}

_NEARBY_GYMS_DEMO = [
    {"name": "FitZone Elite", "distance_km": 1.2, "rating": 4.5},
    {"name": "PowerHouse Gym", "distance_km": 2.1, "rating": 4.2},
    {"name": "CoreFit Studio", "distance_km": 3.4, "rating": 4.7},
]


def recommend_programs(goal: str) -> list:
    """Recommends workout programs matching the user's stated goal."""
    goal_key = goal.lower().strip()
    return _WORKOUT_PROGRAMS.get(goal_key, _WORKOUT_PROGRAMS["general fitness"])


def recommend_nearby_gyms() -> list:
    """
    Returns nearby gym suggestions.
    NOTE: This uses demo data. In production, this would integrate with the
    Google Places API using the user's real location.
    """
    return sorted(_NEARBY_GYMS_DEMO, key=lambda g: g["distance_km"])


def recommend_challenge(goal: str, current_streak_days: int) -> str:
    """Suggests a fitness challenge based on goal and current engagement."""
    if current_streak_days < 3:
        return "3-Day Kickstart Challenge — build your first habit streak!"
    elif current_streak_days < 14:
        return f"14-Day {goal.title()} Challenge — you're building real momentum!"
    else:
        return f"30-Day {goal.title()} Mastery Challenge — you're ready for the next level!"