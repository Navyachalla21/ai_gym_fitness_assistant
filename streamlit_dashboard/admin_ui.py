"""Admin page: every user's performance (shown only to admins)."""
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


def is_admin(api_url: str) -> bool:
    """Asks the backend once per login whether this user is an admin."""
    if "is_admin" not in st.session_state:
        ok = False
        if st.session_state.get("token"):
            try:
                ok = bool(requests.get(f"{api_url}/api/admin/me", timeout=20).json().get("is_admin"))
            except Exception:  # noqa: BLE001
                ok = False
        st.session_state["is_admin"] = ok
    return st.session_state["is_admin"]


def render_admin_users(api_url: str):
    st.subheader("🛠️ Admin: users and their performance")
    res = requests.get(f"{api_url}/api/admin/users", timeout=60)
    if res.status_code != 200:
        st.error(res.json().get("detail", res.text) if res.headers.get("content-type", "").startswith("application/json") else res.text)
        return
    df = pd.DataFrame(res.json()["users"])
    if df.empty:
        st.info("No users yet.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", len(df))
    c2.metric("Total sessions", int(df["sessions"].sum()))
    c3.metric("Total reps", int(df["total_reps"].sum()))
    avg = df["avg_score"].dropna()
    c4.metric("Average score", round(avg.mean(), 1) if len(avg) else "-")

    st.markdown("#### All users")
    st.dataframe(df.rename(columns={"member_id": "Member ID", "username": "Username", "name": "Name",
                                    "sessions": "Sessions", "total_reps": "Reps", "avg_score": "Avg score",
                                    "best_score": "Best", "last_session": "Last session",
                                    "risk_checks": "Risk checks", "chats": "Chats", "meals": "Meals"}),
                 use_container_width=True, hide_index=True)
    if len(avg):
        fig = px.bar(df.dropna(subset=["avg_score"]), x="username", y="avg_score", title="Average performance score per user")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### One user in detail")
    who = st.selectbox("Choose a user", df["username"].tolist())
    r = requests.get(f"{api_url}/api/admin/users/{who}/sessions", timeout=60)
    sess = pd.DataFrame(r.json().get("sessions", [])) if r.status_code == 200 else pd.DataFrame()
    if sess.empty:
        st.info("This user has no saved sessions yet.")
    else:
        if "performance_score" in sess and "created_at" in sess:
            st.plotly_chart(px.line(sess.sort_values("created_at"), x="created_at", y="performance_score",
                                    markers=True, title=f"{who}: performance over time"), use_container_width=True)
        st.dataframe(sess, use_container_width=True, hide_index=True)
    render_delete_controls(api_url, who)


def render_delete_controls(api_url: str, who: str):
    st.markdown("#### Delete data")
    st.caption("This removes the data from the database permanently.")
    sure = st.checkbox(f"I am sure I want to delete data of '{who}'", key=f"sure_{who}")
    c1, c2 = st.columns(2)
    if c1.button("🗑 Delete this user's data (keep account)", disabled=not sure, use_container_width=True, key=f"dd_{who}"):
        r = requests.delete(f"{api_url}/api/admin/users/{who}/data", timeout=60)
        st.success("Data deleted.") if r.status_code == 200 else st.error(r.text)
    if c2.button("⚠️ Delete user account and all data", disabled=not sure, use_container_width=True, key=f"da_{who}"):
        r = requests.delete(f"{api_url}/api/admin/users/{who}", timeout=60)
        if r.status_code == 200:
            st.success("User deleted.")
            st.rerun()
        else:
            st.error(r.text)
