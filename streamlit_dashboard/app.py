import os
import streamlit as st
import requests
from admin_analytics import render_admin_analytics
from nutrition_ui import render_nutrition_tracker

API_URL = os.getenv("API_URL", "https://ai-gym-backend-bwiz.onrender.com")

st.set_page_config(page_title="AI Gym & Fitness Assistant", page_icon="🏋️", layout="wide")
st.title("🏋️ AI Gym & Fitness Assistant — Dashboard")

tabs = st.tabs(["🥗 Diet Coach", "📊 Behavior Risk", "💬 Gym Buddy", "⌚ Smart Gym", "🎯 Recommendations", "📈 Session Performance", "🛠️ Admin Analytics"])

# --- Diet Coach ---
with tabs[0]:
    st.subheader("AI Dietician & Calorie Coach")
    col1, col2 = st.columns(2)
    weight = col1.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
    height = col2.number_input("Height (cm)", min_value=100.0, max_value=220.0, value=170.0)
    goal = st.selectbox("Goal", ["weight loss", "muscle gain", "endurance", "general fitness"])
    preferences = st.text_input("Dietary preferences (e.g., vegetarian, vegan, no restrictions)", "no restrictions")

    if st.button("Generate Diet Plan"):
        with st.spinner("Generating your plan..."):
            res = requests.post(f"{API_URL}/api/diet-plan", json={
                "weight_kg": weight, "height_cm": height, "goal": goal, "preferences": preferences
            })
            if res.status_code == 200:
                data = res.json()
                st.metric("BMI", data["bmi"], data["category"])
                st.markdown(data["plan"])
            else:
                st.error(f"Error: {res.text}")

    render_nutrition_tracker(API_URL, weight, height, goal)

# --- Behavior Risk ---
with tabs[1]:
    st.subheader("AI Fitness Habit Tracker")
    days = st.slider("Days since last workout", 0, 14, 2)
    weekly = st.slider("Average sessions per week", 0.0, 7.0, 4.0)
    completion = st.slider("Average session completion %", 0, 100, 85)

    if st.button("Predict Skip Risk"):
        res = requests.post(f"{API_URL}/api/behavior-risk", json={
            "days_since_last_workout": days,
            "weekly_avg_sessions": weekly,
            "avg_session_completion_pct": completion
        })
        if res.status_code == 200:
            data = res.json()
            col1, col2 = st.columns(2)
            col1.metric("Skip Risk", data["risk_level"], f"{data['skip_probability']*100:.0f}%")
            if data["nudge"]:
                col2.info(data["nudge"])
            sched = data.get("suggested_schedule")
            if sched:
                st.markdown("**Adjusted schedule**")
                s1, s2, s3 = st.columns(3)
                s1.metric("Intensity", sched["intensity"])
                s2.metric("Session length", f"{sched['session_length_min']} min")
                s3.metric("Target / week", sched["sessions_per_week_target"])
                for step in sched["plan"]:
                    st.write(f"- {step}")
                st.caption(sched["reminder"])
        else:
            st.error(f"Error: {res.text}")

# --- Gym Buddy Chat ---
with tabs[2]:
    st.subheader("Virtual Gym Buddy")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_msg = st.text_input("Talk to your gym buddy:", key="buddy_input")
    if st.button("Send") and user_msg:
        res = requests.post(f"{API_URL}/api/gym-buddy-chat", json={"message": user_msg})
        if res.status_code == 200:
            data = res.json()
            st.session_state.chat_history.append(("You", user_msg, None))
            st.session_state.chat_history.append(("Buddy", data["reply"], data["sentiment"]))

    for sender, msg, sentiment in st.session_state.chat_history:
        if sender == "You":
            st.write(f"**You:** {msg}")
        else:
            st.write(f"**Buddy** _(detected mood: {sentiment})_: {msg}")

# --- Smart Gym ---
with tabs[3]:
    st.subheader("Smart Gym Assistant (AI + IoT)")
    st.caption("Equipment publishes sensor data over MQTT; the backend reads it, recommends a resistance "
               "and rest time, and can send the new resistance back to the machine.")

    st.markdown("#### Live equipment (MQTT)")
    st.caption("To see real MQTT data, run `python ai_modules/iot_simulator.py` on your computer. "
               "With no machine publishing, the reading below is simulated and labelled as such.")

    if st.button("Get live reading"):
        try:
            res = requests.get(f"{API_URL}/api/smart-gym-live", timeout=60)
            res.raise_for_status()
            st.session_state["live_gym"] = res.json()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not get a reading: {exc}")

    live = st.session_state.get("live_gym")
    if live:
        if live["source"] == "mqtt":
            st.success("Source: real MQTT telemetry from the equipment")
        else:
            st.warning("Source: simulated reading (no equipment is publishing right now)")
        r, an = live["reading"], live["analysis"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Heart Rate", f"{r['heart_rate_bpm']} bpm", an["heart_rate_zone"] + " zone", delta_color="off")
        col2.metric("Resistance Level", r["resistance_level"])
        col3.metric("Equipment Status", r["equipment_status"])
        st.info(an["advice"])
        col4, col5 = st.columns(2)
        col4.metric("Recommended resistance", an["recommended_resistance"],
                    f"{an['recommended_resistance'] - an['current_resistance']:+d}", delta_color="off")
        col5.metric("Recommended rest", f"{an['recommended_rest_seconds']} s")

        if live["source"] == "mqtt" and an["recommended_resistance"] != an["current_resistance"]:
            if st.button("Apply recommended resistance to the machine"):
                try:
                    res = requests.post(f"{API_URL}/api/smart-gym-live/apply", timeout=60,
                                        json={"resistance_level": an["recommended_resistance"]})
                    res.raise_for_status()
                    st.success("Command sent. Get another reading in a few seconds to see the change.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not send the command: {exc}")
        with st.expander("Connection details"):
            st.json(live["mqtt"])

    st.divider()
    st.markdown("#### Quick simulated reading")
    if st.button("Get Live Sensor Reading"):
        res = requests.get(f"{API_URL}/api/smart-gym-reading")
        if res.status_code == 200:
            data = res.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Heart Rate", f"{data['reading']['heart_rate_bpm']} bpm")
            col2.metric("Resistance Level", data['reading']['resistance_level'])
            col3.metric("Equipment Status", data['reading']['equipment_status'])
            st.info(data["advice"])

# --- Recommendations ---
with tabs[4]:
    st.subheader("Gym Recommender & Planner")
    rec_goal = st.selectbox("Your goal", ["weight loss", "muscle gain", "endurance", "general fitness"], key="rec_goal")
    streak = st.number_input("Current streak (days)", min_value=0, value=5)
    rc1, rc2 = st.columns(2)
    rec_user = rc1.text_input("User ID (your workout history is used to pick your level)", "default", key="rec_user")
    level_choice = rc2.selectbox("Fitness level", ["Auto (from my workout history)", "beginner", "intermediate", "advanced"])

    loc_mode = st.radio("Location", ["Choose a city", "Enter coordinates", "Skip"], horizontal=True)
    rec_city, rec_lat, rec_lon = None, None, None
    if loc_mode == "Choose a city":
        try:
            cities = requests.get(f"{API_URL}/api/cities", timeout=60).json()["cities"]
        except Exception:  # noqa: BLE001
            cities = ["Bengaluru", "Mysuru", "Hyderabad", "Chennai", "Mumbai", "Pune", "Delhi"]
        rec_city = st.selectbox("City", cities)
    elif loc_mode == "Enter coordinates":
        lc1, lc2 = st.columns(2)
        rec_lat = lc1.number_input("Latitude", min_value=-90.0, max_value=90.0, value=12.9716, format="%.4f")
        rec_lon = lc2.number_input("Longitude", min_value=-180.0, max_value=180.0, value=77.5946, format="%.4f")

    if st.button("Get Recommendations"):
        payload = {"goal": rec_goal, "current_streak_days": int(streak), "user_id": rec_user,
                   "city": rec_city, "latitude": rec_lat, "longitude": rec_lon,
                   "fitness_level": None if level_choice.startswith("Auto") else level_choice}
        res = requests.post(f"{API_URL}/api/recommend-plus", json=payload, timeout=60)
        if res.status_code == 200:
            data = res.json()
            st.info(f"Fitness level: **{data['fitness_level']}** ({data['fitness_level_reason']})")
            st.write("**Recommended Programs:**")
            for p in data["programs"]:
                st.write(f"- {p}")
            st.write(f"**Nearby Gyms (demo data){' near ' + data['location_used'] if data['location_used'] else ''}:**")
            for g in data["nearby_gyms"]:
                where = f" ({g['city']})" if g.get("city") else ""
                st.write(f"- {g['name']}{where} — {g['distance_km']} km — ⭐ {g['rating']}")
            if data.get("location_note"):
                st.caption(data["location_note"])
            st.write(f"**Suggested Challenge:** {data['challenge']}")
        else:
            st.error(f"Error: {res.text}")

# --- Session Performance ---
with tabs[5]:
    st.subheader("Pose-to-Performance Analyzer")
    st.caption("Enter results from a completed AI Gym Trainer session (run pose_detector.py separately).")
    reps = st.number_input("Reps completed", min_value=0, value=12)
    duration = st.number_input("Session duration (seconds)", min_value=1, value=120)
    good_feedback_count = st.number_input("Number of 'Good rep!' feedbacks received", min_value=0, value=10)
    total_feedback_count = st.number_input("Total feedback events", min_value=1, value=12)

    if st.button("Analyze Session"):
        feedback_list = ["Good rep!"] * good_feedback_count + ["Adjust form"] * (total_feedback_count - good_feedback_count)
        res = requests.post(f"{API_URL}/api/analyze-session", json={
            "reps": reps, "duration_seconds": duration, "form_feedback_list": feedback_list
        })
        if res.status_code == 200:
            data = res.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Performance Score", data["performance_score"])
            col2.metric("Form Quality", f"{data['form_quality_pct']}%")
            col3.metric("Rating", data["rating"])

# --- Admin Analytics ---
with tabs[6]:
    render_admin_analytics(API_URL)
