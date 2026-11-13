"""First-login profile setup and the 'My Profile' page."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "https://ai-gym-backend-bwiz.onrender.com")
TIMEOUT = 60

GENDERS = ["Female", "Male", "Other", "Prefer not to say"]
GOALS = ["Stay fit", "Lose weight", "Build muscle", "Improve stamina", "Gain weight"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
DIETS = ["Vegetarian", "Non-vegetarian", "Eggetarian", "Vegan"]


def _detail(res):
    try:
        d = res.json().get("detail", res.text)
        return d if isinstance(d, str) else "Please check the values you entered."
    except Exception:  # noqa: BLE001
        return res.text


def load_profile(force: bool = False):
    """Fetches the profile once per login and keeps it in session_state."""
    if not st.session_state.get("token"):
        return None
    if force or not st.session_state.get("profile_checked"):
        try:
            res = requests.get(f"{API_URL}/api/profile", timeout=TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                st.session_state["profile"] = data.get("profile")
                st.session_state["member_id"] = data.get("member_id")
                st.session_state["profile_checked"] = True
        except Exception:  # noqa: BLE001
            pass   # server asleep: try again on the next click, never block the app
    return st.session_state.get("profile")


def _form(existing, first_time: bool):
    p = existing or {}
    user = st.session_state.get("user", {}) or {}

    def pick(options, value, default=0):
        return options.index(value) if value in options else default

    with st.form("profile_form"):
        name = st.text_input("Full name", value=p.get("full_name") or user.get("display_name") or "")
        c1, c2 = st.columns(2)
        age = c1.number_input("Age", min_value=10, max_value=100, value=int(p.get("age") or 22))
        gender = c2.selectbox("Gender", GENDERS, index=pick(GENDERS, p.get("gender")))
        c3, c4 = st.columns(2)
        height = c3.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=float(p.get("height_cm") or 165.0))
        weight = c4.number_input("Weight (kg)", min_value=25.0, max_value=300.0, value=float(p.get("weight_kg") or 60.0))
        c5, c6 = st.columns(2)
        goal = c5.selectbox("Main goal", GOALS, index=pick(GOALS, p.get("goal")))
        level = c6.selectbox("Fitness level", LEVELS, index=pick(LEVELS, p.get("fitness_level")))
        c7, c8 = st.columns(2)
        per_week = c7.number_input("Workouts per week", min_value=0, max_value=14, value=int(p.get("workouts_per_week") or 3))
        diet = c8.selectbox("Diet preference", DIETS, index=pick(DIETS, p.get("diet_pref")))
        injuries = st.text_input("Injuries or limits (optional)", value=p.get("injuries") or "", max_chars=200)
        saved = st.form_submit_button("Save profile and continue" if first_time else "Save changes")

    if saved:
        if not name.strip():
            st.error("Please enter your name.")
            return
        body = {"full_name": name.strip(), "age": int(age), "gender": gender, "height_cm": float(height),
                "weight_kg": float(weight), "goal": goal, "fitness_level": level,
                "workouts_per_week": int(per_week), "diet_pref": diet, "injuries": injuries.strip()}
        try:
            res = requests.put(f"{API_URL}/api/profile", json=body, timeout=TIMEOUT)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not reach the server: {exc}")
            return
        if res.status_code == 200:
            data = res.json()
            st.session_state["profile"] = data["profile"]
            st.session_state["member_id"] = data.get("member_id")
            st.session_state["profile_checked"] = True
            st.session_state["view"] = "dashboard"
            st.rerun()
        else:
            st.error(_detail(res))


def render_profile_page():
    p = load_profile()
    mid = st.session_state.get("member_id") or "-"
    st.markdown("## 👤 My Profile")
    st.caption(f"Your member ID: **{mid}**   |   Username: **{(st.session_state.get('user') or {}).get('username', '-')}**")
    if p:
        bmi = round(p["weight_kg"] / ((p["height_cm"] / 100) ** 2), 1)
        c1, c2, c3 = st.columns(3)
        c1.metric("BMI", bmi)
        c2.metric("Max heart rate", f"{220 - int(p['age'])} bpm")
        c3.metric("Goal", p["goal"])
    st.markdown("### Edit your details")
    _form(p, first_time=False)


def profile_gate():
    """Call right after the sidebar is drawn for a logged-in user.
    New users are asked for their basic details first. Returns after st.stop() when it showed a page."""
    if not st.session_state.get("token"):
        return
    p = load_profile()
    if p is None and st.session_state.get("profile_checked") and not st.session_state.get("profile_skip"):
        mid = st.session_state.get("member_id") or ""
        st.markdown("## 🎉 Welcome! Let's set up your profile")
        st.caption(f"Your member ID is **{mid}**. These basic details personalise your plans and heart zones. "
                   "You can change them any time under My Profile.")
        _form(None, first_time=True)
        if st.button("Skip for now"):
            st.session_state["profile_skip"] = True
            st.rerun()
        st.stop()
    if st.session_state.get("view") == "profile":
        render_profile_page()
        st.stop()
