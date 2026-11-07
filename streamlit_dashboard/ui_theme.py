"""Dark 'neon gym' theme + animated hero banner for the Streamlit dashboard (look only, no logic).

Optional real video: put a short MP4 (under ~6 MB) at  streamlit_dashboard/assets/hero.mp4
and it plays muted and looping behind the banner.
"""
import base64
import os

import streamlit as st
import streamlit.components.v1 as components

_HERE = os.path.dirname(os.path.abspath(__file__))
_VIDEO = os.path.join(_HERE, "assets", "hero.mp4")
_MAX_VIDEO_BYTES = 6 * 1024 * 1024

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');
:root { --bg:#070b14; --card:rgba(255,255,255,.045); --line:rgba(255,255,255,.09);
        --lime:#c6ff3d; --cyan:#22d3ee; --text:#e8eefc; --muted:#93a0bb; }
html, body, [class*="css"], .stApp { font-family:'Inter',sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 85% -10%, rgba(34,211,238,.13), transparent 60%),
                     radial-gradient(900px 500px at -10% 10%, rgba(198,255,61,.08), transparent 55%), var(--bg);
         color: var(--text); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1200px; }
h1, h2, h3, h4 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.01em; color: var(--text); }
h3 { border-left: 4px solid var(--lime); padding-left:.6rem; }
p, label, span, li, div[data-testid="stMarkdownContainer"] { color: var(--text); }
[data-testid="stCaptionContainer"], .stCaption, small { color: var(--muted) !important; }

/* tabs as pills */
.stTabs [data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid var(--line); padding-bottom:.4rem; flex-wrap:wrap; }
.stTabs [data-baseweb="tab"] { background: var(--card); border:1px solid var(--line); border-radius:999px;
        padding:.35rem 1rem; color: var(--muted); transition: all .2s ease; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text); border-color: rgba(198,255,61,.5); transform: translateY(-1px); }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, var(--lime), #7dd957) !important;
        color:#0a1200 !important; border-color: transparent !important; font-weight:600; box-shadow:0 0 18px rgba(198,255,61,.35); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

/* glass metric cards */
[data-testid="stMetric"] { background: var(--card); border:1px solid var(--line); border-radius:16px;
        padding:.9rem 1rem; backdrop-filter: blur(8px); transition: transform .2s ease, border-color .2s ease; }
[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: rgba(34,211,238,.55); }
[data-testid="stMetricValue"] { font-family:'Space Grotesk',sans-serif; color: var(--lime); }
[data-testid="stMetricLabel"] { color: var(--muted); }

/* buttons */
.stButton > button, .stFormSubmitButton > button { background: linear-gradient(135deg, var(--lime), #7dd957); color:#0a1200;
        border:0; border-radius:12px; font-weight:600; padding:.5rem 1.2rem; transition: all .2s ease; }
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px) scale(1.02);
        box-shadow:0 8px 24px rgba(198,255,61,.35); color:#0a1200; }
.stButton > button:disabled { background: #2a3347; color:#6b7a99; box-shadow:none; transform:none; }

/* inputs */
[data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="textarea"] { background: rgba(255,255,255,.05) !important;
        border:1px solid var(--line) !important; border-radius:12px !important; color: var(--text); }
input, textarea { color: var(--text) !important; }
[data-baseweb="input"]:focus-within > div, [data-baseweb="select"]:focus-within > div { border-color: var(--cyan) !important;
        box-shadow:0 0 0 3px rgba(34,211,238,.18); }

/* alerts, tables, expanders, sidebar */
[data-testid="stAlert"] { border-radius:14px; border:1px solid var(--line); background: var(--card); }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
[data-testid="stExpander"] { background: var(--card); border:1px solid var(--line); border-radius:16px; }
[data-testid="stSidebar"] { background:#0a1020; border-right:1px solid var(--line); }
hr { border-color: var(--line); }
.stProgress > div > div > div > div { background: linear-gradient(90deg, var(--cyan), var(--lime)); }
iframe { border:0; }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
</style>
"""

_HERO = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Space+Grotesk:wght@700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0}
body{background:transparent;font-family:'Inter',sans-serif}
.hero{position:relative;height:250px;border-radius:22px;overflow:hidden;border:1px solid rgba(255,255,255,.1);
  background:linear-gradient(120deg,#070b14 0%,#0b1f2a 55%,#10243a 100%);box-shadow:0 20px 60px rgba(0,0,0,.45)}
video,canvas{position:absolute;inset:0;width:100%;height:100%}
video{object-fit:cover;opacity:.35}
.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(7,11,20,.92) 0%,rgba(7,11,20,.55) 55%,rgba(7,11,20,.1) 100%)}
.txt{position:absolute;left:34px;top:50%;transform:translateY(-50%);max-width:70%}
.tag{display:inline-block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#c6ff3d;
  border:1px solid rgba(198,255,61,.4);padding:4px 10px;border-radius:999px;margin-bottom:12px}
h1{font-family:'Space Grotesk',sans-serif;font-size:clamp(26px,4.2vw,44px);line-height:1.08;color:#fff;letter-spacing:-.02em}
h1 span{background:linear-gradient(90deg,#c6ff3d,#22d3ee);-webkit-background-clip:text;background-clip:text;color:transparent}
p{margin-top:10px;color:#b8c3dc;font-size:clamp(13px,1.6vw,16px);max-width:560px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.chip{font-size:12.5px;color:#e8eefc;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);
  padding:6px 12px;border-radius:999px;backdrop-filter:blur(6px);animation:rise .8s ease both}
.chip:nth-child(2){animation-delay:.12s}.chip:nth-child(3){animation-delay:.24s}.chip:nth-child(4){animation-delay:.36s}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@media(max-width:640px){.txt{max-width:92%;left:18px}.hero{height:270px}}
</style></head><body>
<div class="hero" id="hero">
  __VIDEO__
  <canvas id="c"></canvas>
  <div class="shade"></div>
  <div class="txt">
    <div class="tag">AI-powered fitness</div>
    <h1>AI Gym &amp; <span>Fitness Assistant</span></h1>
    <p>Your pose coach, diet planner, habit tracker and gym buddy in one place.</p>
    <div class="chips"><div class="chip">Live pose coaching</div><div class="chip">Skip-risk prediction</div>
      <div class="chip">Smart gym IoT</div><div class="chip">Private accounts</div></div>
  </div>
</div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let W,H,dpr=Math.min(window.devicePixelRatio||1,2);
function size(){const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0)}
size();window.addEventListener('resize',size);
const P=[];for(let i=0;i<46;i++)P.push({x:Math.random(),y:Math.random(),s:.4+Math.random()*1.6,v:.02+Math.random()*.05,c:Math.random()>.5?'198,255,61':'34,211,238'});
const pts=[[0,0],[.12,0],[.16,-8],[.20,0],[.30,0],[.33,10],[.37,-58],[.41,32],[.44,0],[.58,0],[.64,-14],[.72,0],[1,0]];
function ecg(t){t=((t%1)+1)%1;for(let i=1;i<pts.length;i++){if(t<=pts[i][0]){const a=pts[i-1],b=pts[i],k=(t-a[0])/(b[0]-a[0]);return a[1]+(b[1]-a[1])*k}}return 0}
function frame(ts){
  const t=ts/1000;ctx.clearRect(0,0,W,H);
  // pulse rings from the right
  for(let i=0;i<3;i++){const p=((t*.35+i/3)%1),r=40+p*Math.max(W,H)*.55;
    ctx.beginPath();ctx.arc(W*.86,H*.45,r,0,6.283);ctx.strokeStyle='rgba(34,211,238,'+(.22*(1-p))+')';ctx.lineWidth=1.5;ctx.stroke()}
  // particles
  for(const p of P){p.y-=p.v*.016;if(p.y<0){p.y=1;p.x=Math.random()}
    ctx.beginPath();ctx.arc(p.x*W,p.y*H,p.s,0,6.283);ctx.fillStyle='rgba('+p.c+',.55)';ctx.fill()}
  // scrolling heartbeat line
  const base=H*.80,amp=H*.30,period=Math.max(260,W*.34),off=t*110;
  const g=ctx.createLinearGradient(0,0,W,0);g.addColorStop(0,'rgba(198,255,61,0)');g.addColorStop(.35,'rgba(198,255,61,.85)');g.addColorStop(1,'rgba(34,211,238,.95)');
  ctx.beginPath();for(let x=0;x<=W;x+=2){const y=base+ecg((x+off)/period)*amp/58;x?ctx.lineTo(x,y):ctx.moveTo(x,y)}
  ctx.strokeStyle=g;ctx.lineWidth=2.2;ctx.shadowColor='rgba(198,255,61,.9)';ctx.shadowBlur=12;ctx.stroke();ctx.shadowBlur=0;
  if(!reduce)requestAnimationFrame(frame)
}
requestAnimationFrame(frame);
</script></body></html>
"""


def inject_css():
    """Applies the dark neon theme to the whole page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _video_tag() -> str:
    try:
        if os.path.isfile(_VIDEO) and os.path.getsize(_VIDEO) <= _MAX_VIDEO_BYTES:
            with open(_VIDEO, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode()
            return f'<video autoplay muted loop playsinline src="data:video/mp4;base64,{b64}"></video>'
    except OSError:
        pass
    return ""


def hero(height: int = 270):
    """Animated banner (moving heartbeat line, pulse rings, particles; optional looping MP4 behind it)."""
    components.html(_HERO.replace("__VIDEO__", _video_tag()), height=height)