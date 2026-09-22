def analyze_session(reps: int, duration_seconds: int, form_feedback_list: list) -> dict:
    """
    Scores a single workout session based on rep count, pacing, and form quality.
    'form_feedback_list' is a list of feedback strings collected during the session
    (e.g., from pose_detector.py's rep_counter.feedback over time).
    """
    good_form_count = sum(1 for fb in form_feedback_list if "good" in fb.lower())
    total_feedback = len(form_feedback_list) or 1
    form_quality_pct = round((good_form_count / total_feedback) * 100, 1)

    # Reps per minute — a simple efficiency measure
    minutes = max(duration_seconds / 60, 0.1)
    pace = round(reps / minutes, 1)

    # Composite performance score out of 100
    score = round((form_quality_pct * 0.6) + (min(pace / 15, 1) * 100 * 0.4), 1)

    if score >= 80:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    else:
        rating = "Needs Improvement"

    return {
        "reps": reps,
        "duration_seconds": duration_seconds,
        "form_quality_pct": form_quality_pct,
        "pace_reps_per_min": pace,
        "performance_score": score,
        "rating": rating
    }


def generate_weekly_report(session_scores: list) -> dict:
    """Aggregates multiple session scores into a weekly summary."""
    if not session_scores:
        return {"message": "No sessions recorded this week."}

    avg_score = round(sum(s["performance_score"] for s in session_scores) / len(session_scores), 1)
    total_reps = sum(s["reps"] for s in session_scores)

    return {
        "sessions_this_week": len(session_scores),
        "total_reps": total_reps,
        "average_performance_score": avg_score,
        "trend": "Improving" if len(session_scores) > 1 and session_scores[-1]["performance_score"] > session_scores[0]["performance_score"] else "Stable"
    }