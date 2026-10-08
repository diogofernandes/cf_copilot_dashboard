"""Synthetic demonstration; no downloads, credentials or private data."""

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, log_loss
from cf_copilot.params import BASE_DIR
from cf_copilot.ml_logic.data import build_sliding_window_snapshots
from cf_copilot.ml_logic.encoders import preprocess
from cf_copilot.ml_logic.model import initialize_model
from cf_copilot.ml_logic.schema import public_probabilities

DEMO_DATE = pd.Timestamp("2024-10-01")
DEMO_DIR = BASE_DIR / "raw_data" / "demo"
SCHEMA_VERSION = 2


def synthetic_history(size=1600):
    rng = np.random.default_rng(42)
    customer = rng.integers(0, 32, size)
    sent = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 610, size), unit="D")
    terms = rng.choice([7, 14, 30, 45], size)
    delay = np.maximum(0, customer % 8 * 4 + rng.normal(0, 8, size)).astype(int)
    return (
        pd.DataFrame(
            {
                "doc_id": [f"H{i:05}" for i in range(size)],
                "cust_number": [f"C{c:03}" for c in customer],
                "name_customer": [f"Example Customer {c:02}" for c in customer],
                "total_open_amount": np.round(rng.lognormal(8.5, 1.0, size), 2),
                "invoice_sent": sent,
                "due_in_date": sent + pd.to_timedelta(terms, unit="D"),
                "invoice_paid": sent + pd.to_timedelta(terms + delay + 1, unit="D"),
                "invoice_currency": "USD",
            }
        )
        .sort_values("invoice_sent")
        .reset_index(drop=True)
    )


def synthetic_upload():
    rng = np.random.default_rng(7)
    customer = rng.integers(0, 32, 24)
    sent = DEMO_DATE - pd.to_timedelta(rng.integers(5, 70, 24), unit="D")
    return pd.DataFrame(
        {
            "doc_id": [f"INV-{i + 1:04}" for i in range(24)],
            "cust_number": [f"C{c:03}" for c in customer],
            "name_customer": [f"Example Customer {c:02}" for c in customer],
            "total_open_amount": np.round(rng.lognormal(9, 1.0, 24), 2),
            "invoice_sent": sent,
            "due_in_date": sent + pd.to_timedelta(rng.choice([14, 30, 45], 24), unit="D"),
            "invoice_currency": "USD",
        }
    )


def prepare_demo(force=False):
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    model_path = DEMO_DIR / "model.joblib"
    metadata_path = DEMO_DIR / "metadata.json"
    if model_path.exists() and metadata_path.exists() and not force:
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("schema_version") == SCHEMA_VERSION:
            return (
                joblib.load(model_path),
                pd.read_csv(
                    DEMO_DIR / "history.csv", parse_dates=["invoice_sent", "due_in_date", "invoice_paid"]
                ),
                metadata,
            )
    history = synthetic_history()
    snapshots = build_sliding_window_snapshots(history)
    cutoff = snapshots["reference_date"].quantile(0.7)
    train = snapshots[(snapshots["reference_date"] <= cutoff) & (snapshots["invoice_paid"] <= cutoff)]
    test = snapshots[snapshots["reference_date"] > cutoff]
    X_train, y_train = preprocess(train)
    X_test, y_test = preprocess(test)
    if set(y_train.unique()) != set(range(7)):
        raise ValueError("Training needs all seven buckets.")
    model = initialize_model()
    model.set_params(classifier__n_estimators=80, classifier__max_depth=5)
    model.fit(X_train, y_train)
    baseline = DummyClassifier(strategy="prior").fit(X_train, y_train)
    metrics = {
        "model_accuracy": float(accuracy_score(y_test, model.predict(X_test))),
        "baseline_accuracy": float(accuracy_score(y_test, baseline.predict(X_test))),
        "model_log_loss": float(
            log_loss(y_test, public_probabilities(model, model.predict_proba(X_test)), labels=range(7))
        ),
        "baseline_log_loss": float(log_loss(y_test, baseline.predict_proba(X_test), labels=range(7))),
    }
    from cf_copilot.cashflow_prediction.evaluation import evaluate_forecast_holdout

    cf_metrics, _ = evaluate_forecast_holdout(model, test, verbose=False)
    metrics.update(cf_metrics)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "dataset": "synthetic, seed 42",
        "reference_date": str(DEMO_DATE.date()),
        "training_cutoff": str(cutoff.date()),
        "training_rows": len(train),
        "holdout_rows": len(test),
        "known_labels_only": True,
        "metrics": metrics,
        "limitation": "Synthetic demonstration; these metrics do not establish real-world performance.",
    }
    joblib.dump(model, model_path)
    history.to_csv(DEMO_DIR / "history.csv", index=False)
    synthetic_upload().to_csv(DEMO_DIR / "invoices.csv", index=False)
    metadata_path.write_text(json.dumps(metadata, indent=2))
    reports = BASE_DIR / "docs" / "demo_metrics.json"
    reports.parent.mkdir(parents=True, exist_ok=True)
    reports.write_text(json.dumps(metadata, indent=2))
    return model, history, metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    _, _, metadata = prepare_demo(parser.parse_args().force)
    print(json.dumps(metadata, indent=2))
