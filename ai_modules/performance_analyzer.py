try:  # works both as `ai_modules.performance_analyzer` and as a plain script
    from ai_modules import storage
except ImportError:  # pragma: no cover
    import storage


def analyze_session(reps: int, duration_seconds: int, form_feedback_list: list,
                    user_id: str = "default") -> dict:
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

    result = {
        "reps": reps,
        "duration_seconds": duration_seconds,
        "form_quality_pct": form_quality_pct,
        "pace_reps_per_min": pace,
        "performance_score": score,
        "rating": rating
    }
    storage.log_session(result, user_id=user_id)  # keep history for weekly reports + analytics
    return result


def _trend(scores: list) -> str:
    """Compare the first and second half of the period (needs 2+ sessions)."""
    if len(scores) < 2:
        return "Not enough data"
    half = len(scores) // 2
    first = sum(scores[:half]) / half
    second = sum(scores[half:]) / (len(scores) - half)
    if second - first >= 2:
        return "Improving"
    if first - second >= 2:
        return "Declining"
    return "Stable"


def generate_weekly_report(session_scores: list) -> dict:
    """Aggregates a list of session result dicts into a weekly summary."""
    if not session_scores:
        return {"message": "No sessions recorded this week."}

    scores = [s["performance_score"] for s in session_scores]
    return {
        "sessions_this_week": len(session_scores),
        "total_reps": sum(s["reps"] for s in session_scores),
        "average_performance_score": round(sum(scores) / len(scores), 1),
        "best_performance_score": max(scores),
        "average_form_quality_pct": round(
            sum(s.get("form_quality_pct", 0) for s in session_scores) / len(session_scores), 1),
        "trend": _trend(scores),
    }


def generate_weekly_report_from_db(user_id: str = "default", days: int = 7) -> dict:
    """Weekly progress report built from the saved session history."""
    rows = storage.get_sessions(user_id=user_id, days=days)
    if not rows:
        return {"user_id": user_id, "period_days": days, "sessions_this_week": 0,
                "message": "No sessions recorded in this period."}

    report = generate_weekly_report(rows)
    daily: dict = {}
    for r in rows:
        day = r["created_at"][:10]
        d = daily.setdefault(day, {"date": day, "sessions": 0, "total_reps": 0, "_scores": []})
        d["sessions"] += 1
        d["total_reps"] += r["reps"] or 0
        d["_scores"].append(r["performance_score"])
    daily_list = []
    for d in daily.values():
        scores = d.pop("_scores")
        d["avg_score"] = round(sum(scores) / len(scores), 1)
        daily_list.append(d)

    report.update({
        "user_id": user_id,
        "period_days": days,
        "daily_breakdown": sorted(daily_list, key=lambda x: x["date"]),
        "summary": (f"{report['sessions_this_week']} session(s), {report['total_reps']} reps, "
                    f"average score {report['average_performance_score']} — trend: {report['trend']}."),
    })
    return report
