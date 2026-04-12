"""CAPA Intelligence — Streamlit UI entry point."""

import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

from agent import run_rca, run_capa
from audit import lock_record, export_json
from models import MODELS, DEFAULT_MODEL_NAME

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
APP_TITLE = os.getenv("APP_TITLE", "CAPA Intelligence")
st.set_page_config(page_title=APP_TITLE, page_icon="🔬", layout="wide")

# ── Biocon brand CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather+Sans:wght@300;400;600;700&family=Merriweather:wght@300;400;700&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Merriweather Sans', sans-serif;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* ── Top navbar bar ── */
.biocon-navbar {
    background: #002F59;
    padding: 0 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 999;
    margin: -1rem -1rem 0 -1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
.biocon-navbar-logo {
    font-family: 'Merriweather', serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 2px;
}
.biocon-navbar-logo span {
    color: #4097D8;
}
.biocon-navbar-tagline {
    font-size: 0.75rem;
    color: #70A9DC;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.biocon-navbar-right {
    display: flex;
    align-items: center;
    gap: 2rem;
}
.biocon-nav-link {
    color: #70A9DC;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    text-decoration: none;
}

/* ── Hero banner ── */
.biocon-hero {
    background: linear-gradient(135deg, #002F59 0%, #14518B 60%, #2484C6 100%);
    padding: 3rem 2.5rem 2.5rem;
    margin: 0 -1rem 2rem -1rem;
    color: white;
}
.biocon-hero h1 {
    font-family: 'Merriweather', serif;
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    color: #ffffff;
    line-height: 1.2;
}
.biocon-hero h1 span { color: #4097D8; }
.biocon-hero p {
    font-size: 1rem;
    color: #BDD8F0;
    max-width: 700px;
    margin: 0;
    line-height: 1.6;
}
.biocon-badge {
    display: inline-block;
    background: rgba(64,151,216,0.2);
    border: 1px solid #4097D8;
    color: #70A9DC;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 1rem;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #F5F7FA;
    border-right: 1px solid #DDEAF5;
}
[data-testid="stSidebar"] .sidebar-logo {
    background: #002F59;
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 1.2rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
[data-testid="stSidebar"] .sidebar-logo-text {
    font-family: 'Merriweather', serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: white;
    letter-spacing: 1.5px;
}
[data-testid="stSidebar"] .sidebar-logo-text span { color: #4097D8; }
[data-testid="stSidebar"] label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #003E76 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input {
    border: 1.5px solid #BDD8F0 !important;
    border-radius: 4px !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: #2484C6 !important;
    box-shadow: 0 0 0 2px rgba(36,132,198,0.15) !important;
}

/* ── Section cards ── */
.biocon-card {
    background: #ffffff;
    border: 1px solid #DDEAF5;
    border-left: 4px solid #2484C6;
    border-radius: 6px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,47,89,0.07);
}
.biocon-card-header {
    font-family: 'Merriweather', serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #002F59;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.biocon-card-header .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #2484C6;
    display: inline-block;
}

/* ── Textarea ── */
.stTextArea textarea {
    border: 1.5px solid #BDD8F0 !important;
    border-radius: 5px !important;
    font-size: 0.9rem !important;
    font-family: 'Merriweather Sans', sans-serif !important;
    line-height: 1.6 !important;
    color: #ffffff !important;
}
.stTextArea textarea:focus {
    border-color: #2484C6 !important;
    box-shadow: 0 0 0 3px rgba(36,132,198,0.12) !important;
}
.stTextArea label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #003E76 !important;
}

/* ── Primary button (Run RCA) ── */
.stButton > button[kind="primary"] {
    background: #002F59 !important;
    color: white !important;
    border: 2px solid #002F59 !important;
    border-radius: 5px !important;
    font-family: 'Merriweather Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background: #14518B !important;
    border-color: #14518B !important;
    box-shadow: 0 4px 14px rgba(0,47,89,0.3) !important;
}
.stButton > button[kind="primary"]:disabled {
    background: #8AACCA !important;
    border-color: #8AACCA !important;
}

/* ── Secondary button (Generate CAPA) ── */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #002F59 !important;
    border: 2px solid #2484C6 !important;
    border-radius: 5px !important;
    font-family: 'Merriweather Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #002F59 !important;
    color: white !important;
    border-color: #002F59 !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: #EA6B1A !important;
    color: white !important;
    border: none !important;
    border-radius: 5px !important;
    font-family: 'Merriweather Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.4rem !important;
}
.stDownloadButton > button:hover {
    background: #c55810 !important;
    box-shadow: 0 4px 12px rgba(234,107,26,0.35) !important;
}

/* ── RCA / CAPA output area ── */
.output-panel {
    background: #F0F6FC;
    border: 1px solid #BDD8F0;
    border-radius: 6px;
    padding: 1.5rem 1.75rem;
    margin-top: 1rem;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #1a2a3a;
}
.output-panel h2, .output-panel h3 {
    color: #002F59;
    font-family: 'Merriweather', serif;
}

/* ── Audit expander ── */
[data-testid="stExpander"] {
    border: 1px solid #BDD8F0 !important;
    border-radius: 6px !important;
    background: #F5F7FA !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #002F59 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #DDEAF5 !important;
    border-radius: 5px !important;
}

/* ── Info / compliance strip ── */
.compliance-strip {
    background: #E6F1F9;
    border-left: 4px solid #4097D8;
    border-radius: 0 4px 4px 0;
    padding: 0.6rem 1rem;
    font-size: 0.78rem;
    color: #14518B;
    font-weight: 600;
    letter-spacing: 0.3px;
    margin-bottom: 1.5rem;
}

/* ── Status pills ── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.pill-running { background: #FFF3E0; color: #EA6B1A; border: 1px solid #EA6B1A; }
.pill-done    { background: #E8F5E9; color: #2E7D32; border: 1px solid #4CAF50; }

/* ── Section divider ── */
.biocon-divider {
    border: none;
    border-top: 1px solid #DDEAF5;
    margin: 1.5rem 0;
}

/* ── Footer ── */
.biocon-footer {
    background: #002F59;
    color: #70A9DC;
    text-align: center;
    padding: 1rem;
    font-size: 0.72rem;
    letter-spacing: 0.5px;
    margin: 2rem -1rem -1rem -1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
if "audit_trail" not in st.session_state:
    st.session_state.audit_trail = []
if "last_rca" not in st.session_state:
    st.session_state.last_rca = ""
if "last_capa" not in st.session_state:
    st.session_state.last_capa = ""
if "rca_done" not in st.session_state:
    st.session_state.rca_done = False
if "capa_done" not in st.session_state:
    st.session_state.capa_done = False
if "incident_id" not in st.session_state:
    st.session_state.incident_id = ""
if "run_counter" not in st.session_state:
    st.session_state.run_counter = 0


def _generate_incident_id(site: str) -> str:
    site_code = (site.strip().upper()[:3] or "XXX")
    year = datetime.now(timezone.utc).year
    seq = str(st.session_state.run_counter + 1).zfill(4)
    return f"INC-{site_code}-{year}-{seq}"


# ── Top navbar ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="biocon-navbar">
  <div>
    <div class="biocon-navbar-logo">BIO<span>CON</span></div>
    <div class="biocon-navbar-tagline">Biosimilars &amp; Innovation</div>
  </div>
  <div class="biocon-navbar-right">
    <span class="biocon-nav-link">Quality</span>
    <span class="biocon-nav-link">Manufacturing</span>
    <span class="biocon-nav-link">Compliance</span>
    <span class="biocon-nav-link">Support</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div class="sidebar-logo-text">BIO<span>CON</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**CAPA Intelligence**")
    st.caption("AI-powered RCA & CAPA for pharma GxP environments")
    st.markdown('<hr class="biocon-divider">', unsafe_allow_html=True)

    selected_model_name = st.selectbox(
        "LLM Model",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(DEFAULT_MODEL_NAME),
    )
    selected_model = MODELS[selected_model_name]

    site = st.text_input("Site", placeholder="e.g. Bengaluru Plant 3")
    product = st.text_input("Product", placeholder="e.g. Insulin Glargine")

    default_id = _generate_incident_id(site) if site else f"INC-XXX-{datetime.now(timezone.utc).year}-0001"
    incident_id = st.text_input("Incident ID", value=default_id)
    st.session_state.incident_id = incident_id

    st.markdown('<hr class="biocon-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.72rem; color:#6B8FAF; line-height:1.6;">
      Switch models from the dropdown above — no code changes required.<br><br>
      <strong style="color:#003E76;">Compliance:</strong> 21 CFR Part 11 · EU GMP Annex 11
    </div>
    """, unsafe_allow_html=True)

# ── Hero banner ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="biocon-hero">
  <div class="biocon-badge">GxP Quality Management</div>
  <h1>CAPA <span>Intelligence</span></h1>
  <p>AI-powered Root Cause Analysis and Corrective & Preventive Action planning for pharma manufacturing deviations. Every analysis is cryptographically locked for 21 CFR Part 11 compliance.</p>
</div>
""", unsafe_allow_html=True)

# ── Compliance strip ──────────────────────────────────────────────────────────
st.markdown("""
<div class="compliance-strip">
  &#9679; 21 CFR Part 11 compliant &nbsp;|&nbsp; &#9679; EU GMP Annex 11 &nbsp;|&nbsp;
  &#9679; SHA-256 tamper-evident audit trail &nbsp;|&nbsp; &#9679; Multi-model AI analysis
</div>
""", unsafe_allow_html=True)

# ── Incident input card ───────────────────────────────────────────────────────
st.markdown("""
<div class="biocon-card">
  <div class="biocon-card-header"><span class="dot"></span> Incident Description</div>
</div>
""", unsafe_allow_html=True)

incident_text = st.text_area(
    "Incident Description",
    height=180,
    label_visibility="collapsed",
    placeholder=(
        "Paste your incident description here…\n\n"
        "Example: Batch BLR-IG-2024-0882 of Insulin Glargine biosimilar recorded a yield of "
        "72.4%, against a specification of 86.2% minimum. Post-run investigation found that "
        "bioreactor DO cascade control was disabled following preventive maintenance on the DO probe assembly..."
    ),
)

col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    run_rca_btn = st.button("Run RCA Agent", type="primary", disabled=not incident_text.strip())

# ── RCA output ────────────────────────────────────────────────────────────────
if run_rca_btn and incident_text.strip():
    st.session_state.rca_done = False
    st.session_state.capa_done = False
    st.session_state.last_rca = ""
    st.session_state.last_capa = ""

    st.markdown("""
    <div class="biocon-card">
      <div class="biocon-card-header"><span class="dot"></span> Root Cause Analysis &nbsp;<span class="status-pill pill-running">Analyzing…</span></div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        rca_output = st.write_stream(run_rca(incident_text, selected_model))

    st.session_state.last_rca = rca_output
    st.session_state.rca_done = True
    st.session_state.run_counter += 1

elif st.session_state.rca_done and st.session_state.last_rca:
    st.markdown("""
    <div class="biocon-card">
      <div class="biocon-card-header"><span class="dot"></span> Root Cause Analysis &nbsp;<span class="status-pill pill-done">Complete</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(st.session_state.last_rca)

# ── CAPA section ──────────────────────────────────────────────────────────────
if st.session_state.rca_done:
    st.markdown('<hr class="biocon-divider">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        gen_capa_btn = st.button("Generate CAPA Plan", type="secondary")

    if gen_capa_btn:
        st.session_state.capa_done = False
        st.session_state.last_capa = ""

        st.markdown("""
        <div class="biocon-card">
          <div class="biocon-card-header"><span class="dot"></span> CAPA Action Plan &nbsp;<span class="status-pill pill-running">Generating…</span></div>
        </div>
        """, unsafe_allow_html=True)

        capa_output = st.write_stream(
            run_capa(st.session_state.last_rca, st.session_state.incident_id, selected_model)
        )

        st.session_state.last_capa = capa_output
        st.session_state.capa_done = True

        record = lock_record(
            incident_id=st.session_state.incident_id,
            site=site,
            product=product,
            model=selected_model,
            rca_text=st.session_state.last_rca,
            capa_text=capa_output,
        )
        st.session_state.audit_trail.append(record)

    elif st.session_state.capa_done and st.session_state.last_capa:
        st.markdown("""
        <div class="biocon-card">
          <div class="biocon-card-header"><span class="dot"></span> CAPA Action Plan &nbsp;<span class="status-pill pill-done">Complete</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.last_capa)

# ── Audit trail ───────────────────────────────────────────────────────────────
if st.session_state.audit_trail:
    st.markdown('<hr class="biocon-divider">', unsafe_allow_html=True)
    with st.expander("Audit Trail — Session Records", expanded=False):
        trail_display = [
            {
                "Incident ID":     r["incident_id"],
                "Timestamp (UTC)": r["timestamp_utc"],
                "Site":            r["site"],
                "Product":         r["product"],
                "Model":           r["model"],
                "SHA-256":         r["sha256"][:16] + "…",
                "Locked":          r["locked"],
            }
            for r in st.session_state.audit_trail
        ]
        st.dataframe(trail_display, use_container_width=True)

        latest = st.session_state.audit_trail[-1]
        st.download_button(
            label="Download CAPA Record (.json)",
            data=export_json(latest),
            file_name=f"{latest['incident_id']}_capa_record.json",
            mime="application/json",
        )
        st.markdown("""
        <div style="font-size:0.72rem; color:#14518B; margin-top:0.5rem;">
          SHA-256 hash covers all content fields prior to the <code>locked</code> flag.
          Any post-generation alteration invalidates the hash —
          satisfying 21 CFR Part 11 §11.10(e) and EU GMP Annex 11 §9 integrity requirements.
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="biocon-footer">
  Biocon CAPA Intelligence &nbsp;·&nbsp; Powered by EMB Global AI &nbsp;·&nbsp;
  21 CFR Part 11 · EU GMP Annex 11 &nbsp;·&nbsp; For demonstration purposes only
</div>
""", unsafe_allow_html=True)
