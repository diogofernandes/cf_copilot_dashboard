import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from cf_copilot.api.fast import app
from cf_copilot.ml_logic.schema import normalize_invoices


class Model:
    classes_ = np.arange(7)

    def predict_proba(self, X):
        p = np.zeros((len(X), 7))
        p[:, 0] = 0.4
        p[:, 4] = 0.6
        return p


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("EMAIL_PROVIDER", "local_rules")
    from cf_copilot import demo

    history = normalize_invoices(
        pd.DataFrame(
            {
                "doc_id": ["history"],
                "cust_number": ["001"],
                "total_open_amount": [100],
                "invoice_sent": ["2024-01-01"],
                "due_in_date": ["2024-01-15"],
                "invoice_paid": ["2024-01-20"],
            }
        )
    )
    monkeypatch.setattr(demo, "prepare_demo", lambda: (Model(), history, {"dataset": "test fixture"}))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def csv():
    return b"doc_id,cust_number,name_customer,total_open_amount,invoice_sent,due_in_date\nB,001,Example B,100,2024-09-20,2024-10-05\nA,002,Example A,200,2024-09-10,2024-09-24\n"


def upload(client, path, csv, **data):
    return client.post(path, files={"file": ("invoices.csv", csv, "text/csv")}, data=data)


def test_health_and_sample(client):
    assert client.get("/health").json()["model_ready"]
    assert client.get("/demo/invoices").status_code == 200
    assert client.get("/model-info").json()["currency"] == "USD"


def test_prediction_contract(client, csv):
    response = upload(client, "/predict", csv)
    assert response.status_code == 200
    rows = response.json()["predictions"]
    assert [row["doc_id"] for row in rows] == ["B", "A"]
    assert all(row["predicted_bucket"] == 5 for row in rows)
    assert all(set(row["bucket_probabilities"]) == {f"week_{i}" for i in range(1, 8)} for row in rows)
    assert all(sum(row["bucket_probabilities"].values()) == pytest.approx(1) for row in rows)


def test_forecast_and_ranking(client, csv):
    forecast = upload(client, "/predict_cashflow", csv).json()
    assert len(forecast) == 7
    assert sum(row["forecast_cash"] for row in forecast) == pytest.approx(300)
    ranking = upload(client, "/prioritise_invoices", csv).json()
    assert ranking[0]["doc_id"] == "A"
    assert ranking[0]["risk_score"] == pytest.approx(0.6)
    draft = client.post(
        "/rag_script",
        json={
            key: ranking[0][key]
            for key in [
                "doc_id",
                "cust_number",
                "name_customer",
                "total_open_amount",
                "due_in_date",
                "days_past_due",
                "cust_late_ratio",
            ]
        },
    )
    assert draft.status_code == 200
    assert draft.json()["provider"] == "local_rules"
    assert draft.json()["action"] == "draft_email"
    assert "Example A" in draft.json()["email_body"]


@pytest.mark.parametrize("path", ["/predict", "/predict_cashflow", "/prioritise_invoices"])
def test_bad_csv_returns_422(client, path):
    assert upload(client, path, b"amount\n100\n").status_code == 422
    assert upload(client, path, b"").status_code == 422


def test_missing_model_is_service_error(client, csv):
    app.state.pipeline = None
    assert upload(client, "/predict", csv).status_code == 503
    assert not client.get("/health").json()["model_ready"]


def test_invalid_reference_date(client, csv):
    assert upload(client, "/predict", csv, reference_date="not-a-date").status_code == 422


def test_upload_limit(client, monkeypatch):
    import cf_copilot.api.fast as api

    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 8)
    assert upload(client, "/predict", b"too-large-content").status_code == 413


def test_unknown_invoice_can_receive_draft(client):
    response = client.post(
        "/rag_script",
        json={
            "doc_id": "new-invoice",
            "cust_number": "C-NEW",
            "name_customer": "New customer",
            "total_open_amount": 100,
            "due_in_date": "2024-09-20",
            "days_past_due": 11,
        },
    )
    assert response.status_code == 200
    assert "New customer" in response.json()["email_body"]
