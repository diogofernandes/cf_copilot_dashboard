# CF Copilot — portfolio case study

## Problem
Finance teams need to understand expected receipts and decide which outstanding invoices deserve attention.
A due-date spreadsheet does not express uncertainty about when cash will arrive.

## Contribution and collaboration
Diogo Fernandes worked collaboratively with teammates across the project.
Contributions were shared across data preparation, experiments, forecasting, collection ranking,
API integration, the dashboard and retrieval-based drafts.
This portfolio edition refines that shared work with a reproducible local demonstration,
validation, corrected prediction alignment, temporal label availability and regression checks.

## Technical decisions
- Train payment timing rather than presenting contractual due dates as predictions.
- Aggregate probability-weighted receipts, retaining an explicit long-payment tail.
- Compute customer history as of a forecast reference date.
- Keep invoice identifiers aligned through every transformation.
- Separate model probability from a transparent collections-priority heuristic.
- Make optional LLM drafts distinguishable from deterministic local policy.
- Compare against a baseline and state the limitations of synthetic evaluation.

## Demonstration script
1. Start the API and dashboard.
2. Load the 24 synthetic sample invoices at reference date 2024-10-01.
3. Generate a cash-flow forecast; explain the six finite weeks and 43+ day tail.
4. Rank invoices; explain amount, delay probability and overdue multiplier.
5. Select a customer and prepare a collection draft; point out provider and human review.
6. Show the API documentation, tests, model card and baseline comparison.

## Claims to make
Built a collaborative end-to-end invoice intelligence prototype using Random Forest, FastAPI and Streamlit.
Created a local demonstration with validated inputs, consistent payment intervals and temporally constrained evaluation.
Integrated optional playbook retrieval for reviewable collection drafts.

## Claims to avoid
Do not claim reduced overdue balances, production adoption, calibrated confidence, default detection,
automated email delivery, or sole authorship. Synthetic holdout performance is explicitly synthetic.

## Future work
Evaluate against contractual due-date and customer-history baselines on a new untouched real-data holdout.
Model right-censored invoices, fit probability calibration on a separate validation window,
add authenticated hosting and measured collection outcomes.
