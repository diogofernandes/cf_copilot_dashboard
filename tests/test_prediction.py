import numpy as np
import pandas as pd
import pytest
from cf_copilot.ml_logic.registry import predict
from cf_copilot.ml_logic.schema import normalize_invoices, payment_bucket
from cf_copilot.cashflow_prediction.registry import predict_cashflow
from cf_copilot.collection_ranking.invoices_ranker import get_priority_invoices
from cf_copilot.ml_logic.temporal import temporal_split


class AmountModel:
    classes_ = np.arange(7)

    def predict_proba(self, X):
        result = np.zeros((len(X), 7))
        result[np.arange(len(X)), (X.invoice_amount_log > np.log1p(100)).astype(int)] = 1
        return result


@pytest.fixture
def invoices():
    return pd.DataFrame(
        {
            "doc_id": ["second", "first"],
            "cust_number": ["0002", "0001"],
            "name_customer": ["B", "A"],
            "total_open_amount": [200.0, 50.0],
            "invoice_sent": ["2024-09-10", "2024-09-01"],
            "due_in_date": ["2024-09-24", "2024-09-15"],
        }
    )


@pytest.fixture
def history(invoices):
    df = normalize_invoices(invoices)
    df["invoice_paid"] = pd.to_datetime(["2024-09-25", "2024-09-17"])
    return df


def test_bucket_boundaries():
    assert payment_bucket([1, 7, 8, 14, 15, 21, 22, 28, 29, 35, 36, 42, 43, 99]).tolist() == [
        0,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
    ]


def test_prediction_keeps_invoice_identity(invoices, history):
    result = predict(AmountModel(), invoices, "2024-10-01", history)
    assert result["invoices"].doc_id.tolist() == ["second", "first"]
    assert result["week_bucket"].tolist() == [2, 1]
    assert result["invoices"].cust_number.tolist() == ["0002", "0001"]
    np.testing.assert_allclose(result["probabilities"].sum(axis=1), 1)


def test_forecast_conserves_normalized_amount(invoices, history):
    invoices["invoice_currency"] = ["CAD", "USD"]
    forecast = predict_cashflow(invoices, AmountModel(), "2024-10-01", history)
    assert len(forecast) == 7
    assert forecast.forecast_cash.sum() == pytest.approx(200 * 0.75 + 50)
    assert forecast.loc[forecast.week_bucket == 2, "forecast_cash"].item() == 150
    assert forecast.loc[forecast.week_bucket == 1, "forecast_cash"].item() == 50


def test_rank_retains_raw_probability(invoices, history):
    ranking = get_priority_invoices(invoices, AmountModel(), "2024-10-01", history)
    assert {"risk_score", "priority_score", "predicted_bucket", "name_customer", "due_in_date"} <= set(
        ranking
    )
    assert set(ranking.doc_id) == set(invoices.doc_id)


@pytest.mark.parametrize(
    "column,value",
    [
        ("total_open_amount", -1),
        ("total_open_amount", float("inf")),
        ("due_in_date", "bad date"),
        ("doc_id", None),
        ("invoice_sent", "2025-01-01"),
    ],
)
def test_invalid_inputs_rejected(invoices, history, column, value):
    invoices.loc[0, column] = value
    with pytest.raises(ValueError):
        predict(AmountModel(), invoices, "2024-10-01", history)


def test_duplicate_ids_rejected(invoices):
    invoices.loc[1, "doc_id"] = invoices.loc[0, "doc_id"]
    with pytest.raises(ValueError, match="unique"):
        normalize_invoices(invoices, inference=True)


def test_paid_invoices_rejected(invoices, history):
    invoices["invoice_paid"] = "2024-09-30"
    with pytest.raises(ValueError, match="paid invoices"):
        predict(AmountModel(), invoices, "2024-10-01", history)


def test_training_never_uses_future_payment_labels():
    df = pd.DataFrame(
        {
            "reference_date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-03-01"]),
            "invoice_paid": pd.to_datetime(["2024-01-15", "2024-03-20", "2024-03-20"]),
        }
    )
    train, test = temporal_split(df, "2024-02-01")
    assert train.index.tolist() == [0]
    assert test.index.tolist() == [2]
    assert (train.invoice_paid <= pd.Timestamp("2024-02-01")).all()


def test_demo_estimator_matches_documented_random_forest():
    from sklearn.ensemble import RandomForestClassifier
    from cf_copilot.demo import prepare_demo
    model, _, metadata = prepare_demo()
    assert isinstance(model.named_steps["classifier"], RandomForestClassifier)
    assert metadata["estimator"] == "RandomForestClassifier"
    assert metadata["temporal_split_fraction"] == 0.8
    assert "categorical" in model.named_steps["preprocessor"].named_transformers_
