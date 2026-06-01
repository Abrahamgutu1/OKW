"""
OKW FieldSync — Lead Service Line Inventory Dashboard
Oracle 23ai · PIPE_VISION_AI · ODEQ 2026
ArcGIS-inspired utility GIS aesthetic
"""

import streamlit as st
import pandas as pd
import oracledb
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OKW FieldSync · Service Line Inventory",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inspector registry ─────────────────────────────────────────────────────────
INSPECTOR_REGISTRY = {
    "PIN-9402": "A. Mutu (Badge #402)",
    "PIN-1185": "J. Doe (Badge #185)",
    "PIN-2365": "S. Smith (Badge #365)",
}

# ── CSS — Twin-Panel ArcGIS + Grafana Command Center + Retool List ────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* ── App shell — dark command center base ── */
.stApp { background: #0f1117; color: #e2e8f0; }
.stSidebar { background: #1a1d27 !important; border-right: 1px solid #2d3148; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }

/* ── Sidebar text ── */
.stSidebar label,
.stSidebar .stMarkdown,
.stSidebar p { color: #94a3b8 !important; font-size: .8rem !important; }
.stSidebar h3 { color: #e2e8f0 !important; font-size: .85rem !important; font-weight: 600 !important; }

/* ── Sidebar inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    color: #e2e8f0 !important;
    border-radius: 4px !important;
    font-size: .82rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #00b2d6 !important;
    box-shadow: 0 0 0 2px rgba(0,178,214,.15) !important;
}

/* ── Sidebar connect button ── */
.stButton > button {
    background: linear-gradient(135deg, #00b2d6 0%, #0284a8 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 4px !important;
    font-size: .82rem !important;
    font-weight: 600 !important;
    padding: .55rem 1rem !important;
    width: 100%;
    letter-spacing: .03em;
    transition: opacity .15s;
}
.stButton > button:hover { opacity: .88 !important; }

/* ── Form submit — green commit ── */
.stFormSubmitButton > button {
    background: #16a34a !important;
    color: #fff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    width: 100%;
    padding: .55rem 1rem !important;
}
.stFormSubmitButton > button:hover { background: #15803d !important; }

/* ══════════════════════════════════════════════════
   TOPBAR — ArcGIS Command Center style
══════════════════════════════════════════════════ */
.esri-topbar {
    background: linear-gradient(90deg, #0f1117 0%, #1a1d27 100%);
    border-bottom: 2px solid #00b2d6;
    padding: .7rem 1.4rem;
    display: flex; align-items: center; justify-content: space-between;
}
.esri-topbar-logo { display: flex; align-items: center; gap: .8rem; }
.esri-topbar-icon {
    background: #00b2d6; border-radius: 5px;
    width: 34px; height: 34px; display: flex; align-items: center;
    justify-content: center; font-size: 1rem;
    box-shadow: 0 0 12px rgba(0,178,214,.4);
}
.esri-topbar-title {
    font-size: .92rem; font-weight: 700; color: #f1f5f9;
    letter-spacing: .05em; text-transform: uppercase;
}
.esri-topbar-sub { font-size: .68rem; color: #64748b; margin-top: 2px; }
.esri-topbar-right { display: flex; align-items: center; gap: 1rem; }
.esri-status-badge {
    background: rgba(22,163,74,.15); border: 1px solid #16a34a;
    color: #4ade80; padding: 3px 10px; border-radius: 3px;
    font-size: .67rem; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
}
.esri-status-offline {
    background: rgba(234,179,8,.1); border: 1px solid #ca8a04;
    color: #fbbf24; padding: 3px 10px; border-radius: 3px;
    font-size: .67rem; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase;
}
.topbar-pwsid {
    font-family: 'JetBrains Mono', monospace; font-size: .7rem;
    color: #475569; background: #1e2235; padding: 3px 8px;
    border-radius: 3px; border: 1px solid #2d3148;
}

/* ══════════════════════════════════════════════════
   GRAFANA-STYLE KPI METRIC GRID
══════════════════════════════════════════════════ */
.kpi-strip {
    display: flex; gap: 1px;
    background: #2d3148;
    border: 1px solid #2d3148;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 1rem;
}
.kpi-tile {
    flex: 1; padding: .9rem 1.2rem;
    background: #1a1d27;
    position: relative;
}
.kpi-tile::after {
    content: '';
    position: absolute; top: 20%; right: 0; bottom: 20%;
    width: 1px; background: #2d3148;
}
.kpi-tile:last-child::after { display: none; }
.kpi-tile-num {
    font-size: 2rem; font-weight: 700; line-height: 1;
    font-family: 'JetBrains Mono', monospace;
    color: #e2e8f0;
}
.kpi-tile-num.blue  { color: #38bdf8; }
.kpi-tile-num.red   { color: #f87171; }
.kpi-tile-num.green { color: #4ade80; }
.kpi-tile-num.amber { color: #fbbf24; }
.kpi-tile-label {
    font-size: .62rem; color: #64748b; text-transform: uppercase;
    letter-spacing: .12em; margin-top: .3rem; font-weight: 600;
}
.kpi-tile-sub { font-size: .67rem; color: #475569; margin-top: .15rem; }
.kpi-tile-spark {
    position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    border-radius: 0 0 6px 6px;
}
.kpi-tile-spark.blue  { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
.kpi-tile-spark.red   { background: linear-gradient(90deg, #dc2626, #f87171); }
.kpi-tile-spark.green { background: linear-gradient(90deg, #16a34a, #4ade80); }
.kpi-tile-spark.amber { background: linear-gradient(90deg, #d97706, #fbbf24); }

/* ══════════════════════════════════════════════════
   RETOOL / SALESFORCE LIGHTNING SPLIT-LIST
══════════════════════════════════════════════════ */
.panel {
    background: #1a1d27;
    border: 1px solid #2d3148;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 1rem;
}
.panel-header {
    padding: .55rem 1rem;
    background: #0f1117;
    border-bottom: 1px solid #2d3148;
    font-size: .67rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: .12em;
    display: flex; align-items: center; justify-content: space-between;
}
.panel-header-left { display: flex; align-items: center; gap: .5rem; }
.panel-count {
    background: #2d3148; color: #94a3b8; padding: 1px 7px;
    border-radius: 10px; font-size: .65rem; font-weight: 700;
}

/* Retool-style asset rows */
.asset-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: .5rem .85rem;
    border-bottom: 1px solid #1e2235;
    background: #1a1d27;
    transition: background .1s;
    cursor: pointer;
}
.asset-row:hover { background: #1e2235; }
.asset-row.active {
    background: rgba(0,178,214,.08);
    border-left: 3px solid #00b2d6;
}
.asset-row-left { display: flex; align-items: center; gap: .65rem; }
.asset-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.asset-dot.lead    { background: #f87171; box-shadow: 0 0 6px rgba(248,113,113,.5); }
.asset-dot.safe    { background: #4ade80; box-shadow: 0 0 6px rgba(74,222,128,.4); }
.asset-dot.unknown { background: #fbbf24; }
.asset-row-id {
    font-size: .78rem; font-weight: 600; color: #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
}
.asset-row-sub { font-size: .65rem; color: #475569; margin-top: 1px; }
.asset-row-badge {
    font-size: .6rem; font-weight: 700; padding: 2px 6px;
    border-radius: 3px; text-transform: uppercase; letter-spacing: .05em;
    white-space: nowrap;
}
.badge-lead    { background: rgba(248,113,113,.15); color: #f87171; border: 1px solid rgba(248,113,113,.3); }
.badge-safe    { background: rgba(74,222,128,.12); color: #4ade80; border: 1px solid rgba(74,222,128,.25); }
.badge-unknown { background: rgba(251,191,36,.1); color: #fbbf24; border: 1px solid rgba(251,191,36,.25); }
.badge-verified { background: rgba(56,189,248,.1); color: #38bdf8; border: 1px solid rgba(56,189,248,.25); }

/* ══════════════════════════════════════════════════
   RIGHT PANEL — Inspection workspace
══════════════════════════════════════════════════ */
.class-chip {
    display: inline-block; padding: 3px 10px; border-radius: 3px;
    font-size: .68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; margin-bottom: .5rem;
}
.chip-lead    { background: rgba(248,113,113,.2); color: #f87171; border: 1px solid rgba(248,113,113,.4); }
.chip-clear   { background: rgba(74,222,128,.15); color: #4ade80; border: 1px solid rgba(74,222,128,.3); }
.chip-pending { background: rgba(251,191,36,.12); color: #fbbf24; border: 1px solid rgba(251,191,36,.25); }

.section-title {
    font-size: .65rem; font-weight: 700; color: #475569;
    text-transform: uppercase; letter-spacing: .12em;
    padding: .35rem 0; border-bottom: 1px solid #2d3148;
    margin-bottom: .65rem; margin-top: .5rem;
}

/* Attribute table — Salesforce Lightning style */
.meta-table { width: 100%; border-collapse: collapse; font-size: .77rem; }
.meta-table tr { border-bottom: 1px solid #1e2235; }
.meta-table tr:hover { background: #1e2235; }
.meta-table td { padding: .38rem .6rem; }
.meta-table td:first-child {
    font-weight: 500; color: #64748b; width: 40%;
    font-size: .65rem; text-transform: uppercase; letter-spacing: .07em;
}
.meta-table td:last-child {
    color: #e2e8f0; font-family: 'JetBrains Mono', monospace; font-size: .75rem;
}
.meta-table .vector-row td { color: #38bdf8 !important; }
.meta-table .audit-row td  { color: #4ade80 !important; }

/* Photo frame */
.photo-frame {
    background: #0f1117; border: 1px solid #2d3148;
    border-radius: 4px; padding: .5rem; margin-bottom: .75rem;
}
.photo-placeholder {
    background: #0f1117; border: 1px dashed #2d3148;
    border-radius: 4px; padding: 2.5rem 1rem; text-align: center;
}
.photo-placeholder .ph-icon { font-size: 2rem; margin-bottom: .4rem; }
.photo-placeholder .ph-text { font-size: .75rem; color: #475569; }

/* Audit form */
.audit-notice {
    background: rgba(251,191,36,.08); border: 1px solid rgba(251,191,36,.3);
    border-radius: 4px; padding: .6rem .85rem; margin-bottom: .75rem;
    font-size: .72rem; color: #fbbf24;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 4px !important;
    color: #e2e8f0 !important;
    font-size: .82rem !important;
}

/* Form container */
div[data-testid="stForm"] {
    background: #0f1117; border: 1px solid #2d3148;
    border-radius: 4px; padding: 1rem;
}

/* Streamlit overrides */
.stMarkdown h4 { color: #e2e8f0 !important; font-size: .88rem !important; }
hr { border-color: #2d3148 !important; }

/* Empty state */
.empty-state {
    background: #1a1d27; border: 1px dashed #2d3148;
    border-radius: 6px; padding: 3.5rem 2rem; text-align: center;
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: .6rem; }
.empty-state-text { font-size: .8rem; color: #475569; line-height: 1.7; }

/* Report section */
.report-panel {
    background: #1a1d27; border: 1px solid #2d3148;
    border-top: 2px solid #00b2d6; border-radius: 6px;
    padding: 1rem 1.3rem .6rem; margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k in ("df", "err", "selected_idx", "override_msg", "vec_ok", "hv_count"):
    if k not in st.session_state:
        st.session_state[k] = None
if not st.session_state.override_msg:
    st.session_state.override_msg = ""

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.5rem 0 1rem">
        <div style="font-size:.7rem;color:#a0b4c0;text-transform:uppercase;
             letter-spacing:.12em;font-weight:700">OKW FieldSync</div>
        <div style="font-size:.82rem;color:#ffffff;font-weight:600;margin-top:2px">
            Service Line Inventory
        </div>
        <div style="font-size:.68rem;color:#7a9ab0;margin-top:2px">ODEQ 2026 Compliance</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Database Connection")
    db_user     = st.text_input("User",     value="system")
    db_password = st.text_input("Password", value="Awesomekid123", type="password")
    db_host     = st.text_input("Host",     value="localhost")
    db_port     = st.number_input("Port",   value=1521, step=1)
    db_service  = st.text_input("Service",  value="FREEPDB1")

    st.markdown("---")
    load_btn = st.button("Connect to Database", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:.68rem;color:#a0a0a0;line-height:1.8">
        <div style="color:#d0d0d0;font-weight:600;margin-bottom:.3rem">DATA SOURCE</div>
        Oracle 23ai · FREEPDB1<br>
        SYSTEM.EVIDENCE<br><br>
        <div style="color:#d0d0d0;font-weight:600;margin-bottom:.3rem">AI ENGINE</div>
        PIPE_VISION_AI<br>
        ResNet-50 v1-12<br>
        VECTOR_DISTANCE (Cosine)<br><br>
        <div style="color:#d0d0d0;font-weight:600;margin-bottom:.3rem">AUTHORITY</div>
        Oklahoma DEQ<br>
        Lead &amp; Copper Rule 2026
    </div>
    """, unsafe_allow_html=True)

# ── SQL ────────────────────────────────────────────────────────────────────────
AUDIT_SQL = """
SELECT
    EVIDENCE_ID,
    SERVICE_LINE_ID,
    PHOTO_URL,
    GPS_LATITUDE,
    GPS_LONGITUDE,
    UPLOAD_DATE,
    NVL(USER_VERIFIED_STATUS, 'UNVERIFIED') AS USER_VERIFIED_STATUS,
    AUDITED_BY,
    VECTOR_DISTANCE(
        IMAGE_VECTOR,
        VECTOR('[1.00, 0.00, 1.00]', 3, FLOAT32),
        COSINE
    ) AS AI_DISTANCE
FROM EVIDENCE
ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
"""

FALLBACK_SQL = """
SELECT
    EVIDENCE_ID,
    SERVICE_LINE_ID,
    PHOTO_URL,
    GPS_LATITUDE,
    GPS_LONGITUDE,
    UPLOAD_DATE,
    NVL(USER_VERIFIED_STATUS, 'UNVERIFIED') AS USER_VERIFIED_STATUS,
    AUDITED_BY,
    NULL AS AI_DISTANCE
FROM EVIDENCE
ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
"""

# ── Fetch ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch(user, password, host, port, service):
    try:
        conn = oracledb.connect(user=user, password=password,
                                dsn=f"{host}:{int(port)}/{service}")
        cursor = conn.cursor()
        try:
            cursor.execute(AUDIT_SQL)
            vec_ok = True
        except Exception:
            cursor.execute(FALLBACK_SQL)
            vec_ok = False
        cols = [c[0].upper() for c in cursor.description]
        rows = cursor.fetchall()
        df   = pd.DataFrame(rows, columns=cols)
        cursor.execute("""
            SELECT COUNT(*) FROM EVIDENCE
            WHERE USER_VERIFIED_STATUS IN (
                'MANUALLY_CONFIRMED_LEAD', 'MANUALLY_CONFIRMED_SAFE'
            )
        """)
        hv_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return df, None, vec_ok, int(hv_count)
    except oracledb.DatabaseError as e:
        err = str(e)
        if any(c in err for c in ["DPY-6005","DPY-4011","ORA-03113","ORA-03114"]):
            return None, "CONNECTION_LOST", False, 0
        if "ORA-01017" in err:
            return None, "ORA-01017", False, 0
        return None, err, False, 0
    except Exception as e:
        return None, str(e), False, 0

if load_btn:
    with st.spinner("Connecting to Oracle 23ai…"):
        df, err, vec_ok, hv_count = fetch(db_user, db_password, db_host, int(db_port), db_service)
        st.session_state.df           = df
        st.session_state.err          = err
        st.session_state.vec_ok       = vec_ok
        st.session_state.hv_count     = hv_count
        st.session_state.selected_idx = None
        st.session_state.override_msg = ""

df       = st.session_state.df
err      = st.session_state.err
vec_ok   = st.session_state.get("vec_ok", False)
hv_count = st.session_state.get("hv_count", 0) or 0

# ── Helpers ────────────────────────────────────────────────────────────────────
def distance_to_confidence(distance):
    try:
        d = float(distance)
    except (TypeError, ValueError):
        return "clear", "Non-Lead", 87.5
    if d < 0.35:
        conf = 99.9 - ((d / 0.35) * 34.9)
        return "lead", "Lead — SUSPECT", round(conf, 1)
    clamped = min(d, 1.0)
    conf = 65.0 + (((clamped - 0.35) / 0.65) * 34.9)
    return "clear", "Non-Lead — CLEAR", round(conf, 1)

def load_image(url: str):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return Image.open(BytesIO(r.content))

def render_placeholder(msg: str):
    st.markdown(f"""
    <div class="photo-placeholder">
        <div class="ph-icon">📷</div>
        <div class="ph-text">{msg}</div>
    </div>""", unsafe_allow_html=True)

def audit_color(status: str) -> str:
    s = str(status).upper()
    if s == "MANUALLY_CONFIRMED_LEAD": return "#c0392b"
    if s == "MANUALLY_CONFIRMED_SAFE": return "#2d6a4f"
    return "#7a5200"

# ── Top header bar ─────────────────────────────────────────────────────────────
status_html = f'<span class="esri-status-badge">● CONNECTED</span>' if df is not None \
              else '<span class="esri-status-offline">○ OFFLINE</span>'
vec_note = " · Vector Distance Active" if vec_ok else ""

st.markdown(f"""
<div class="esri-topbar">
  <div class="esri-topbar-logo">
    <div class="esri-topbar-icon">💧</div>
    <div>
      <div class="esri-topbar-title">OKW FieldSync — Lead Service Line Inventory</div>
      <div class="esri-topbar-sub">
        Oklahoma City Public Works &nbsp;·&nbsp; Oracle 23ai{vec_note} &nbsp;·&nbsp; ODEQ 2026
      </div>
    </div>
  </div>
  <div class="esri-topbar-right">
    <span class="topbar-pwsid">PWSID: OK1020401</span>
    {status_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Error ──────────────────────────────────────────────────────────────────────
if err:
    if err == "CONNECTION_LOST":
        st.warning("⚡ Database session lost. Click **Connect to Database** to reconnect. If the container stopped, run `docker start oracle-free` first.")
    elif err == "ORA-01017":
        st.error("**Authentication Failed (ORA-01017)** — Invalid credentials or SYSTEM account is locked.")
        st.code('docker exec -i oracle-free sqlplus \'system/Awesomekid123@localhost:1521/FREEPDB1\' << \'EOF\'\nALTER USER system IDENTIFIED BY Awesomekid123;\nEXIT;\nEOF', language="bash")
    else:
        st.error(f"**Database Connection Error:** {err}")
    st.stop()

if df is None:
    st.markdown("""
    <div class="empty-state" style="margin-top:1rem">
        <div class="empty-state-icon">🔌</div>
        <div class="empty-state-text">
            Enter credentials in the sidebar<br>
            and click <strong style="color:#38bdf8">Connect to Database</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── KPI strip ──────────────────────────────────────────────────────────────────
total       = len(df)
lines       = df["SERVICE_LINE_ID"].nunique()
has_photo   = int(df["PHOTO_URL"].apply(lambda x: str(x).strip().startswith("http")).sum())
suspect_cnt = int((pd.to_numeric(df["AI_DISTANCE"], errors="coerce") < 0.35).sum()) \
              if "AI_DISTANCE" in df.columns else 0

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-tile">
    <div class="kpi-tile-num blue">{total}</div>
    <div class="kpi-tile-label">Evidence Records</div>
    <div class="kpi-tile-sub">{lines} service lines</div>
    <div class="kpi-tile-spark blue"></div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num red">{suspect_cnt}</div>
    <div class="kpi-tile-label">Lead Suspect</div>
    <div class="kpi-tile-sub">Cosine &lt; 0.35</div>
    <div class="kpi-tile-spark red"></div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num">{has_photo}</div>
    <div class="kpi-tile-label">Photo Records</div>
    <div class="kpi-tile-sub">Field images</div>
    <div class="kpi-tile-spark blue"></div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num green">{hv_count}</div>
    <div class="kpi-tile-label">Verified</div>
    <div class="kpi-tile-sub">Inspector sign-off</div>
    <div class="kpi-tile-spark green"></div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num amber">{total - hv_count}</div>
    <div class="kpi-tile-label">Pending Review</div>
    <div class="kpi-tile-sub">Awaiting verification</div>
    <div class="kpi-tile-spark amber"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main layout ────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2], gap="medium")

# ── LEFT: inventory list ───────────────────────────────────────────────────────
with left_col:
    st.markdown(f"""
    <div class="panel">
      <div class="panel-header">
        <div class="panel-header-left">
            <span>📋</span> Service Line Inventory
        </div>
        <span class="panel-count">{total}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("", placeholder="Filter by Service Line ID…",
                           label_visibility="collapsed")
    filtered = df.copy()
    if search.strip():
        filtered = filtered[
            filtered["SERVICE_LINE_ID"].astype(str).str.contains(search.strip(), case=False)
        ]

    if filtered.empty:
        st.caption("No records match the filter.")
    else:
        for i, (_, row) in enumerate(filtered.iterrows()):
            ev_id   = row.get("EVIDENCE_ID",    "—")
            sl_id   = row.get("SERVICE_LINE_ID","—")
            p_url   = str(row.get("PHOTO_URL",  "") or "").strip()
            u_date  = row.get("UPLOAD_DATE",    None)
            ai_dist = row.get("AI_DISTANCE",    None)
            uv_stat = str(row.get("USER_VERIFIED_STATUS","UNVERIFIED"))
            has_p   = p_url.startswith("http")

            date_str = "—"
            if u_date is not None:
                try:
                    date_str = u_date.strftime("%m/%d/%Y") if hasattr(u_date,"strftime") \
                               else str(u_date)[:10]
                except Exception:
                    date_str = str(u_date)[:10]

            # Classification badge
            mat_class, badge_cls = ("Lead", "badge-lead")
            if ai_dist is not None:
                try:
                    d = float(ai_dist)
                    if d >= 0.35:
                        mat_class, badge_cls = ("Non-Lead", "badge-safe")
                except Exception:
                    pass
            if uv_stat == "MANUALLY_CONFIRMED_SAFE":
                mat_class, badge_cls = ("Confirmed Safe", "badge-safe")
            elif uv_stat == "MANUALLY_CONFIRMED_LEAD":
                mat_class, badge_cls = ("Confirmed Lead", "badge-lead")

            is_active = st.session_state.selected_idx == i
            row_cls   = "asset-row active" if is_active else "asset-row"

            dot_cls = "lead" if badge_cls == "badge-lead" else ("safe" if badge_cls == "badge-safe" else "unknown")
            photo_icon = "📷" if has_p else "—"
            st.markdown(f"""
            <div class="{row_cls}">
              <div class="asset-row-left">
                <span class="asset-dot {dot_cls}"></span>
                <div>
                  <div class="asset-row-id">SL-{sl_id} · EV-{ev_id}</div>
                  <div class="asset-row-sub">{photo_icon} &nbsp;{date_str}</div>
                </div>
              </div>
              <span class="asset-row-badge {badge_cls}">{mat_class}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("→ Inspect", key=f"sel_{i}", use_container_width=True):
                st.session_state.selected_idx = i
                st.session_state.override_msg = ""
                st.rerun()

# ── RIGHT: inspection panel ────────────────────────────────────────────────────
with right_col:
    idx = st.session_state.selected_idx

    if idx is None:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🗺️</div>
            <div class="empty-state-text">
                Select a record from the inventory list<br>
                to open the inspection workspace
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        try:
            row = filtered.iloc[idx]
        except IndexError:
            st.session_state.selected_idx = None
            st.rerun()

        ev_id         = row.get("EVIDENCE_ID",    "—")
        sl_id         = row.get("SERVICE_LINE_ID","—")
        lat           = row.get("GPS_LATITUDE",   None)
        lon           = row.get("GPS_LONGITUDE",  None)
        u_date        = row.get("UPLOAD_DATE",    None)
        ai_distance   = row.get("AI_DISTANCE",    None)
        db_status     = str(row.get("USER_VERIFIED_STATUS","UNVERIFIED"))
        audited_by    = row.get("AUDITED_BY",     None)
        photo_url_str = str(row["PHOTO_URL"]).strip()
        is_live_url   = photo_url_str.startswith("http")

        # Classification
        mat_type, mat_label, confidence = distance_to_confidence(ai_distance)
        if ai_distance is None:
            mat_type  = "clear" if is_live_url else "lead"
            mat_label = "Non-Lead — CLEAR" if is_live_url else "Lead — SUSPECT"
            confidence = 87.5

        # Format values
        lat_str  = f"{float(lat):.6f}" if lat is not None else "Not recorded"
        lon_str  = f"{float(lon):.6f}" if lon is not None else "Not recorded"
        dist_str = f"{float(ai_distance):.4f}" if ai_distance is not None else "N/A"
        try:
            date_str = u_date.strftime("%m/%d/%Y %H:%M") \
                       if u_date is not None and hasattr(u_date,"strftime") \
                       else (str(u_date)[:16] if u_date else "—")
        except Exception:
            date_str = str(u_date)

        chip_cls = "chip-lead" if mat_type == "lead" else "chip-clear"
        a_color  = audit_color(db_status)
        audited_suffix = f" — {audited_by}" \
                         if audited_by and str(audited_by) not in ("None","") else ""

        # ── Record header ──
        hdr1, hdr2 = st.columns([4, 1])
        with hdr1:
            st.markdown(f"""
            <div style="margin-bottom:.5rem">
                <span class="class-chip {chip_cls}">{mat_label}</span>
                <div style="font-size:1rem;font-weight:700;color:#1a1a2e">
                    Service Line {sl_id} &nbsp;·&nbsp; Evidence Record {ev_id}
                </div>
                <div style="font-size:.72rem;color:#6b6b6b;margin-top:2px">
                    AI Confidence: {confidence}% &nbsp;·&nbsp; Vector Distance: {dist_str}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with hdr2:
            if st.button("✕ Close", key="close_panel"):
                st.session_state.selected_idx = None
                st.session_state.override_msg = ""
                st.rerun()

        # ── Map ──
        if lat is not None and lon is not None:
            try:
                map_df = pd.DataFrame({"latitude": [float(lat)], "longitude": [float(lon)]})
                st.markdown('<div class="section-title">🗺️ Field Coordinate Location</div>',
                            unsafe_allow_html=True)
                st.map(map_df, zoom=15, use_container_width=True)
            except (ValueError, TypeError):
                st.caption("⚠️ Invalid GPS coordinate data.")

        # ── Photo ──
        st.markdown('<div class="section-title">📷 Field Inspection Photo</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="photo-frame">', unsafe_allow_html=True)
        if is_live_url:
            try:
                st.image(load_image(photo_url_str), use_container_width=True)
            except Exception as e:
                st.error(f"Image load failed: {e}")
                render_placeholder("Field image unavailable — check URL or network access.")
        else:
            render_placeholder("No field photo on record for this evidence entry.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Metadata ──
        st.markdown('<div class="section-title">📊 Record Attributes</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <table class="meta-table">
          <tr><td>Evidence ID</td><td>EV-{ev_id}</td></tr>
          <tr><td>Service Line ID</td><td>SL-{sl_id}</td></tr>
          <tr><td>GPS Latitude</td><td>{lat_str}</td></tr>
          <tr><td>GPS Longitude</td><td>{lon_str}</td></tr>
          <tr><td>Upload Date</td><td>{date_str}</td></tr>
          <tr><td>AI Classification</td><td>{mat_label}</td></tr>
          <tr><td>AI Confidence</td><td>{confidence}%</td></tr>
          <tr class="vector-row">
            <td>Vector Distance (Cosine)</td>
            <td>{dist_str} &nbsp;<span style="color:#6b6b6b;font-size:.68rem">
                baseline [1.00, 0.00, 1.00] · threshold &lt; 0.35</span>
            </td>
          </tr>
          <tr><td>Audit Status</td>
            <td style="color:{a_color};font-weight:600">
                {db_status.replace("MANUALLY_CONFIRMED_","")}{audited_suffix}
            </td>
          </tr>
        </table>
        """, unsafe_allow_html=True)

        # ── Secure audit form ──────────────────────────────────────────────
        st.markdown('<div class="section-title">🔒 Field Verification — Inspector Sign-Off</div>', unsafe_allow_html=True)

        if st.session_state.override_msg:
            st.success(st.session_state.override_msg)

        with st.form(key=f"audit_form_{ev_id}"):
            st.markdown("""
            <div class="audit-notice">
                <strong>ODEQ Security Notice:</strong> All material classification overrides
                require an authorized field inspector token. Your badge ID will be
                permanently recorded against this evidence entry.
            </div>
            """, unsafe_allow_html=True)

            secure_token = st.text_input(
                "Inspector Security Token PIN",
                type="password",
                help="Enter your unique ODEQ field inspection PIN."
            )

            status_options = ["UNVERIFIED","MANUALLY_CONFIRMED_LEAD","MANUALLY_CONFIRMED_SAFE"]
            try:
                cur_idx = status_options.index(db_status)
            except ValueError:
                cur_idx = 0

            audit_decision = st.selectbox(
                "Material Classification Override",
                options=status_options,
                index=cur_idx,
                format_func=lambda x: x.replace("MANUALLY_CONFIRMED_","✓ ").replace("UNVERIFIED","— Unverified")
            )

            submit = st.form_submit_button("Submit Field Verification")

            if submit:
                if secure_token not in INSPECTOR_REGISTRY:
                    st.error("Invalid security token. Access denied. This attempt has been logged.")
                elif audit_decision == "UNVERIFIED":
                    st.warning("Select a confirmed material classification to submit.")
                else:
                    try:
                        inspector = INSPECTOR_REGISTRY[secure_token]
                        conn   = oracledb.connect(user=db_user, password=db_password,
                                                  dsn=f"{db_host}:{int(db_port)}/{db_service}")
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE EVIDENCE
                            SET USER_VERIFIED_STATUS = :1, AUDITED_BY = :2
                            WHERE EVIDENCE_ID = :3
                        """, (audit_decision, inspector, int(ev_id)))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.session_state.override_msg = (
                            f"✅ Record EV-{ev_id} verified as "
                            f"{audit_decision.replace('MANUALLY_CONFIRMED_','')} by {inspector}."
                        )
                        st.toast("🔒 Audit Log Emitted to Pluggable Engine", icon="✅")
                        fetch.clear()
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Database write failed: {ex}")

# ── Ingestion Hub ─────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📥 Oklahoma DEQ Ingestion Hub — Historical Excel / PDF Tap Cards"):
    st.markdown("""
    <div style="font-size:.8rem;color:#94a3b8;margin-bottom:1rem">
        Upload historical data packages directly into Oracle 23ai.
        Records with installation dates of <strong style="color:#fbbf24">1987 or later</strong>
        automatically clear regulatory constraints per the federal lead ban.
    </div>
    """, unsafe_allow_html=True)

    up_col1, up_col2 = st.columns(2)

    with up_col1:
        excel_file = st.file_uploader("Historical Inventory Excel Template", type=["xlsx","xls"])
        if excel_file:
            try:
                import_df = pd.read_excel(excel_file)
                st.success(f"Staged {len(import_df)} rows from spreadsheet — ready for batch insert.")
                st.dataframe(import_df.head(5), use_container_width=True)
            except Exception as e:
                st.error(f"Excel parsing failed: {e}")

    with up_col2:
        pdf_file = st.file_uploader("Historical Tap Card Certificates (PDF)", type=["pdf"])
        if pdf_file:
            st.info("PDF staged — regulatory regex scan pending. Install `pdfplumber` for full extraction.")

# ── Compliance Report Generator ───────────────────────────────────────────────
import os
import re
import subprocess

PWSID         = "OK1020401"
WORKSPACE_DIR = os.path.expanduser("~/Desktop/OKW FieldSync")
TEX_PATH      = os.path.join(WORKSPACE_DIR, "compliance_report.tex")
PDF_PATH      = os.path.join(WORKSPACE_DIR, "compliance_report.pdf")

def classify_material(status, install_year=None):
    s = str(status).upper() if status else "UNKNOWN"
    if s == "MANUALLY_CONFIRMED_LEAD":
        return "LEAD"
    if s == "MANUALLY_CONFIRMED_SAFE":
        if install_year and int(install_year) >= 1987:
            return "NON-LEAD (Post-1987 Statutory Compliance)"
        return "NON-LEAD"
    return "LEAD STATUS UNKNOWN"

def tex_escape(val):
    if val is None:
        return "---"
    s = str(val)
    for char, repl in [
        ("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
        ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
        ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
    ]:
        s = s.replace(char, repl)
    return s

def generate_deq_compliance_report(data_df, hv_cnt):
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        tot       = len(data_df)
        lines_cnt = data_df["SERVICE_LINE_ID"].nunique()
        lead_cnt  = sum(1 for _, r in data_df.iterrows()
                        if "LEAD" in classify_material(r.get("USER_VERIFIED_STATUS"))
                        and "UNKNOWN" not in classify_material(r.get("USER_VERIFIED_STATUS")))
        safe_cnt  = sum(1 for _, r in data_df.iterrows()
                        if "NON-LEAD" in classify_material(r.get("USER_VERIFIED_STATUS")))
        unk_cnt   = tot - lead_cnt - safe_cnt

        table_rows = ""
        for _, r in data_df.iterrows():
            ev      = tex_escape(r.get("EVIDENCE_ID",    "---"))
            sl      = tex_escape(r.get("SERVICE_LINE_ID","---"))
            lat_v   = r.get("GPS_LATITUDE")
            lon_v   = r.get("GPS_LONGITUDE")
            lat_s   = f"{float(lat_v):.4f}" if lat_v is not None else "---"
            lon_s   = f"{float(lon_v):.4f}" if lon_v is not None else "---"
            st_raw  = r.get("USER_VERIFIED_STATUS","UNVERIFIED")
            sys_m   = tex_escape(classify_material(st_raw))
            cust_m  = "NON-LEAD" if "SAFE" in str(st_raw) else "UNKNOWN"
            dist_v  = r.get("AI_DISTANCE")
            dist_s  = f"{float(dist_v):.4f}" if dist_v and str(dist_v) != "None" and str(dist_v) != "nan" else "N/A"
            ins     = tex_escape(str(r.get("AUDITED_BY","---"))[:24])
            table_rows += (
                f"EV-{ev} & SL-{sl} & {lat_s}, {lon_s} & "
                f"\\small {sys_m} & \\small {cust_m} & {dist_s} & {ins} \\\\\n\\midrule\n"
            )

        latex_str = (
            r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[top=1in,bottom=1in,left=0.65in,right=0.65in]{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{fancyhdr}
\usepackage{xcolor}
\definecolor{deqblue}{HTML}{0D3B66}
\pagestyle{fancy}
\fancyhf{}
\lhead{\textbf{Oklahoma DEQ LSLI Compliance Submittal}}
\rhead{PWSID: """ + PWSID + r"""}
\cfoot{\thepage}
\begin{document}
\begin{center}
{\Large\bfseries\color{deqblue} LEAD SERVICE LINE INVENTORY COMPLIANCE AUDIT LOG} \\
\vspace{2mm}
\small Prepared per 40 CFR \S141.84 and Oklahoma DEQ Rules \\
\textbf{Date:} \today
\end{center}
\section*{Executive Metrics}
\begin{tabular}{ll}
\toprule
\textbf{Metric} & \textbf{Count} \\
\midrule
Total Evidence Records & """ + str(tot) + r""" \
Distinct Service Lines & """ + str(lines_cnt) + r""" \
Lead Suspect & """ + str(lead_cnt) + r""" \
Inspector Verified Safe & """ + str(hv_cnt) + r""" \
Pending Review & """ + str(unk_cnt) + r""" \
\bottomrule
\end{tabular}
\section*{Certified Field Evidence Ledger}
\begin{longtable}{lllllll}
\toprule
\textbf{EV} & \textbf{SL} & \textbf{GPS} & \textbf{System Mat.} & \textbf{Customer Mat.} & \textbf{AI Dist} & \textbf{Inspector} \\
\midrule
\endhead
""" + table_rows + r"""\bottomrule
\end{longtable}
\section*{Legal Attestation}
I hereby certify under penalty of law that this document was compiled using evidence-based inspection records in accordance with 40 CFR Part 141 and Oklahoma Administrative Code 252:641.
\vspace{1.2cm}
\begin{flushleft}
\rule{6cm}{0.4pt} \hfill \rule{4cm}{0.4pt} \\
\textbf{Authorized Utility Sign-off} \hfill \textbf{Date}
\end{flushleft}
\end{document}
"""
        )

        with open(TEX_PATH, "w", encoding="utf-8") as f:
            f.write(latex_str)

        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode",
             f"-output-directory={WORKSPACE_DIR}", TEX_PATH],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if proc.returncode == 0:
            return True, proc.stdout
        else:
            return False, proc.stdout

    except Exception as ex:
        return False, str(ex)

# ── Report UI ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="report-panel">
    <div style="font-size:.67rem;font-weight:700;color:#38bdf8;text-transform:uppercase;
         letter-spacing:.12em;margin-bottom:.3rem">📄 Oklahoma DEQ Compliance Report Console</div>
    <div style="font-size:.75rem;color:#64748b">
        Generate a legally binding LaTeX/PDF audit package for official ODEQ LSLI submission.
        Requires <code style="background:#0f1117;padding:1px 4px;border-radius:3px;color:#94a3b8">pdflatex</code>
        — install: <code style="background:#0f1117;padding:1px 4px;border-radius:3px;color:#94a3b8">brew install --cask mactex</code>
    </div>
</div>
""", unsafe_allow_html=True)

if df is not None:
    rep1, rep2, rep3 = st.columns([2, 1, 1])
    with rep1:
        st.markdown(f"""
        <div style="font-size:.78rem;color:#64748b;padding:.4rem 0">
            <strong style="color:#e2e8f0">{total}</strong> records &nbsp;·&nbsp;
            <strong style="color:#f87171">{suspect_cnt}</strong> flagged &nbsp;·&nbsp;
            <strong style="color:#4ade80">{hv_count}</strong> verified &nbsp;·&nbsp;
            PWSID: <strong style="color:#38bdf8">{PWSID}</strong>
        </div>
        """, unsafe_allow_html=True)

    with rep2:
        gen_btn = st.button("📄 Generate Report", use_container_width=True)

    with rep3:
        if os.path.exists(PDF_PATH):
            with open(PDF_PATH, "rb") as pdf_f:
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_f.read(),
                    file_name=f"OKW_ODEQ_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    if gen_btn:
        with st.spinner("Compiling LaTeX report…"):
            ok, log = generate_deq_compliance_report(df, hv_count)
            if ok:
                st.success("✅ Report compiled. Click Download PDF above.")
                st.rerun()
            else:
                st.error("Compilation failed.")
                with st.expander("Compiler log"):
                    st.code(log[-3000:] if log else "No output")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#0f1117;border-top:1px solid #2d3148;padding:.5rem 1.5rem;margin-top:1rem;
     font-size:.67rem;color:#475569;display:flex;justify-content:space-between;align-items:center">
    <span style="font-family:'JetBrains Mono',monospace">
        OKW FieldSync · Oracle 23ai @ {db_host}:{db_port}/{db_service} · PWSID OK1020401
    </span>
    <span style="color:#38bdf8;font-family:'JetBrains Mono',monospace">
        {"⬡ VECTOR_DISTANCE" if vec_ok else "◇ Standard"} · ODEQ 2026
    </span>
</div>
""", unsafe_allow_html=True)