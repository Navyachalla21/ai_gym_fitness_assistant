"""Login screen + 'My History & Privacy' page for the Streamlit dashboard."""
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "https://ai-gym-backend-bwiz.onrender.com")
TIMEOUT = 60  # Render's free tier can take ~50s to wake up

MODULES = {"Workout sessions": "sessions", "Skip-risk checks": "risk-checks",
           "Gym Buddy chats": "chats", "Meals": "meals"}


def _install_auth_header():
    """Adds 'Authorization: Bearer <token>' to every request sent to our API, so the existing
    tabs save and read the logged-in user's own data without any change."""
    if getattr(requests.Session, "_gym_auth_patched", False):
        return
    original = requests.Session.request

    def request(self, method, url, *args, **kwargs):
        try:
            token = st.session_state.get("token")
        except Exception:  # noqa: BLE001
            token = None
        if token and str(url).startswith(API_URL):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("Authorization", f"Bearer {token}")
            kwargs["headers"] = headers
        return original(self, method, url, *args, **kwargs)

    requests.Session.request = request
    requests.Session._gym_auth_patched = True


def _detail(res) -> str:
    try:
        return res.json().get("detail", res.text)
    except Exception:  # noqa: BLE001
        return res.text


def _sign_in(path: str, payload: dict):
    try:
        res = requests.post(f"{API_URL}{path}", json=payload, timeout=TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not reach the server: {exc}")
        return
    if res.status_code == 200:
        data = res.json()
        st.session_state["token"] = data["token"]
        st.session_state["user"] = data["user"]
        st.session_state["view"] = "dashboard"
        st.session_state.pop("guest", None)
        st.rerun()
    else:
        st.error(_detail(res))


def require_login():
    """Shows the login/register screen until the user signs in (or continues as guest).
    When signed in, draws the left sidebar (welcome, quote, clip, menu, log out)."""
    _install_auth_header()
    from sidebar_ui import render_sidebar

    if st.session_state.get("token"):
        render_sidebar(guest=False)
        return
    if st.session_state.get("guest"):
        render_sidebar(guest=True)
        return

    from sidebar_ui import apply_readable_css, banner
    apply_readable_css()
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.title("🏋️ AI Gym & Fitness Assistant")
        st.caption("Log in to keep your own history. Your data stays private to your account.")
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log in"):
                    _sign_in("/auth/login", {"username": u, "password": p})
        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Your name")
                u2 = st.text_input("Choose a username (letters, numbers, underscore)")
                p2 = st.text_input("Choose a password (min 8 characters)", type="password")
                if st.form_submit_button("Create account"):
                    _sign_in("/auth/register", {"username": u2, "password": p2, "display_name": name})
        if st.button("Continue as guest"):
            st.session_state["guest"] = True
            st.session_state["view"] = "dashboard"
            st.rerun()
    with right:
        # put your clip at assets/login.mp4 (under 6 MB); until then the running ECG animation is shown
        banner(520, 26, os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "login.mp4"))
    st.stop()


def _api(method: str, path: str, **kw):
    return requests.request(method, f"{API_URL}{path}", timeout=TIMEOUT, **kw)


def render_history_page():
    """Lists the user's saved records and lets them delete one, a whole module, or the account."""
    if not st.session_state.get("token"):
        st.info("Log in to see and manage your saved history.")
        return

    st.caption("Everything the app remembers about you. Deleted data is removed permanently "
               "and is not remembered anymore. Data you keep is remembered.")
    res = _api("GET", "/api/history")
    if res.status_code != 200:
        st.error(_detail(res))
        return
    counts = res.json()["counts"]
    cols = st.columns(len(MODULES))
    for col, (label, key) in zip(cols, MODULES.items()):
        col.metric(label, counts.get(key, 0))

    label = st.selectbox("Module", list(MODULES), key="hist_module")
    module = MODULES[label]
    res = _api("GET", f"/api/history/{module}")
    records = res.json()["records"] if res.status_code == 200 else []
    if not records:
        st.write("Nothing saved here yet.")
    else:
        st.dataframe(pd.DataFrame(records), width="stretch")
        ids = [r["id"] for r in records]
        pick = st.selectbox("Record id to delete", ids, key="hist_pick")
        if st.button("Delete this record", key="hist_del_one"):
            r = _api("DELETE", f"/api/history/{module}/{pick}")
            if r.status_code == 200:
                st.rerun()
            else:
                st.error(_detail(r))

        st.markdown("---")
        sure = st.checkbox(f"Yes, delete ALL my {label.lower()} permanently", key="hist_sure")
        if st.button(f"Delete all {label.lower()}", disabled=not sure, key="hist_del_all"):
            r = _api("DELETE", f"/api/history/{module}")
            if r.status_code == 200:
                st.rerun()
            else:
                st.error(_detail(r))

    st.markdown("---")
    st.markdown("**Delete my account and all my data**")
    pw = st.text_input("Enter your password to confirm", type="password", key="acct_pw")
    sure2 = st.checkbox("I understand this cannot be undone", key="acct_sure")
    if st.button("Delete my account", disabled=not (pw and sure2), key="acct_del"):
        r = _api("POST", "/api/account/delete", json={"password": pw})
        if r.status_code == 200:
            for key in ("token", "user", "guest", "view"):
                st.session_state.pop(key, None)
            st.rerun()
        else:
            st.error(_detail(r))
