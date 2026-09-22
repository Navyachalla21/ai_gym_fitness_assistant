import numpy as np
from sklearn.linear_model import LogisticRegression

# Realistic synthetic training data representing behavioral patterns.
# Features: [days_since_last_workout, weekly_avg_sessions, avg_session_completion_pct]
# Label: 1 = likely to skip next workout, 0 = likely to attend
_TRAINING_X = np.array([
    [1, 5, 95], [0, 6, 98], [1, 4, 90], [2, 4, 85],
    [3, 3, 70], [4, 2, 60], [5, 2, 55], [6, 1, 40],
    [7, 1, 30], [8, 0, 20], [2, 5, 92], [3, 4, 75],
    [0, 5, 96], [1, 3, 80], [5, 1, 35], [6, 0, 25],
])
_TRAINING_Y = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1])

_model = LogisticRegression()
_model.fit(_TRAINING_X, _TRAINING_Y)


def predict_skip_risk(days_since_last_workout: int, weekly_avg_sessions: float,
                       avg_session_completion_pct: float) -> dict:
    """
    Predicts the probability a user will skip their next workout,
    based on recent engagement patterns.
    """
    features = np.array([[days_since_last_workout, weekly_avg_sessions, avg_session_completion_pct]])
    skip_probability = _model.predict_proba(features)[0][1]
    risk_level = "High" if skip_probability > 0.6 else "Medium" if skip_probability > 0.3 else "Low"

    nudge = None
    if risk_level == "High":
        nudge = "We miss you! A quick 15-minute session today keeps your streak alive 💪"
    elif risk_level == "Medium":
        nudge = "You're doing well — don't break momentum, even a light session counts today."

    return {
        "skip_probability": round(float(skip_probability), 2),
        "risk_level": risk_level,
        "nudge": nudge
    }