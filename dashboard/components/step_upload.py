"""
components/step_upload.py — Step 01: Upload invoices CSV.
"""

import streamlit as st
import pandas as pd
from io import BytesIO

from dashboard.constants import ICONS
from dashboard.state import adopt_input
from dashboard.services.api import sample_invoices


def render_step_upload():
    st.markdown(f"""
    <div class="step-block">
        <div style="display:flex;align-items:center;justify-content:center;
                    margin-bottom:0.5rem;">{ICONS["upload"]}</div>
        <span class="snum">STEP 01</span>
        <span class="stitle">Upload Invoices CSV</span>
        <span class="sdesc">Upload outstanding invoices or explore the sample portfolio.</span>
    </div>
    """, unsafe_allow_html=True)

    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        uploaded = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed", key=f"upload-{st.session_state.uploader_epoch}")
        st.markdown("""
        <div style="background:rgba(0,212,170,0.04);border:1px solid rgba(0,212,170,0.15);
                    border-radius:10px;padding:1rem;margin-top:0.8rem;text-align:center;">
            <div style="font-size:0.72rem;color:#6b7fa3;margin-bottom:0.5rem;
                        text-transform:uppercase;letter-spacing:0.08em;">Expected columns</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:#00d4aa;line-height:2;">
                doc_id · cust_number · total_open_amount<br>
                invoice_sent · due_in_date<br>
                Optional: name_customer · invoice_currency
            </div>
        </div>""", unsafe_allow_html=True)

    with col_c:
        info = st.session_state.get("service_info", {})
        if info.get("demo_mode"):
            st.caption("Synthetic demonstration · trained XGBoost · local collection drafts. No email is sent.")
            if st.button("Load sample invoices", key="btn_sample", width="stretch"):
                content, error = sample_invoices()
                if error:
                    st.error(error)
                else:
                    st.session_state.sample_bytes = content
                    st.session_state.sample_pending = True
        with st.expander("Upload details"):
            reference = st.date_input("Forecast reference date", value=pd.Timestamp(st.session_state.reference_date).date())
            st.session_state.reference_date = str(reference)
            st.caption("ISO or YYYYMMDD dates. Unique invoice IDs. Maximum 5 MB and 10,000 rows. USD/CAD supported.")
        if st.session_state.get("sample_pending"):
            content = st.session_state.sample_bytes
            st.session_state.sample_pending = False
            st.session_state.active_source = "sample"
            st.session_state.last_upload = uploaded.getvalue() if uploaded else None
        elif uploaded and uploaded.getvalue() != st.session_state.get("last_upload"):
            content = uploaded.getvalue()
            st.session_state.last_upload = content
            st.session_state.active_source = "upload"
        elif st.session_state.get("active_source") == "upload":
            content = uploaded.getvalue() if uploaded else None
        else:
            content = st.session_state.sample_bytes
        if content is not None:
            adopt_input(content, reference)
            if st.session_state.upload_error:
                st.error(st.session_state.upload_error)
            elif st.session_state.df is not None:
                df = st.session_state.df
                st.success(f"Loaded {len(df):,} invoices — $" + f"{df['total_open_amount'].sum():,.0f} outstanding (USD)")
                st.download_button("Download current invoices", st.session_state.uploaded_bytes, "invoices.csv", "text/csv")
        elif st.session_state.df is not None:
            from dashboard.state import reset_state
            reset_state()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
