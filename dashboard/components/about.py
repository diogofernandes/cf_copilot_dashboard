"""Recruiter-facing case study, backed by the recorded model documentation."""
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]

def render_about():
    st.title("About Cash Flow Co-Pilot")
    st.markdown("**An end-to-end machine-learning project for forecasting invoice payments and supporting collections.**")
    st.write("Final team project completed at Le Wagon. This website is an interactive portfolio showcase of the project.")
    st.subheader("The business problem")
    st.write("Finance teams need to anticipate cash receipts and decide which outstanding invoices deserve attention. "
             "An invoice due date expresses a contractual deadline, a payment forecast estimates when cash may actually arrive.")
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
    st.subheader("The model: Random Forest")
    st.write("The application uses a scikit-learn pipeline with median imputation and a Random Forest multiclass classifier, with ordinal encoding for the invoice size category. "
             "It combines the predictions of multiple decision trees and returns a probability for each payment interval.")
    st.markdown("""**Why it fits this problem:** invoice data is structured and tabular. Random forests can capture nonlinear relationships and interactions between amount, age, payment terms and customer behaviour. Combining trees trained on resampled data helps reduce the variance of an individual tree. Feature scaling is not required, and their interval probabilities support cash-flow aggregation.

This is the rationale for the current model, rather than a claim that it beats every alternative. The reproducible demo compares it with a class-frequency baseline, a fresh real-data comparison is still needed before production use.""")
    st.write("Features include invoice age, days until due, payment terms, calendar months, historical customer mean delay, "
             "late-payment ratio, transaction count, days since the customer's last invoice, a composite customer risk score, open amount, log amount and invoice size category.")
    st.subheader("Evaluation: what the numbers mean")
    report = json.loads((ROOT / "docs/demo_metrics.json").read_text())
    metrics = report["metrics"]
    left, right = st.columns(2)
    left.metric("Random Forest interval accuracy", f'{metrics["model_accuracy"]:.1%}')
    right.metric("Class-frequency baseline accuracy", f'{metrics["baseline_accuracy"]:.1%}')
    st.write(f'The synthetic holdout contains {report["holdout_rows"]:,} snapshot rows. '
             f'Log loss is {metrics["model_log_loss"]:.3f} for Random Forest versus '
             f'{metrics["baseline_log_loss"]:.3f} for the baseline, lower is better.')
    st.write("Training uses an 80/20 chronological cutoff, followed by evaluation on later snapshots. Training only uses payment labels observed by its cutoff. "
             "Repeated invoice snapshots match the recurring forecasting task, so they are not independent invoice observations.")
    st.info("These are synthetic demonstration results, not evidence of real-world collection improvements or production accuracy.")
    st.subheader("Technology and architecture")
    st.write("Streamlit and Plotly provide the frontend, FastAPI validates and serves requests, pandas prepares data, "
             "scikit-learn and Random Forest provide the model. Regression tests cover the API and complete dashboard workflow.")
    st.write("The default demonstration uses deterministic local collection rules. The project also includes an optional "
             "Gemini retrieval integration with example playbooks. The demo does not call an external LLM.")
    st.subheader("Limitations and next steps")
    st.markdown("""
- Payment after 28 days is a timing risk, not a probability of default or a measure of lateness against the due date.
- Eventually unpaid invoices are not modelled as a separate outcome, predicted receipts can overstate a real portfolio.
- Probabilities have not been calibrated, and forecasts do not include confidence intervals.
- The 43+ day interval is an open-ended tail, not a seventh-week payment promise.
- Currency conversion uses illustrative historical USD/CAD assumptions.
- Next steps: a new real-data holdout, stronger baselines, censored-outcome modelling, probability calibration and authenticated deployment for private data.
""")
    st.subheader("Source code")
    st.link_button("Original Le Wagon team project", "https://github.com/EwaltsJ/cf_copilot")
    st.link_button("Portfolio showcase source", "https://github.com/diogofernandes/cf_copilot_dashboard")
    st.caption("Public demonstration: use synthetic or approved example data.")
