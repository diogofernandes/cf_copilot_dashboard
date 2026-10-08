# Public portfolio deployment

## Streamlit Community Cloud

The public entry point is portfolio_app.py. It starts the same FastAPI backend on a loopback-only port inside the Streamlit process. Cached startup shares one model across sessions; invoice selections and results remain session-local.

Public hosting forces synthetic demo mode and local drafts. No Kaggle, Gemini, GCP or MLflow credentials are needed. Only synthetic or approved example invoice data should be used.

Deploy from Diogo's personal repository, never the original team repository:

- Repository: diogofernandes/cf_copilot_dashboard
- Branch: the prepared portfolio branch
- Main file: portfolio_app.py
- Python: 3.11
- Dependencies: root requirements.txt and packages.txt
- Choose an available descriptive subdomain during deployment.

The hosted website opens the working dashboard by default. The About the project tab contains the recruiter case study.

The eventual CV URL must be the verified deployed app URL, not localhost or a proposed subdomain. A public URL has not been provisioned yet.

## Local hosting smoke test

Run: streamlit run portfolio_app.py --server.port=8502
This checks the self-contained public deployment path without the separately started development API.
