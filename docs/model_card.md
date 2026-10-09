# Model card

## Intended use
A portfolio demonstration of invoice payment timing and expected cash aggregation.
A trained model can support review of receivables; it does not decide credit, payment enforcement,
or legal action. The default model is fitted to reproducible synthetic data.

## Features and model
Invoice timing, customer behaviour and amount features feed a scikit-learn pipeline. Numeric features use median imputation, and invoice size uses ordinal encoding. A RandomForestClassifier combines tree predictions using seed 42.
Internal classes 0–6 map consistently to public buckets 1–7.

## Prediction intervals
Days 1–7, 8–14, 15–21, 22–28, 29–35, 36–42, and 43+ after the reference date.
Day 7 belongs to the first interval. The tail is open ended.
Expected amounts across all seven intervals sum to normalized invoice totals, up to rounding.

## Evaluation
Training snapshots and holdout snapshots are separated in time. Training labels must be paid
and observed by the training cutoff. Repeated snapshots of an invoice represent the intended
recurring-forecast task; metrics are not independent per-invoice observations.
A prior-frequency DummyClassifier is the synthetic baseline. Recorded scores live in demo_metrics.json.
Cash-flow evaluation covers six finite weeks; it excludes the open-ended tail.
The synthetic demo's parameters are fixed; no tuning uses its holdout.

## Historical dataset
The original research uses the [Payment Date Prediction for Invoices dataset](https://www.kaggle.com/datasets/pradumn203/payment-date-prediction-for-invoices-dataset).
Historical data and credentials are not included in the public demo.
Historical experiments may have tuned parameters using overlapping periods;
a new final untouched holdout is necessary before claiming real-world model quality.
Only eventually paid invoices receive exact timing targets. Unpaid invoices are right-censored:
the current classifier does not estimate nonpayment and may overstate receipts on a real portfolio.

## Probability and cash assumptions
Model probabilities are used directly. Arbitrary sharpening has been removed.
Calibration curves are diagnostics; they do not mean probabilities have been calibrated.
No confidence interval is estimated. A class-prior baseline may outperform Random Forest on a different distribution.
Amounts are converted to USD. Historical CAD conversion rates:
2018 0.771, 2019 0.754, 2020 0.745; other years use 0.75.
These are illustrative approximations, unsuitable for live accounting without supplied FX rates.
USD and CAD are supported; other currencies are rejected.

## Collection scores
Risk = P(payment after 28 days). This is not delinquency relative to contractual due date
and is not a probability of default. Priority = normalized amount × risk × overdue multiplier:
1.0 when not overdue, 1.2 for 1–6 days, 1.5 for 7–29 days, 2.0 for 30+ days.
These weights are a human-designed heuristic.

## Drafts and privacy
Default drafts use a small local demonstration policy. Optional Gemini retrieval uses the example
company playbooks, and exposes source references. Human review is required; no email is sent.
Optional provider calls may send invoice facts to Gemini. Use synthetic or approved data.
API endpoints have no authentication; run locally, or add access control before hosting private invoice data.

## Known limitations
Synthetic behavior is deliberately learnable and cannot substantiate production outcomes.
Dataset age, customer mix, changing payment terms and economic conditions can shift model behavior.
Snapshot repetition and eventual-payment selection affect reported metrics.
There is no fairness analysis, drift monitoring, survival model, fitted calibration or causal outcome evaluation.

## Project provenance
Final Le Wagon team project: https://github.com/EwaltsJ/cf_copilot
The original README specifies Random Forest, but the current team model.py instantiates XGBoost. This portfolio demonstration follows the README at the user's request. Synthetic results are newly generated with RandomForestClassifier, not the original team's historical metrics.
