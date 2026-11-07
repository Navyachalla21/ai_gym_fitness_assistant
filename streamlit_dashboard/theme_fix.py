"""Slim neon styling layer. Works together with .streamlit/config.toml (dark base theme),
so inputs, error boxes and tables stay readable."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');
:root { --lime:#c6ff3d; --cyan:#22d3ee; --line:rgba(255,255,255,.12); --card:rgba(255,255,255,.05); }
html, body, .stApp { font-family:'Inter',sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 85% -10%, rgba(34,211,238,.14), transparent 60%),
                     radial-gradient(900px 500px at -10% 10%, rgba(198,255,61,.08), transparent 55%), #070b14; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1200px; }
h1, h2, h3, h4 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.01em; }
h3 { border-left: 4px solid var(--lime); padding-left:.6rem; }

/* tabs as pills */
.stTabs [data-baseweb="tab-list"] { gap:.4rem; flex-wrap:wrap; }
.stTabs [data-baseweb="tab"] { background: var(--card); border:1px solid var(--line); border-radius:999px; padding:.35rem 1rem; }
.stTabs [data-baseweb="tab"]:hover { border-color: rgba(198,255,61,.6); }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, var(--lime), #7dd957) !important;
        border-color: transparent !important; box-shadow:0 0 18px rgba(198,255,61,.35); }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { color:#0a1200 !important; font-weight:600; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

/* metric cards */
[data-testid="stMetric"] { background: var(--card); border:1px solid var(--line); border-radius:16px; padding:.9rem 1rem; }
[data-testid="stMetricValue"] { font-family:'Space Grotesk',sans-serif; color: var(--lime); }

/* buttons: dark text on the lime gradient */
.stButton > button, .stFormSubmitButton > button { background: linear-gradient(135deg, var(--lime), #7dd957);
        border:0; border-radius:12px; font-weight:600; transition: transform .2s ease, box-shadow .2s ease; }
.stButton > button p, .stFormSubmitButton > button p { color:#0a1200 !important; font-weight:600; }
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px);
        box-shadow:0 8px 24px rgba(198,255,61,.35); }
.stButton > button:disabled, .stFormSubmitButton > button:disabled { background:#2a3347; box-shadow:none; transform:none; }
.stButton > button:disabled p, .stFormSubmitButton > button:disabled p { color:#8793ad !important; }

/* rounded cards */
[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stAlert"] { border-radius:14px; }
[data-testid="stExpander"] { border:1px solid var(--line); }
.stProgress > div > div > div > div { background: linear-gradient(90deg, var(--cyan), var(--lime)); }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)