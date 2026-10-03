"""
API test runner for the AI Gym & Fitness Assistant.

Usage (backend must be running):
    python run_tests.py                                   # tests http://localhost:8000
    python run_tests.py https://ai-gym-backend-bwiz.onrender.com   # tests the live backend

Writes test_results.md (a Markdown table with the ACTUAL results) and prints it.
"""
import sys
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
TIMEOUT = 90  # Render's free tier can take ~50s to wake up
rows = []


def call(method, path, **kw):
    return requests.request(method, BASE + path, timeout=TIMEOUT, **kw)


def record(module, test, inp, expected, fn):
    """Run fn() -> (ok, actual_text). Any exception is recorded as a FAIL."""
    try:
        ok, actual = fn()
    except Exception as exc:  # noqa: BLE001
        ok, actual = False, f"Error: {exc}"
    rows.append((module, test, inp, expected, str(actual).replace("|", "/").replace("\n", " "),
                 "PASS" if ok else "FAIL"))


# ------------------------------------------------------------------ API
def t_root():
    r = call("GET", "/")
    return r.status_code == 200, f"{r.status_code} {r.text[:80]}"


def t_diet():
    r = call("POST", "/api/diet-plan", json={"weight_kg": 70, "height_cm": 170,
                                             "goal": "weight loss", "preferences": "vegetarian"})
    d = r.json()
    return (r.status_code == 200 and d["bmi"] == 24.2 and d["category"] == "Normal weight"
            and len(d["plan"]) > 100), f"BMI {d.get('bmi')} ({d.get('category')}), plan length {len(d.get('plan', ''))} chars"


def t_diet_underweight():
    r = call("POST", "/api/diet-plan", json={"weight_kg": 50, "height_cm": 170,
                                             "goal": "muscle gain", "preferences": "no restrictions"})
    d = r.json()
    return (r.status_code == 200 and d["bmi"] == 17.3 and d["category"] == "Underweight"), \
        f"BMI {d.get('bmi')} ({d.get('category')})"


def risk(days, weekly, comp):
    return call("POST", "/api/behavior-risk", json={"days_since_last_workout": days,
                                                    "weekly_avg_sessions": weekly,
                                                    "avg_session_completion_pct": comp}).json()


def t_risk_high():
    d = risk(13, 1.28, 77)
    s = d.get("suggested_schedule") or {}
    return (d["risk_level"] == "High" and s.get("session_length_min") == 15), \
        f"{d['risk_level']} ({d['skip_probability']:.0%}); schedule: {s.get('intensity')}, {s.get('session_length_min')} min"


def t_risk_low():
    d = risk(1, 6, 95)
    s = d.get("suggested_schedule") or {}
    return (d["risk_level"] == "Low" and d["nudge"] is None), \
        f"{d['risk_level']} ({d['skip_probability']:.0%}); schedule: {s.get('intensity')}, {s.get('session_length_min')} min"


def t_risk_mid():
    d = risk(3, 3, 70)  # informational: records what the model returns for a middle profile
    return d["risk_level"] in ("Low", "Medium", "High"), f"{d['risk_level']} ({d['skip_probability']:.0%})"


def buddy(msg):
    return call("POST", "/api/gym-buddy-chat", json={"message": msg}).json()


def t_buddy(msg, want):
    def run():
        d = buddy(msg)
        return d["sentiment"] == want and len(d["reply"]) > 10, f"sentiment={d['sentiment']}; reply: {d['reply'][:90]}..."
    return run


def t_session_good():
    d = call("POST", "/api/analyze-session", json={"reps": 12, "duration_seconds": 120,
                                                   "form_feedback_list": ["Good rep!"] * 10 + ["Adjust form"] * 2}).json()
    return (d["performance_score"] == 66.0 and d["form_quality_pct"] == 83.3 and d["rating"] == "Good"), \
        f"score {d['performance_score']}, form {d['form_quality_pct']}%, rating {d['rating']}"


def t_session_poor():
    d = call("POST", "/api/analyze-session", json={"reps": 3, "duration_seconds": 300,
                                                   "form_feedback_list": ["Keep elbow tucked in!"] * 4 + ["Good rep!"]}).json()
    return d["rating"] == "Needs Improvement", f"score {d['performance_score']}, form {d['form_quality_pct']}%, rating {d['rating']}"


def t_smart():
    d = call("GET", "/api/smart-gym-reading").json()
    hr = d["reading"]["heart_rate_bpm"]
    advice = d["advice"].lower()
    expect = "reducing" if hr > 150 else "increase" if hr < 100 else "maintain"
    return expect in advice, f"HR {hr} bpm, resistance {d['reading']['resistance_level']}, status {d['reading']['equipment_status']} -> {d['advice'][:70]}"


def t_recommend(goal, streak, want_text):
    def run():
        d = call("POST", "/api/recommend", json={"goal": goal, "current_streak_days": streak}).json()
        return (len(d["programs"]) >= 1 and len(d["nearby_gyms"]) >= 1 and want_text in d["challenge"]), \
            f"{len(d['programs'])} programs, {len(d['nearby_gyms'])} gyms, challenge: {d['challenge'][:60]}"
    return run


def t_weekly():
    r = call("GET", "/api/weekly-report", params={"user_id": "default", "days": 7})
    d = r.json()
    return r.status_code == 200 and ("sessions_this_week" in d), f"{r.status_code}; {d.get('summary') or d.get('message')}"


def t_summary():
    r = call("GET", "/api/analytics/summary", params={"user_id": "default", "days": 30})
    d = r.json()
    return r.status_code == 200 and "total_sessions" in d, f"{r.status_code}; sessions={d.get('total_sessions')}, risk checks={d.get('risk_checks')}"


def t_validation():
    r = call("POST", "/api/diet-plan", json={})
    return r.status_code == 422, f"HTTP {r.status_code} for empty body"


record("Backend API", "Root endpoint availability", "GET /", "200 OK", t_root)
record("AI Dietician", "BMI + plan (normal BMI)", "70 kg, 170 cm, weight loss, vegetarian", "BMI 24.2 Normal weight, plan returned", t_diet)
record("AI Dietician", "BMI category (underweight)", "50 kg, 170 cm, muscle gain", "BMI 17.3 Underweight", t_diet_underweight)
record("Habit Tracker", "High-risk profile", "13 days, 1.28/wk, 77%", "High risk + light 15-min schedule", t_risk_high)
record("Habit Tracker", "Low-risk profile (contrast)", "1 day, 6/wk, 95%", "Low risk, no nudge", t_risk_low)
record("Habit Tracker", "Middle profile (informational)", "3 days, 3/wk, 70%", "Valid risk level returned", t_risk_mid)
record("Gym Buddy", "Negative message", "I feel tired and stressed today", "sentiment negative + reply", t_buddy("I feel tired and stressed today", "negative"))
record("Gym Buddy", "Positive message", "I feel great and motivated!", "sentiment positive + reply", t_buddy("I feel great and motivated!", "positive"))
record("Gym Buddy", "Negation handling", "I am not happy with my progress", "sentiment negative", t_buddy("I am not happy with my progress", "negative"))
record("Performance Analyzer", "Good session", "12 reps, 120 s, 10/12 good", "66.0 / 83.3% / Good", t_session_good)
record("Performance Analyzer", "Poor session (contrast)", "3 reps, 300 s, 1/5 good", "Needs Improvement", t_session_poor)
record("Smart Gym", "Sensor reading + matching advice", "GET /api/smart-gym-reading", "Advice matches heart-rate zone", t_smart)
record("Gym Recommender", "Beginner streak", "weight loss, streak 0", "3-Day Kickstart Challenge", t_recommend("weight loss", 0, "3-Day Kickstart"))
record("Gym Recommender", "Advanced streak", "muscle gain, streak 20", "30-Day Mastery Challenge", t_recommend("muscle gain", 20, "30-Day"))
record("Weekly Report", "Report from saved sessions", "GET /api/weekly-report", "200 + report fields", t_weekly)
record("Admin Analytics", "Summary endpoint", "GET /api/analytics/summary", "200 + totals", t_summary)
record("Backend API", "Input validation", "POST /api/diet-plan with {}", "422 validation error", t_validation)

# ----------------------------------------------------------------- output
lines = [f"# Test results — {BASE}", "",
         "| # | Module | Test | Input | Expected | Actual | Result |",
         "|---|--------|------|-------|----------|--------|--------|"]
for i, (m, t, inp, exp, act, res) in enumerate(rows, 1):
    lines.append(f"| {i} | {m} | {t} | {inp} | {exp} | {act} | {res} |")
passed = sum(1 for r in rows if r[-1] == "PASS")
lines += ["", f"**{passed}/{len(rows)} passed.**"]
out = "\n".join(lines)
print(out)
with open("test_results.md", "w", encoding="utf-8") as f:
    f.write(out + "\n")