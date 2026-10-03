"""Admin Dashboard & Analytics tab (Plotly) for the Streamlit app."""
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

TIMEOUT = 60  # Render's free tier can take ~50s to wake up


def _get(api_url: str, path: str, **params):
    res = requests.get(f"{api_url}{path}", params=params, timeout=TIMEOUT)
    res.raise_for_status()
    return res.json()


def _seed_demo(api_url: str):
    try:
        requests.post(f"{api_url}/api/analytics/seed-demo", timeout=TIMEOUT).raise_for_status()
        st.session_state["adm_user"] = "demo"
        st.session_state["adm_msg"] = "Demo data loaded under User ID 'demo'."
    except Exception as exc:  # noqa: BLE001
        st.session_state["adm_msg"] = f"Could not load demo data: {exc}"


def render_admin_analytics(api_url: str):
    st.subheader("Admin Dashboard & Analytics")
    st.caption("Usage history across modules. Charts are built with Plotly from the saved session, "
               "risk-check and chat data.")

    st.session_state.setdefault("adm_user", "default")
    c1, c2, c3 = st.columns([2, 1, 1])
    user_id = c1.text_input("User ID", key="adm_user")
    days = c2.selectbox("Period (days)", [7, 14, 30, 90], index=2, key="adm_days")
    c3.write("")
    c3.button("Load demo data", on_click=_seed_demo, args=(api_url,))
    if st.session_state.get("adm_msg"):
        st.info(st.session_state.pop("adm_msg"))

    try:
        summary = _get(api_url, "/api/analytics/summary", user_id=user_id, days=days)
        sessions = _get(api_url, "/api/analytics/sessions", user_id=user_id, days=days)["sessions"]
        risks = _get(api_url, "/api/analytics/risks", user_id=user_id, days=days)["risk_checks"]
        mood = _get(api_url, "/api/analytics/mood", user_id=user_id)
        weekly = _get(api_url, "/api/weekly-report", user_id=user_id, days=7)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load analytics from the backend: {exc}")
        return

    # ---- headline numbers
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sessions", summary["total_sessions"])
    k2.metric("Total reps", summary["total_reps"])
    avg = summary["average_performance_score"]
    k3.metric("Avg performance score", avg if avg is not None else "—")
    k4.metric("Recent mood", mood["recent_mood"])

    if not (sessions or risks or mood["points"]):
        st.warning("No data for this user yet. Run a session, use the other tabs, "
                   "or click 'Load demo data'.")
        return

    # ---- weekly report
    st.markdown("#### Weekly progress report (last 7 days)")
    if weekly.get("sessions_this_week"):
        st.success(weekly["summary"])
        w1, w2, w3 = st.columns(3)
        w1.metric("Best score", weekly["best_performance_score"])
        w2.metric("Avg form quality", f"{weekly['average_form_quality_pct']}%")
        w3.metric("Trend", weekly["trend"])
        daily = pd.DataFrame(weekly["daily_breakdown"])
        fig = px.bar(daily, x="date", y="avg_score", text="sessions",
                     labels={"avg_score": "Avg score", "date": "Date", "sessions": "Sessions"})
        fig.update_traces(texttemplate="%{text} session(s)", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write(weekly.get("message", "No sessions in the last 7 days."))

    left, right = st.columns(2)

    # ---- performance over time
    with left:
        st.markdown("#### Performance score per session")
        if sessions:
            df = pd.DataFrame(sessions)
            df["created_at"] = pd.to_datetime(df["created_at"])
            fig = px.line(df, x="created_at", y="performance_score", markers=True,
                          labels={"created_at": "Date", "performance_score": "Score"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No sessions yet.")

    # ---- form quality
    with right:
        st.markdown("#### Form quality per session (%)")
        if sessions:
            fig = px.area(df, x="created_at", y="form_quality_pct",
                          labels={"created_at": "Date", "form_quality_pct": "Form quality %"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No sessions yet.")

    left, right = st.columns(2)

    # ---- skip-risk distribution
    with left:
        st.markdown("#### Skip-risk distribution")
        dist = summary["risk_distribution"]
        if dist:
            order = [lvl for lvl in ("Low", "Medium", "High") if lvl in dist]
            fig = px.bar(x=order, y=[dist[o] for o in order], labels={"x": "Risk level", "y": "Checks"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No risk checks yet.")

    # ---- mood over time
    with right:
        st.markdown("#### Mood over time (Gym Buddy)")
        if mood["points"]:
            mdf = pd.DataFrame(mood["points"])
            mdf["time"] = pd.to_datetime(mdf["time"])
            fig = px.line(mdf, x="time", y="score", markers=True,
                          labels={"time": "Time", "score": "Mood (-1 negative … +1 positive)"})
            fig.update_yaxes(range=[-1.2, 1.2], dtick=1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No chat messages yet.")

    with st.expander("Raw data"):
        if sessions:
            st.write("Sessions")
            st.dataframe(pd.DataFrame(sessions), use_container_width=True)
        if risks:
            st.write("Risk checks")
            st.dataframe(pd.DataFrame(risks), use_container_width=True)
