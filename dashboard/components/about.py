"""Recruiter-facing case study, backed by the recorded model documentation."""
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]

def render_about():
    st.title("About Cash Flow Co-Pilot")
    st.markdown("**An end-to-end machine-learning project for forecasting invoice payments and supporting collections.**")
    st.markdown("Built collaboratively by **Diogo Fernandes and teammates**, with shared contributions across the project. "
                "Diogo also built the frontend during the course. This portfolio edition preserves that frontend and adds a reproducible demonstration and reliability fixes.")
    st.subheader("The business problem")
    st.write("Finance teams need to anticipate cash receipts and decide which outstanding invoices deserve attention. "
             "An invoice due date expresses a contractual deadline; a payment forecast estimates when cash may actually arrive.")
    st.subheader("Try it in two minutes")
    st.write("Open the Cash Flow Co-Pilot tab, load the 24 sample invoices, generate a forecast, run risk predictions, "
             "select an invoice, then generate a collection draft. The sample uses synthetic data at reference date 1 October 2024.")
    st.subheader("How it works")
    st.markdown("""
1. **Validate invoices:** check identifiers, dates, currencies and amounts while preserving row identity.
2. **Create features:** combine invoice details with customer history available at the forecast date.
3. **Predict payment timing:** estimate probabilities for seven intervals: days 1–7, 8–14, 15–21, 22–28, 29–35, 36–42 and 43+.
4. **Forecast receipts:** multiply each invoice amount by its interval probabilities and sum across invoices.
5. **Prioritise collections:** combine invoice amount, probability of payment after 28 days and an overdue multiplier.
6. **Prepare a draft:** use invoice facts and collection policy to produce text for human review. No email is sent.
""")
    st.subheader("The model: XGBoost")
    st.write("The application uses a scikit-learn pipeline with median imputation and an XGBoost multiclass classifier. "
             "It learns an ensemble of boosted decision trees and returns a probability for each payment interval.")
    st.markdown("""**Why it fits this problem:** invoice data is structured and tabular. Boosted trees can capture nonlinear relationships and interactions between amount, age, payment terms and customer behaviour. They work with numeric features without requiring feature scaling, and their interval probabilities support cash-flow aggregation.

This is the rationale for the current model, rather than a claim that it beats every alternative. The reproducible demo compares it with a class-frequency baseline; a fresh real-data comparison is still needed before production use.""")
    st.write("The seven inputs are invoice age, days until due, payment terms, historical customer mean delay, "
             "days since the customer's last invoice, log invoice amount and a sine encoding of invoice month.")
    st.subheader("Evaluation: what the numbers mean")
    report = json.loads((ROOT / "docs/demo_metrics.json").read_text())
    metrics = report["metrics"]
    left, right = st.columns(2)
    left.metric("XGBoost interval accuracy", f'{metrics["model_accuracy"]:.1%}')
    right.metric("Class-frequency baseline accuracy", f'{metrics["baseline_accuracy"]:.1%}')
    st.write(f'The synthetic holdout contains {report["holdout_rows"]:,} snapshot rows. '
             f'Log loss is {metrics["model_log_loss"]:.3f} for XGBoost versus '
             f'{metrics["baseline_log_loss"]:.3f} for the baseline; lower is better.')
    st.write("Training and evaluation are separated in time. Training only uses payment labels observed by its cutoff. "
             "Repeated invoice snapshots match the recurring forecasting task, so they are not independent invoice observations.")
    st.info("These are synthetic demonstration results, not evidence of real-world collection improvements or production accuracy.")
    st.subheader("Technology and architecture")
    st.write("Streamlit and Plotly provide the frontend; FastAPI validates and serves requests; pandas prepares data; "
             "scikit-learn and XGBoost provide the model. Regression tests cover the API and complete dashboard workflow.")
    st.code("Invoice CSV → validation + historical features → XGBoost probabilities\n"
            "                                             ↓\n"
            "                         cash forecast + collection ranking → draft", language="text")
    st.write("The default demonstration uses deterministic local collection rules. The project also includes an optional "
             "Gemini retrieval integration with example playbooks. The demo does not call an external LLM.")
    st.subheader("Limitations and next steps")
    st.markdown("""
- Payment after 28 days is a timing risk, not a probability of default or a measure of lateness against the due date.
- Eventually unpaid invoices are not modelled as a separate outcome; predicted receipts can overstate a real portfolio.
- Probabilities have not been calibrated, and forecasts do not include confidence intervals.
- The 43+ day interval is an open-ended tail, not a seventh-week payment promise.
- Currency conversion uses illustrative historical USD/CAD assumptions.
- Next steps: a new real-data holdout, stronger baselines, censored-outcome modelling, probability calibration and authenticated deployment for private data.
""")
    st.subheader("Source code")
    st.link_button("View Diogo's project repository", "https://github.com/diogofernandes/cf_copilot_dashboard")
    st.caption("Public demonstration: use synthetic or approved example data.")
