"""Login screen + 'My History & Privacy' page for the Streamlit dashboard."""
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "https://ai-gym-backend-bwiz.onrender.com")
TIMEOUT = 60  # Render's free tier can take ~50s to wake up

MODULES = {"Workout sessions": "sessions", "Skip-risk checks": "risk-checks",
           "Gym Buddy chats": "chats", "Meals": "meals"}


import base64
import re


def password_problems(password: str, username: str = "") -> list:
    """Strong-password rules (the backend checks the same rules)."""
    problems = []
    if len(password) < 8:
        problems.append("at least 8 characters")
    if not password[:1].isupper():
        problems.append("the first character must be an uppercase letter")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"[0-9]", password):
        problems.append("a digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("a special character such as @ # $ % ! ?")
    if username and len(username) >= 3 and username.lower() in password.lower():
        problems.append("it must not contain your username")
    return problems


_ECG_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="700" height="220" viewBox="0 0 700 220">'
            '<path d="M0 110 H130 L150 110 L170 70 L190 150 L215 25 L245 195 L268 110 H350 L372 92 L394 110 H700" '
            'fill="none" stroke="%s" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/></svg>')


def _ecg_url(color: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((_ECG_SVG % color).encode()).decode()


def _login_background(card: bool = True) -> str:
    """Full-page running background for the login screen (CSS only, no iframe).
    Put a clip at streamlit_dashboard/assets/login.mp4 (under 6 MB) to play it instead."""
    from sidebar_ui import _video_tag
    clip = _video_tag(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "login.mp4"))
    card_css = """
[data-testid="stColumn"]:nth-child(2), [data-testid="column"]:nth-child(2) {
    background:rgba(8,14,30,.80); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
    border:1px solid rgba(255,255,255,.18); border-radius:22px; padding:26px 28px !important;
    box-shadow:0 20px 60px rgba(0,0,0,.55); }
""" if card else ""
    tag = '<div class="tag">Train smart. <b>Stay consistent.</b></div>' if card else ""
    return f"""
<style>
.stApp {{ background:#050a16 !important; }}
header[data-testid="stHeader"] {{ background:transparent !important; }}
.block-container {{ position:relative; z-index:2; padding-top:7vh !important; max-width:1200px; }}
.login-bg {{ position:fixed; inset:0; z-index:0; overflow:hidden;
    background: radial-gradient(900px 600px at 85% 10%, rgba(34,211,238,.28), transparent 60%),
                radial-gradient(800px 600px at 10% 90%, rgba(198,255,61,.20), transparent 55%), #050a16; }}
.login-bg video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:.85; }}
.login-bg .ecg {{ position:absolute; left:0; right:0; height:220px; background-repeat:repeat-x; background-size:700px 220px; }}
.login-bg .e1 {{ top:12%; background-image:url({_ecg_url('#c6ff3d')}); animation:ecgmove 7s linear infinite; opacity:.9; }}
.login-bg .e2 {{ top:62%; background-image:url({_ecg_url('#22d3ee')}); animation:ecgmove 11s linear infinite; opacity:.6; }}
.login-bg .orb {{ position:absolute; width:380px; height:380px; border-radius:50%; filter:blur(70px); opacity:.35;
    background:#2563eb; animation:orbfloat 14s ease-in-out infinite alternate; }}
.login-bg .o1 {{ left:-80px; top:20%; }} .login-bg .o2 {{ right:-60px; bottom:5%; background:#c6ff3d; opacity:.18; animation-duration:18s; }}
.login-bg .tag {{ position:absolute; left:0; right:0; bottom:5%; text-align:center; font-weight:700; font-size:26px; color:#fff;
    text-shadow:0 2px 18px rgba(0,0,0,.6); }}
.login-bg .tag b {{ color:#c6ff3d; }}
@keyframes ecgmove {{ from {{ background-position-x:0; }} to {{ background-position-x:-700px; }} }}
@keyframes orbfloat {{ from {{ transform:translate(0,0); }} to {{ transform:translate(60px,-50px); }} }}
{card_css}

.lp-hero {{ text-align:center; padding:4vh 0 2vh; }}
.lp-hero h1 {{ font-size:clamp(34px,6vw,58px); font-weight:800; line-height:1.1; margin:0 0 14px; }}
.lp-hero h1 span {{ color:#c6ff3d; }}
.lp-hero p {{ font-size:clamp(16px,2.2vw,20px); color:#d6e0f5; max-width:760px; margin:0 auto 10px; }}
.lp-h2 {{ text-align:center; font-size:28px; font-weight:800; margin:44px 0 6px; color:#fff; }}
.lp-sub {{ text-align:center; color:#b4c2e0; margin-bottom:18px; }}
.lp-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; }}
.lp-card {{ background:rgba(8,14,30,.78); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
    border:1px solid rgba(255,255,255,.16); border-radius:18px; padding:20px; }}
.lp-card .ic {{ font-size:30px; }} .lp-card h3 {{ margin:8px 0 6px; font-size:19px; color:#fff; }}
.lp-card p {{ margin:0; color:#c9d5ee; font-size:15px; line-height:1.5; }}
.lp-step b {{ display:inline-block; width:34px; height:34px; line-height:34px; text-align:center; border-radius:50%;
    background:linear-gradient(135deg,#c6ff3d,#7dd957); color:#0a1200; margin-bottom:8px; }}
.lp-cta {{ text-align:center; margin:40px 0 10px; font-size:26px; font-weight:800; }}
.login-title {{ font-size:28px; font-weight:800; color:#fff; line-height:1.2; margin-bottom:6px; }}
.login-sub {{ color:#b4c2e0; font-size:14px; margin-bottom:14px; }}
</style>
<div class="login-bg">{clip}<div class="orb o1"></div><div class="orb o2"></div>
<div class="ecg e1"></div><div class="ecg e2"></div>
{tag}</div>
"""


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


def _sign_in(path: str, payload: dict, admin_only: bool = False):
    try:
        res = requests.post(f"{API_URL}{path}", json=payload, timeout=TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not reach the server: {exc}")
        return
    if res.status_code != 200:
        st.error(_detail(res))
        return
    data = res.json()
    st.session_state["token"] = data["token"]
    st.session_state["user"] = data["user"]
    st.session_state.pop("guest", None)
    st.session_state.pop("is_admin", None)
    if admin_only:
        try:
            ok = bool(requests.get(f"{API_URL}/api/admin/me", timeout=TIMEOUT).json().get("is_admin"))
        except Exception:  # noqa: BLE001
            ok = False
        if not ok:
            for k in ("token", "user"):
                st.session_state.pop(k, None)
            st.error("This account is not an admin account.")
            return
        st.session_state["is_admin"] = True
        st.session_state["view"] = "admin"
    else:
        st.session_state["view"] = "dashboard"
    st.rerun()


def _landing():
    """First page for visitors: what the app is, what it offers, and a Get started button."""
    from sidebar_ui import apply_readable_css
    apply_readable_css()
    st.markdown(_login_background(card=False), unsafe_allow_html=True)
    st.markdown(
        "<div class='lp-hero'><h1>Train smarter. Eat better.<br><span>Stay consistent.</span></h1>"
        "<p>AI Gym &amp; Fitness Assistant is your personal AI coach. It plans your diet, watches your form through your "
        "camera, chats like a workout buddy and warns you before you skip workouts.</p></div>",
        unsafe_allow_html=True)
    _a, c1, c2, _b = st.columns([1.2, 1.4, 1.4, 1.2])
    if c1.button("🚀 Get started: create account", use_container_width=True, key="lp_start"):
        st.session_state["auth_page"] = "auth"; st.session_state["auth_mode"] = "register"; st.rerun()
    if c2.button("Log in", use_container_width=True, key="lp_login"):
        st.session_state["auth_page"] = "auth"; st.session_state["auth_mode"] = "login"; st.rerun()

    _a, c5, _b = st.columns([1.2, 2.8, 1.2])
    if c5.button("🛠️ Admin login", use_container_width=True, key="lp_admin"):
        st.session_state["auth_page"] = "auth"; st.session_state["auth_mode"] = "admin"; st.rerun()

    st.markdown(
        "<div class='lp-h2'>Why fitness and diet go together</div>"
        "<div class='lp-sub'>Results come from small habits repeated every week.</div>"
        "<div class='lp-grid'>"
        "<div class='lp-card'><div class='ic'>🏋️</div><h3>Fitness</h3><p>Regular strength and cardio sessions build muscle, "
        "protect your heart, improve sleep and lift your mood. Good form keeps you injury free.</p></div>"
        "<div class='lp-card'><div class='ic'>🥗</div><h3>Diet</h3><p>Your body is built in the kitchen. The right calories, "
        "protein and balance for your goal (loss, gain or endurance) make every workout count.</p></div>"
        "<div class='lp-card'><div class='ic'>🔁</div><h3>Consistency</h3><p>The best plan is the one you follow. Tracking, "
        "reminders and a friendly buddy help you show up even on low days.</p></div></div>",
        unsafe_allow_html=True)

    st.markdown(
        "<div class='lp-h2'>What this app gives you</div>"
        "<div class='lp-sub'>Six AI tools in one dashboard.</div>"
        "<div class='lp-grid'>"
        "<div class='lp-card'><div class='ic'>🥗</div><h3>Diet Coach</h3><p>BMI, calorie guidance and an AI meal plan for your goal, plus a meal tracker.</p></div>"
        "<div class='lp-card'><div class='ic'>📊</div><h3>Behavior Risk</h3><p>Predicts if you are likely to skip workouts and suggests how to stay on track.</p></div>"
        "<div class='lp-card'><div class='ic'>💬</div><h3>Gym Buddy</h3><p>Chat or talk to an AI partner that understands your mood and replies in voice.</p></div>"
        "<div class='lp-card'><div class='ic'>⌚</div><h3>Smart Gym</h3><p>Heart-rate zones and recommended resistance and rest from equipment data.</p></div>"
        "<div class='lp-card'><div class='ic'>🎯</div><h3>Recommendations</h3><p>Workout programs, nearby gyms and challenges matched to your level.</p></div>"
        "<div class='lp-card'><div class='ic'>📈</div><h3>Live AI Trainer</h3><p>Use your laptop or phone camera. It counts reps, checks form and scores your session.</p></div>"
        "</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='lp-h2'>How it works</div><div class='lp-sub'>Ready in a minute.</div>"
        "<div class='lp-grid'>"
        "<div class='lp-card lp-step'><b>1</b><h3>Create your account</h3><p>Pick a username and a strong password, then add your basic details.</p></div>"
        "<div class='lp-card lp-step'><b>2</b><h3>Explore the tools</h3><p>Open any module from the Dashboard menu on the left.</p></div>"
        "<div class='lp-card lp-step'><b>3</b><h3>Track your progress</h3><p>Everything you do is saved privately in My History.</p></div></div>"
        "<div class='lp-cta'>Ready to explore? Let's get started.</div>", unsafe_allow_html=True)
    _a, c3, c4, _b = st.columns([1.2, 1.4, 1.4, 1.2])
    if c3.button("🚀 Create my account", use_container_width=True, key="lp_start2"):
        st.session_state["auth_page"] = "auth"; st.session_state["auth_mode"] = "register"; st.rerun()
    if c4.button("Continue as guest", use_container_width=True, key="lp_guest"):
        st.session_state["guest"] = True; st.session_state["view"] = "dashboard"; st.rerun()
    st.stop()


def require_login():
    """Shows the login/register screen until the user signs in (or continues as guest).
    When signed in, draws the left sidebar (welcome, quote, clip, menu, log out)."""
    _install_auth_header()
    from sidebar_ui import render_sidebar

    if st.session_state.get("token"):
        render_sidebar(guest=False)
        from profile_ui import profile_gate
        profile_gate()          # asks new users for their basic details; shows the profile page
        return
    if st.session_state.get("guest"):
        render_sidebar(guest=True)
        return

    if st.session_state.get("auth_page", "landing") == "landing":
        _landing()
    from sidebar_ui import apply_readable_css
    apply_readable_css()
    st.markdown(_login_background(card=True), unsafe_allow_html=True)
    _l, mid, _r = st.columns([1, 1.25, 1])
    with mid:
        st.markdown("<div class='login-title'>🏋️ AI Gym &amp; Fitness Assistant</div>"
                    "<div class='login-sub'>Log in to keep your own history. Your data stays private to your account.</div>",
                    unsafe_allow_html=True)
        _mode = st.session_state.get("auth_mode", "login")
        _order = {"register": ["Create account", "Log in", "🛠️ Admin login"],
                  "admin": ["🛠️ Admin login", "Log in", "Create account"]}.get(
                      _mode, ["Log in", "Create account", "🛠️ Admin login"])
        _tabs = dict(zip(_order, st.tabs(_order)))
        login_tab, register_tab, admin_tab = _tabs["Log in"], _tabs["Create account"], _tabs["🛠️ Admin login"]
        with login_tab:
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log in", use_container_width=True):
                    _sign_in("/auth/login", {"username": u, "password": p})
        with register_tab:
            with st.form("register_form"):
                name = st.text_input("Your name")
                u2 = st.text_input("Choose a username (letters, numbers, underscore)")
                p2 = st.text_input("Create a password", type="password")
                st.caption("Password rules: starts with an UPPERCASE letter, at least 8 characters, "
                           "with a lowercase letter, a digit and a special character (@ # $ % ! ?).")
                if st.form_submit_button("Create account", use_container_width=True):
                    problems = password_problems(p2, u2)
                    if problems:
                        st.error("Weak password. It needs:\n\n" + "\n".join(f"- ❌ {x}" for x in problems))
                    else:
                        _sign_in("/auth/register", {"username": u2, "password": p2, "display_name": name})
        with admin_tab:
            st.caption("For administrators only. Shows every user's performance.")
            with st.form("admin_form"):
                au = st.text_input("Admin username")
                ap = st.text_input("Admin password", type="password")
                if st.form_submit_button("Admin log in", use_container_width=True):
                    _sign_in("/auth/login", {"username": au, "password": ap}, admin_only=True)
        if st.button("Continue as guest", use_container_width=True):
            st.session_state["guest"] = True
            st.session_state["view"] = "dashboard"
            st.rerun()
        if st.button("← Back to home", use_container_width=True, key="back_home"):
            st.session_state["auth_page"] = "landing"
            st.rerun()
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
