"""Nutrition tracker section for the Diet Coach tab (Module 2): log meals, see intake vs target."""
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

TIMEOUT = 60  # Render's free tier can take ~50s to wake up


def _call(method, api_url, path, **kw):
    res = requests.request(method, f"{api_url}{path}", timeout=TIMEOUT, **kw)
    res.raise_for_status()
    return res.json()


def _log_meal(api_url, user_id):
    name = st.session_state.get("nt_meal_name", "").strip()
    if not name:
        st.session_state["nt_msg"] = ("error", "Enter a meal name first.")
        return
    try:
        _call("POST", api_url, "/api/meals", json={
            "meal_name": name, "calories": st.session_state.get("nt_calories", 0),
            "protein_g": st.session_state.get("nt_protein", 0), "user_id": user_id})
        st.session_state["nt_msg"] = ("success", f"Logged {name}.")
        st.session_state["nt_meal_name"] = ""
    except Exception as exc:  # noqa: BLE001
        st.session_state["nt_msg"] = ("error", f"Could not save the meal: {exc}")


def render_nutrition_tracker(api_url: str, weight_kg: float, height_cm: float, goal: str):
    st.divider()
    st.subheader("Nutrition tracker")
    st.caption("Log what you eat and compare it with your estimated daily calorie target.")

    user_id = st.text_input("User ID", "default", key="nt_user")

    try:
        target = _call("GET", api_url, "/api/calorie-target",
                       params={"weight_kg": weight_kg, "height_cm": height_cm, "goal": goal})
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load your calorie target from the backend: {exc}")
        return
    st.info(f"Estimated daily target for **{goal}**: **{target['target_calories']} kcal** "
            f"(maintenance about {target['maintenance_calories']} kcal). {target['note']}")

    c1, c2, c3, c4 = st.columns([3, 1.3, 1.3, 1])
    c1.text_input("Meal", key="nt_meal_name", placeholder="e.g. Veg biryani")
    c2.number_input("Calories", min_value=0, max_value=5000, value=400, step=10, key="nt_calories")
    c3.number_input("Protein (g)", min_value=0, max_value=500, value=15, step=1, key="nt_protein")
    c4.write("")
    c4.write("")
    c4.button("Log meal", on_click=_log_meal, args=(api_url, user_id))
    if st.session_state.get("nt_msg"):
        kind, text = st.session_state.pop("nt_msg")
        (st.success if kind == "success" else st.error)(text)

    try:
        summary = _call("GET", api_url, "/api/meals/summary",
                        params={"user_id": user_id, "target_calories": target["target_calories"], "days": 7})
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load your intake summary: {exc}")
        return

    today = summary["today"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Eaten today", f"{today['calories']} kcal")
    m2.metric("Target", f"{target['target_calories']} kcal")
    m3.metric("Remaining", f"{today['remaining']} kcal", today["status"], delta_color="off")
    st.progress(min(1.0, today["percent_of_target"] / 100), text=f"{today['percent_of_target']}% of today's target")
    st.caption(f"Protein today: {today['protein_g']} g")

    if today["meals"]:
        st.markdown("**Today's meals**")
        for meal in today["meals"]:
            a, b = st.columns([6, 1])
            a.write(f"{meal['meal_name']} — {meal['calories']:.0f} kcal, {meal['protein_g']:.0f} g protein")
            if b.button("Remove", key=f"del_{meal['id']}"):
                try:
                    _call("DELETE", api_url, f"/api/meals/{meal['id']}", params={"user_id": user_id})
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not remove it: {exc}")
    else:
        st.write("No meals logged today yet.")

    daily = pd.DataFrame(summary["daily"])
    if daily["calories"].sum() > 0:
        fig = go.Figure()
        fig.add_bar(x=daily["date"], y=daily["calories"], name="Eaten (kcal)")
        fig.add_hline(y=target["target_calories"], line_dash="dash", annotation_text="Target")
        fig.update_layout(title="Last 7 days", yaxis_title="kcal", margin=dict(t=40, b=10))
        st.plotly_chart(fig, width="stretch")
