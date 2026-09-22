import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Gym & Fitness Assistant", page_icon="🏋️", layout="wide")
st.title("🏋️ AI Gym & Fitness Assistant — Dashboard")

tabs = st.tabs(["🥗 Diet Coach", "📊 Behavior Risk", "💬 Gym Buddy", "⌚ Smart Gym", "🎯 Recommendations", "📈 Session Performance"])

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
    st.subheader("Smart Gym Assistant (Simulated IoT)")
    st.caption("Simulated sensor data — demonstrates the AI+IoT integration layer described in the project brief.")
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

    if st.button("Get Recommendations"):
        res = requests.post(f"{API_URL}/api/recommend", json={"goal": rec_goal, "current_streak_days": streak})
        if res.status_code == 200:
            data = res.json()
            st.write("**Recommended Programs:**")
            for p in data["programs"]:
                st.write(f"- {p}")
            st.write("**Nearby Gyms (demo data):**")
            for g in data["nearby_gyms"]:
                st.write(f"- {g['name']} — {g['distance_km']} km — ⭐ {g['rating']}")
            st.write(f"**Suggested Challenge:** {data['challenge']}")

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




