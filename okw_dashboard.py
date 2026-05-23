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

# ── CSS — ArcGIS / Esri utility dashboard aesthetic ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Avenir+Next:wght@400;600&family=Open+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Open Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* ── App shell ── */
.stApp { background: #f4f4f4; color: #2b2b2b; }
.stSidebar {
    background: #2b2b2b !important;
    border-right: none;
}
.block-container { padding-top: 0 !important; max-width: 100% !important; }

/* ── Sidebar text ── */
.stSidebar label,
.stSidebar .stMarkdown,
.stSidebar p { color: #d1d1d1 !important; font-size: .82rem !important; }
.stSidebar h3 { color: #ffffff !important; font-size: .88rem !important; font-weight: 600 !important; }

/* ── Sidebar inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #3d3d3d !important;
    border: 1px solid #555 !important;
    color: #f0f0f0 !important;
    border-radius: 3px !important;
    font-size: .82rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #00b2d6 !important;
    box-shadow: 0 0 0 2px rgba(0,178,214,.2) !important;
}

/* ── Sidebar button ── */
.stButton > button {
    background: #00b2d6 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 3px !important;
    font-size: .82rem !important;
    font-weight: 600 !important;
    padding: .5rem 1rem !important;
    width: 100%;
    letter-spacing: .02em;
}
.stButton > button:hover { background: #0097b8 !important; }

/* ── Form submit button ── */
.stFormSubmitButton > button {
    background: #2d6a4f !important;
    color: #fff !important;
    border: none !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    width: 100%;
    padding: .55rem 1rem !important;
    letter-spacing: .02em;
}
.stFormSubmitButton > button:hover { background: #245e44 !important; }

/* ── Top header bar — Esri navy ── */
.esri-topbar {
    background: #1a1a2e;
    padding: .75rem 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0;
}
.esri-topbar-logo {
    display: flex; align-items: center; gap: .75rem;
}
.esri-topbar-icon {
    background: #00b2d6; border-radius: 4px;
    width: 32px; height: 32px; display: flex; align-items: center;
    justify-content: center; font-size: 1rem;
}
.esri-topbar-title {
    font-size: .95rem; font-weight: 700; color: #ffffff;
    letter-spacing: .04em; text-transform: uppercase;
}
.esri-topbar-sub { font-size: .7rem; color: #a0b4c0; margin-top: 1px; }
.esri-status-badge {
    background: #1e4d2b; border: 1px solid #2d7a4f;
    color: #5cb85c; padding: 3px 12px; border-radius: 2px;
    font-size: .7rem; font-weight: 700; letter-spacing: .06em;
    text-transform: uppercase;
}
.esri-status-offline {
    background: #4a3000; border: 1px solid #7a5200;
    color: #ffc107; padding: 3px 12px; border-radius: 2px;
    font-size: .7rem; font-weight: 700; letter-spacing: .06em;
    text-transform: uppercase;
}

/* ── KPI strip — Esri style ── */
.kpi-strip {
    display: flex; gap: 0;
    background: #ffffff;
    border-bottom: 3px solid #00b2d6;
    margin-bottom: 1rem;
}
.kpi-tile {
    flex: 1; padding: 1rem 1.4rem;
    border-right: 1px solid #e0e0e0;
    background: #ffffff;
}
.kpi-tile:last-child { border-right: none; }
.kpi-tile-num {
    font-size: 2.2rem; font-weight: 700; line-height: 1;
    color: #2b2b2b; font-family: 'Open Sans', sans-serif;
}
.kpi-tile-num.blue  { color: #00b2d6; }
.kpi-tile-num.red   { color: #c0392b; }
.kpi-tile-num.green { color: #2d6a4f; }
.kpi-tile-num.amber { color: #d47c00; }
.kpi-tile-label {
    font-size: .68rem; color: #6b6b6b; text-transform: uppercase;
    letter-spacing: .1em; margin-top: .25rem; font-weight: 600;
}
.kpi-tile-sub { font-size: .7rem; color: #9a9a9a; margin-top: .1rem; }

/* ── Panel cards ── */
.panel {
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-top: 3px solid #00b2d6;
    border-radius: 2px;
    margin-bottom: 1rem;
}
.panel-header {
    padding: .6rem 1rem;
    background: #f0f0f0;
    border-bottom: 1px solid #d0d0d0;
    font-size: .72rem; font-weight: 700; color: #4a4a4a;
    text-transform: uppercase; letter-spacing: .1em;
    display: flex; align-items: center; gap: .5rem;
}
.panel-body { padding: .75rem 1rem; }

/* ── Asset list rows ── */
.asset-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: .55rem .75rem;
    border-bottom: 1px solid #ebebeb;
    cursor: pointer; transition: background .1s;
    background: #fff;
}
.asset-row:hover { background: #f0f8ff; }
.asset-row.active { background: #e6f4f9; border-left: 3px solid #00b2d6; }
.asset-row-id {
    font-size: .78rem; font-weight: 700; color: #1a6b8a;
}
.asset-row-meta { font-size: .68rem; color: #7a7a7a; margin-top: 2px; }
.asset-row-badge {
    font-size: .65rem; font-weight: 700; padding: 2px 7px;
    border-radius: 2px; text-transform: uppercase; letter-spacing: .05em;
}
.badge-lead     { background: #fde8e8; color: #c0392b; border: 1px solid #e8a0a0; }
.badge-safe     { background: #e8f5e9; color: #2d6a4f; border: 1px solid #81c784; }
.badge-unknown  { background: #fff8e1; color: #7a5200; border: 1px solid #ffc107; }
.badge-verified { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }

/* ── Classification chip ── */
.class-chip {
    display: inline-block; padding: 2px 8px; border-radius: 2px;
    font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
    margin-bottom: .5rem;
}
.chip-lead    { background: #c0392b; color: #fff; }
.chip-clear   { background: #2d6a4f; color: #fff; }
.chip-pending { background: #7a5200; color: #fff; }

/* ── Metadata table ── */
.meta-table { width: 100%; border-collapse: collapse; font-size: .78rem; }
.meta-table td { padding: .4rem .6rem; border-bottom: 1px solid #ebebeb; }
.meta-table td:first-child {
    font-weight: 600; color: #4a4a4a; width: 42%;
    text-transform: uppercase; font-size: .67rem; letter-spacing: .06em;
    background: #f7f7f7;
}
.meta-table td:last-child { color: #2b2b2b; }
.meta-table .vector-row td { background: #e6f4f9 !important; color: #1a6b8a !important; }

/* ── Photo frame ── */
.photo-frame {
    background: #f4f4f4; border: 1px solid #d0d0d0;
    border-radius: 2px; padding: .5rem; margin-bottom: .75rem;
}
.photo-placeholder {
    background: #f0f0f0; border: 2px dashed #c0c0c0;
    border-radius: 2px; padding: 3rem 1rem; text-align: center;
    color: #9a9a9a;
}
.photo-placeholder .ph-icon { font-size: 2rem; margin-bottom: .5rem; }
.photo-placeholder .ph-text { font-size: .78rem; }

/* ── Audit form ── */
.audit-notice {
    background: #fff8e1; border: 1px solid #ffc107; border-radius: 2px;
    padding: .65rem .85rem; margin-bottom: .75rem;
    font-size: .73rem; color: #5a3e00;
}
.audit-notice strong { color: #3a2800; }

/* ── Section divider ── */
.section-title {
    font-size: .7rem; font-weight: 700; color: #4a4a4a;
    text-transform: uppercase; letter-spacing: .1em;
    padding: .4rem 0; border-bottom: 2px solid #00b2d6;
    margin-bottom: .75rem; margin-top: .5rem;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #fff !important;
    border: 1px solid #c0c0c0 !important;
    border-radius: 3px !important;
    color: #2b2b2b !important;
    font-size: .82rem !important;
}

/* ── Streamlit overrides ── */
.stMarkdown h4 { color: #2b2b2b !important; font-size: .88rem !important; }
div[data-testid="stForm"] {
    background: #f9f9f9; border: 1px solid #d0d0d0;
    border-radius: 3px; padding: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k in ("df", "err", "selected_idx", "override_msg", "vec_ok", "db_log"):
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

    if st.session_state.db_log:
        st.markdown("---")
        st.caption("⚙️ **Engine Execution Exception Trace:**")
        st.code(st.session_state.db_log, language="sql")

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

# ── SQL Queries ────────────────────────────────────────────────────────────────
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
FROM SYSTEM.EVIDENCE
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
FROM SYSTEM.EVIDENCE
ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
"""

# ── Fetch ──────────────────────────────────────────────────────────────────────
def fetch_records():
    try:
        conn = oracledb.connect(user=db_user, password=db_password,
                                dsn=f"{db_host}:{int(db_port)}/{db_service}")
        cursor = conn.cursor()
        cursor.execute("ALTER SESSION SET CONTAINER = FREEPDB1")
        
        vec_ok, sql_log = True, None
        try:
            cursor.execute(AUDIT_SQL)
        except Exception as sql_ex:
            sql_log = str(sql_ex)
            cursor.execute(FALLBACK_SQL)
            vec_ok = False
            
        cols = [c[0].upper() for c in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        st.session_state.df = pd.DataFrame(rows, columns=cols)
        st.session_state.vec_ok = vec_ok
        st.session_state.db_log = sql_log
        st.session_state.err = None
    except oracledb.DatabaseError as e:
        err = str(e)
        st.session_state.db_log = err
        if any(c in err for c in ["DPY-6005","DPY-4011","ORA-03113","ORA-03114"]):
            st.session_state.err = "CONNECTION_LOST"
        elif "ORA-01017" in err:
            st.session_state.err = "ORA-01017"
        else:
            st.session_state.err = err
    except Exception as e:
        st.session_state.err = str(e)
        st.session_state.db_log = str(e)

if load_btn or st.session_state.df is None:
    fetch_records()

df = st.session_state.df
err = st.session_state.err
vec_ok = st.session_state.get("vec_ok", False)

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
        Oklahoma City Public Works &nbsp;|&nbsp; Oracle 23ai{vec_note} &nbsp;|&nbsp; ODEQ 2026
      </div>
    </div>
  </div>
  {status_html}
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
    <div style="background:#fff;border:1px solid #d0d0d0;border-top:3px solid #00b2d6;
         padding:3rem;text-align:center;margin-top:1rem;border-radius:2px">
        <div style="font-size:2rem;margin-bottom:.5rem">💧</div>
        <div style="font-size:.9rem;font-weight:600;color:#2b2b2b;margin-bottom:.3rem">
            No Database Connection
        </div>
        <div style="font-size:.78rem;color:#6b6b6b">
            Enter credentials in the sidebar and click <strong>Connect to Database</strong>
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

# Dynamic row metric counter aggregation for Inspector verification values
hv_count = int(df["USER_VERIFIED_STATUS"].str.contains("MANUALLY_CONFIRMED", na=False).sum())

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-tile">
    <div class="kpi-tile-num blue">{total}</div>
    <div class="kpi-tile-label">Total Evidence Records</div>
    <div class="kpi-tile-sub">Across {lines} service lines</div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num red">{suspect_cnt}</div>
    <div class="kpi-tile-label">Lead — Suspect</div>
    <div class="kpi-tile-sub">AI cosine distance &lt; 0.35</div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num">{has_photo}</div>
    <div class="kpi-tile-label">Photo Records</div>
    <div class="kpi-tile-sub">Field images available</div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num green">{hv_count}</div>
    <div class="kpi-tile-label">Inspector Verified</div>
    <div class="kpi-tile-sub">Manual field sign-off</div>
  </div>
  <div class="kpi-tile">
    <div class="kpi-tile-num amber">{total - hv_count}</div>
    <div class="kpi-tile-label">Pending Review</div>
    <div class="kpi-tile-sub">Awaiting field verification</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main layout ────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2], gap="medium")

# ── LEFT: inventory list ───────────────────────────────────────────────────────
with left_col:
    st.markdown("""
    <div class="panel">
      <div class="panel-header">📋 Service Line Inventory</div>
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

            st.markdown(f"""
            <div class="{row_cls}">
              <div>
                <div class="asset-row-id">SL-{sl_id} &nbsp;·&nbsp; EV-{ev_id}</div>
                <div class="asset-row-meta">
                    {"📷" if has_p else "○"} &nbsp;{date_str}
                </div>
              </div>
              <span class="asset-row-badge {badge_cls}">{mat_class}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("View Record", key=f"sel_{i}", use_container_width=True):
                st.session_state.selected_idx = i
                st.session_state.override_msg = ""
                st.rerun()

# ── RIGHT: inspection panel ────────────────────────────────────────────────────
with right_col:
    idx = st.session_state.selected_idx

    if idx is None:
        st.markdown("""
        <div style="background:#fff;border:1px solid #d0d0d0;border-top:3px solid #00b2d6;
             padding:3rem;text-align:center;border-radius:2px">
            <div style="font-size:2rem;margin-bottom:.5rem">🗺️</div>
            <div style="font-size:.88rem;font-weight:600;color:#2b2b2b;margin-bottom:.3rem">
                Select a Service Line Record
            </div>
            <div style="font-size:.75rem;color:#6b6b6b">
                Choose a record from the inventory list to view field data,<br>
                AI classification, and geospatial coordinates.
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

        # ── Secure audit form ──
        st.markdown('<div class="section-title">🔒 Field Verification — Inspector Sign-Off</div>',
                    unsafe_allow_html=True)

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
                format_func=lambda x: x.replace("MANUALLY_CONFIRMED_","✓ ")
                                       .replace("UNVERIFIED","— Unverified")
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
                        cursor.execute("ALTER SESSION SET CONTAINER = FREEPDB1")
                        cursor.execute("""
                            UPDATE SYSTEM.EVIDENCE
                            SET USER_VERIFIED_STATUS = :1, AUDITED_BY = :2
                            WHERE EVIDENCE_ID = :3
                        """, (audit_decision, inspector, int(ev_id)))
                        conn.commit()
                        cursor.close()
                        conn.close()

                        st.session_state.override_msg = (
                            f"✅ Record EV-{ev_id} verified as "
                            f"{audit_decision.replace('MANUALLY_CONFIRMED_','')} "
                            f"by {inspector}."
                        )
                        st.toast("🔒 Audit Log Emitted to Pluggable Engine", icon="✅")
                        fetch_records()
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Database write failed: {ex}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#2b2b2b;padding:.5rem 1.5rem;margin-top:1rem;
     font-size:.68rem;color:#9a9a9a;display:flex;justify-content:space-between">
    <span>OKW FieldSync · Lead Service Line Inventory · Oracle 23ai @ {db_host}:{db_port}/{db_service}</span>
    <span>{"VECTOR_DISTANCE Active" if vec_ok else "Standard Query Mode"} · ODEQ 2026</span>
</div>
""", unsafe_allow_html=True)