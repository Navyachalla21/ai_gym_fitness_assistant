"""Left sidebar (welcome, quote, running clip, navigation) and the 'How to use' manual."""
import base64
import datetime
import os

import streamlit as st
import streamlit.components.v1 as components

_HERE = os.path.dirname(os.path.abspath(__file__))
_VIDEO = os.path.join(_HERE, "assets", "hero.mp4")   # optional real clip; animation is used if it is missing
_MAX_VIDEO_BYTES = 6 * 1024 * 1024

QUOTES = [
    "Small steps every day beat big plans someday.",
    "You don't have to be extreme, just consistent.",
    "Your only competition is who you were yesterday.",
    "Strong is built one rep at a time.",
    "Show up today. Future you will say thank you.",
    "Progress, not perfection.",
    "The hardest rep is the first step through the door.",
    "Sweat now, shine later.",
    "Rest when you must, but never quit.",
    "Your body can do it. It's your mind you have to convince.",
    "Discipline is choosing what you want most over what you want now.",
    "A good workout is the one you actually did.",
]


def quote_of_the_day() -> str:
    return QUOTES[datetime.date.today().toordinal() % len(QUOTES)]


@st.cache_data(show_spinner=False)
def _video_tag(path: str = "") -> str:
    path = path or _VIDEO
    try:
        if os.path.isfile(path) and os.path.getsize(path) <= _MAX_VIDEO_BYTES:
            with open(path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode()
            return f'<video autoplay muted loop playsinline src="data:video/mp4;base64,{b64}"></video>'
    except OSError:
        pass
    return ""


_BANNER = """
<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0}html,body{height:100%}body{background:transparent;font-family:Arial,sans-serif}
.box{position:relative;height:100vh;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.12);
 background:linear-gradient(120deg,#070b14,#0b1f2a 60%,#10243a)}
video,canvas{position:absolute;inset:0;width:100%;height:100%}video{object-fit:cover;opacity:.55}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,11,20,.15),rgba(7,11,20,.7))}
.t{position:absolute;left:16px;bottom:14px;color:#fff;font-weight:700;font-size:__FS__px;letter-spacing:.02em}
.t span{color:#c6ff3d}
</style></head><body><div class="box">__VIDEO__<canvas id="c"></canvas><div class="shade"></div>
<div class="t">Train smart. <span>Stay consistent.</span></div></div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');let W,H;
function size(){const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W;cv.height=H}
size();window.addEventListener('resize',size);
const P=[];for(let i=0;i<24;i++)P.push({x:Math.random(),y:Math.random(),s:.4+Math.random()*1.4,v:.02+Math.random()*.05,c:Math.random()>.5?'198,255,61':'34,211,238'});
const pts=[[0,0],[.12,0],[.16,-8],[.20,0],[.30,0],[.33,10],[.37,-58],[.41,32],[.44,0],[.58,0],[.64,-14],[.72,0],[1,0]];
function ecg(t){t=((t%1)+1)%1;for(let i=1;i<pts.length;i++){if(t<=pts[i][0]){const a=pts[i-1],b=pts[i],k=(t-a[0])/(b[0]-a[0]);return a[1]+(b[1]-a[1])*k}}return 0}
const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function frame(ts){const t=ts/1000;ctx.clearRect(0,0,W,H);
 for(let i=0;i<2;i++){const p=((t*.3+i/2)%1);ctx.beginPath();ctx.arc(W*.82,H*.4,14+p*W*.45,0,6.283);ctx.strokeStyle='rgba(34,211,238,'+(.28*(1-p))+')';ctx.stroke()}
 for(const p of P){p.y-=p.v*.016;if(p.y<0){p.y=1;p.x=Math.random()}ctx.beginPath();ctx.arc(p.x*W,p.y*H,p.s,0,6.283);ctx.fillStyle='rgba('+p.c+',.6)';ctx.fill()}
 const base=H*.5,amp=H*.32,period=190,off=t*90;
 const g=ctx.createLinearGradient(0,0,W,0);g.addColorStop(0,'rgba(198,255,61,.1)');g.addColorStop(.5,'rgba(198,255,61,.95)');g.addColorStop(1,'rgba(34,211,238,.95)');
 ctx.beginPath();for(let x=0;x<=W;x+=2){const y=base+ecg((x+off)/period)*amp/58;x?ctx.lineTo(x,y):ctx.moveTo(x,y)}
 ctx.strokeStyle=g;ctx.lineWidth=2;ctx.shadowColor='rgba(198,255,61,.9)';ctx.shadowBlur=10;ctx.stroke();ctx.shadowBlur=0;
 if(!reduce)requestAnimationFrame(frame)}
requestAnimationFrame(frame);
</script></body></html>
"""


MODULE_NAMES = ["🥗 Diet Coach", "📊 Behavior Risk", "💬 Gym Buddy", "⌚ Smart Gym",
                "🎯 Recommendations", "📈 Session Performance", "🛠️ Admin Analytics"]

_READABLE_CSS = """
<style>
/* ORIGINAL dark neon look; only fixes: text always bright white, typed text visible */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span,
.stApp div[data-testid="stMarkdownContainer"] { color:#f1f5ff; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color:#ffffff !important; background:none !important;
    -webkit-text-fill-color:#ffffff !important; opacity:1 !important; }
.stApp [data-testid="stCaptionContainer"], .stApp small { color:#b4c2e0 !important; }
section[data-testid="stSidebar"] { background:#0b1220 !important; border-right:1px solid rgba(255,255,255,.10); }
section[data-testid="stSidebar"] * { color:#f1f5ff; }
section[data-testid="stSidebar"] [data-testid="stExpander"] { border:1px solid rgba(255,255,255,.14); border-radius:14px;
    background:rgba(255,255,255,.04); }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary p { font-weight:700; }
.stApp .stButton > button p, .stApp .stFormSubmitButton > button p { color:#0a1200 !important; font-weight:700; }
.stApp .stButton > button:disabled p { color:#8793ad !important; }
section[data-testid="stSidebar"] .stButton > button:disabled { background:#16324a !important; border:1px solid #22d3ee !important; }
section[data-testid="stSidebar"] .stButton > button:disabled p { color:#bff4ff !important; font-weight:700; }
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricValue"] * { color:#c6ff3d !important; }
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricLabel"] * { color:#d6e0f5 !important; }
/* inputs: dark boxes, white text */
.stApp div[data-testid="stTextInputRootElement"], .stApp div[data-testid="stNumberInputContainer"],
.stApp div[data-baseweb="input"], .stApp div[data-baseweb="base-input"], .stApp div[data-baseweb="textarea"],
.stApp div[data-baseweb="select"] > div { background:#0f1729 !important; border-color:rgba(255,255,255,.28) !important; }
.stApp input, .stApp textarea { background:#0f1729 !important; color:#ffffff !important;
    -webkit-text-fill-color:#ffffff !important; caret-color:#c6ff3d !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color:#8d9bbd !important; -webkit-text-fill-color:#8d9bbd !important; }
.stApp div[data-baseweb="select"] * { color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
.stApp [data-testid="stNumberInput"] button { background:#1b2742 !important; }
.stApp [data-testid="stNumberInput"] button svg { fill:#ffffff !important; }
</style>
"""


def apply_readable_css():
    st.markdown(_READABLE_CSS, unsafe_allow_html=True)


def banner(height: int = 160, font: int = 15, video_path: str = ""):
    """The running ECG animation (or a real clip when a video file exists)."""
    tag = _video_tag(video_path) if video_path else _video_tag()
    components.html(_BANNER.replace("__VIDEO__", tag).replace("__FS__", str(font)), height=height)


def render_clip_row():
    """Small running clip under the page title (the single manual lives in the left menu)."""
    banner(150, 16)


def _go(view: str):
    st.session_state["view"] = view


def _pick(i: int):
    st.session_state["view"] = "dashboard"
    st.session_state["module"] = i


def _logout():
    for key in ("token", "user", "guest", "view", "module"):
        st.session_state.pop(key, None)


def _leave_guest():
    for key in ("guest", "view", "module"):
        st.session_state.pop(key, None)


def render_sidebar(guest: bool = False):
    """Welcome + quote, then Dashboard (7 core modules), My History, How to use, Log out."""
    apply_readable_css()
    view = st.session_state.get("view", "dashboard")
    current = st.session_state.get("module", 0)
    with st.sidebar:
        banner(110, 13)
        if guest:
            st.markdown("### Welcome, guest! 👋")
        else:
            user = st.session_state.get("user", {}) or {}
            name = user.get("display_name") or user.get("username") or "Athlete"
            st.markdown(f"### Welcome, {name}! 👋")
        st.markdown(f"*“{quote_of_the_day()}”*")
        st.divider()

        with st.expander("🏠 Dashboard", expanded=(view == "dashboard")):
            for i, label in enumerate(MODULE_NAMES):
                st.button(label, key=f"mod_{i}", on_click=_pick, args=(i,), width="stretch",
                          disabled=(view == "dashboard" and current == i))
        if not guest:
            st.button("🗂 My History", on_click=_go, args=("history",), width="stretch", disabled=(view == "history"))
        st.button("📖 User manual", on_click=_go, args=("guide",), width="stretch", disabled=(view == "guide"))

        st.divider()
        if guest:
            st.caption("Guest mode: data is shared and not private.")
            st.button("Log in / Register", on_click=_leave_guest, width="stretch")
        else:
            st.button("Log out", on_click=_logout, width="stretch")


def render_guide():
    """Step-by-step manual for every module."""
    st.header("📖 How to use the AI Gym & Fitness Assistant")
    st.caption("A quick manual for every module. Open a section to read it.")

    st.subheader("Quick start")
    st.markdown("""
1. **Create an account** (or log in). Your data is private to your account.
2. Open **🏠 Dashboard** in the left menu. It lists the **7 core modules**. Click one to open it.
3. Fill in the fields and press the button in that module.
4. Everything you save is remembered. Open **🗂 My History** in the left menu to see it, or delete it.
5. Use **Log out** at the bottom of the left menu when you finish.
""")

    st.subheader("The modules")

    with st.expander("🥗 Diet Coach and Nutrition Tracker", expanded=True):
        st.markdown("""
**What it does:** builds a diet plan for your goal and tracks what you eat.

**How to use it**
1. Enter your **weight (kg)** and **height (cm)**.
2. Choose your **goal**: weight loss, muscle gain, endurance or general fitness.
3. Type any **dietary preference** (for example vegetarian, vegan, no restrictions).
4. Press **Generate Diet Plan**. You get your **BMI**, its category and an AI meal plan.

**Nutrition tracker (below the plan)**
1. It shows your **estimated daily calorie target** for your goal.
2. Type the **meal name**, **calories** and **protein**, then press **Log meal**.
3. The bar shows how much of today's target you have eaten and how many calories remain.
4. Press **Remove** next to a meal if you logged it by mistake.
5. The chart shows your last 7 days against the target line.
""")

    with st.expander("📊 Behavior Risk (skip prediction)"):
        st.markdown("""
**What it does:** predicts how likely you are to skip your next workout and adjusts your plan.

**How to use it**
1. Move the three sliders: **days since your last workout**, **average sessions per week** and **average session completion %**.
2. Press **Predict Skip Risk**.
3. You see the **risk level** (Low, Medium or High) with the probability, a friendly **nudge**, and an **adjusted schedule**:
   intensity, session length, target sessions per week and a short plan.
4. High risk gives an easier restart plan. Low risk makes the plan more challenging.

Each check is saved, so your risk history appears in **My History**.
""")

    with st.expander("💬 Gym Buddy (chat)"):
        st.markdown("""
**What it does:** a friendly AI workout partner that notices your mood and remembers your recent chat.

**How to use it**
1. Type a message, for example how you feel today or what you want to train.
2. Press **Send**. The buddy replies and shows the **detected mood** (positive, neutral or negative).
3. If you feel low, it suggests one tiny step. If you feel great, it keeps your momentum going.
4. Your chats are saved. The **mood trend** appears in Admin Analytics, and the messages in **My History**.
""")

    with st.expander("⌚ Smart Gym (equipment and heart rate)"):
        st.markdown("""
**What it does:** reads gym-equipment data (heart rate, resistance, status) and recommends a resistance level and rest time.

**How to use it**
1. Press **Get live reading**. If a machine is publishing over MQTT you see real data.
   If not, a **simulated reading** is shown and clearly labelled.
2. Read the **heart-rate zone**, the **advice**, the **recommended resistance** and the **recommended rest**.
3. With real equipment connected, press **Apply recommended resistance to the machine** to send the change.
4. **Get Live Sensor Reading** (lower section) gives a quick simulated reading for a demo.

For a demo with data, run `python ai_modules/iot_simulator.py` on your computer.
""")

    with st.expander("🎯 Recommendations"):
        st.markdown("""
**What it does:** suggests workout programs, nearby gyms and a challenge that fits your goal.

**How to use it**
1. Choose your **goal** and enter your **current streak** in days.
2. **Fitness level**: leave it on *Auto* to use your saved workout history, or choose beginner, intermediate or advanced.
3. Pick a **location**: choose a city, enter coordinates, or skip.
4. Press **Get Recommendations**. You get your fitness level with the reason, recommended programs,
   nearby gyms (demo data) and a suggested challenge.
""")

    with st.expander("📈 Session Performance and the AI Trainer"):
        st.markdown("""
**What it does:** scores a finished workout from your reps, pace and form.

**Step 1: do the workout with the AI Trainer** (on a computer with a webcam)
1. Run the trainer: `python ai_modules/pose_detector.py`.
2. Stand where the camera can see your whole body and do your reps.
3. The trainer counts reps, checks your form and can coach you by voice.

**Step 2: score it here**
1. Enter **reps completed** and **session duration** in seconds.
2. Enter how many **'Good rep!'** feedbacks you received and the **total feedback events**.
3. Press **Analyze Session**. You get a **performance score**, **form quality %** and a **rating**.

Each session is saved and feeds your weekly report and level detection.
""")

    with st.expander("🛠️ Admin Analytics (charts and weekly report)"):
        st.markdown("""
**What it does:** shows your progress as charts.

**How to use it**
1. Choose the **period** (7, 14, 30 or 90 days).
2. Read the headline numbers: sessions, total reps, average score and recent mood.
3. Explore the **weekly report**, sessions per week, performance and form quality, skip-risk distribution and mood over time.
4. Open **Raw data** to see the underlying records.

The charts fill up as you use the other tabs. Logged-in users always see their own data.
""")

    with st.expander("🗂 My History and privacy"):
        st.markdown("""
**What it does:** shows everything the app remembers about you, and lets you remove it.

**How to use it**
1. Open **🗂 My History** in the left menu.
2. Pick a module: workout sessions, skip-risk checks, Gym Buddy chats or meals.
3. **Delete one record:** choose its id and press **Delete this record**.
4. **Delete a whole module:** tick the confirmation box, then press **Delete all**.
5. **Delete your account:** enter your password and confirm. Your account and all data are removed permanently.

Deleted data is gone for good and is not remembered. Data you keep is remembered every time you log in.
""")

    with st.expander("💡 Tips and common questions"):
        st.markdown("""
- **The first action is slow.** The free server can take up to a minute to wake up. Please wait.
- **Is my data private?** Yes. Each account sees only its own data. Guest mode uses shared data that is not private.
- **Why do I see no charts?** Use the other modules first (for example Behavior Risk or Session Performance). Charts appear once data is saved.
- **Forgot to log out on a shared computer?** Press **Log out** in the left menu.
- **Also on your computer:** the voice coach and the heart-rate monitor run beside the AI Trainer.
""")
