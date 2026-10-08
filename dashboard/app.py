"""
app.py — Cash Flow Copilot Dashboard v04 (refactored)

Entry point: streamlit run app.py

Pipeline: Upload → Forecast → Predict Risk → AI Email (4 steps)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st

st.set_page_config(
    page_title="Cash Flow Copilot",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Bootstrap ─────────────────────────────────────────────────────────
from dashboard.state import init_state
from dashboard.styles.theme import inject_css

init_state()
inject_css()

from dashboard.services.api import service_info
st.session_state.service_info = service_info()
if st.session_state.reference_date is None:
    st.session_state.reference_date = st.session_state.service_info.get('reference_date', '2024-10-01')

# ── Landing sections ──────────────────────────────────────────────────
from dashboard.components.landing import (
    render_nav,
    render_hero,
    render_how_it_works,
    render_cta_banner,
    render_footer,
)

render_nav()
st.markdown("""
<style>
[data-testid="stTabs"] button p { color: #a9bad2 !important; }
[data-testid="stTabs"] button[aria-selected="true"] p { color: #00d4aa !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #00d4aa !important; }
.st-key-project_about { padding: 1.5rem 0; max-width: 1050px; margin: auto; }
.st-key-project_about, .st-key-project_about p, .st-key-project_about li { color: #a9bad2; }
.st-key-project_about h1, .st-key-project_about h2, .st-key-project_about h3,
.st-key-project_about strong, .st-key-project_about [data-testid="stMetricValue"] { color: #f3f7fc; }
.st-key-project_about a { color: #00d4aa; }
.st-key-project_about [data-testid="stCode"] { background: #122035; color: #f3f7fc; }
</style>
""", unsafe_allow_html=True)
demo_tab, about_tab = st.tabs(["Cash Flow Co-Pilot", "About the project"])
with about_tab:
    from dashboard.components.about import render_about
    with st.container(key="project_about"):
        render_about()

with demo_tab:
    render_hero()
    render_how_it_works()
    render_cta_banner()

    # ── Pipeline ──────────────────────────────────────────────────────────
    from dashboard.components.progress_bar import render_progress_bar
    from dashboard.components.step_upload import render_step_upload
    from dashboard.components.step_forecast import render_step_forecast
    from dashboard.components.step_risk import render_step_risk
    from dashboard.components.step_email import render_step_email

    render_progress_bar()
    render_step_upload()
    render_step_forecast()
    render_step_risk()
    render_step_email()

# ── Footer ────────────────────────────────────────────────────────────
render_footer()
