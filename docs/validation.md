# Validation — 2026-10-08

- 28 regression tests passed in the project Python 3.11 environment.
- Ruff checks passed across the backend, dashboard and tests.
- Original course theme CSS is protected by a fingerprint regression test.
- Synthetic demo model trained and evaluated; results recorded in demo_metrics.json.
- Live API returned 24 invoice predictions, seven cash-flow intervals and collection rankings.
- Chromium exercised loading the sample, forecasting, ranking, invoice selection and drafting.
- Screenshots in screenshots/ were visually inspected against the original frontend.
- Draft provider was local_rules; drafts require human review and no emails are sent.
- Streamlit health endpoint returned HTTP 200.
- requirements.lock.txt records the tested application dependencies.
- Docker builds and optional cloud/Gemini services have not been exercised.
- Public deployment remains deferred. No changes have been pushed to the team repository.
- The self-contained hosting entry point passed the full Chromium workflow and recruiter-tab check locally.
- CI workflow publication was blocked by the GitHub token's missing workflow scope; local checks passed.
