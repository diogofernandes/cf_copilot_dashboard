"""Local model registry; cloud and experiment tracking are optional extras."""

import json
import time
from functools import wraps
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from cf_copilot.params import (
    LOCAL_REGISTRY_PATH,
    MODEL_TARGET,
    CURRENT_DATE,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT,
    MLFLOW_MODEL_NAME,
    GCS_BUCKET_NAME,
    GCS_MODEL_PREFIX,
)
from cf_copilot.ml_logic.data import data_cleaning, engineer_features, load_historical_data
from cf_copilot.ml_logic.encoders import preprocess
from cf_copilot.ml_logic.schema import public_probabilities
from cf_copilot.ml_logic.reporting import make_json_serializable


def save_model(model):
    path = Path(LOCAL_REGISTRY_PATH) / "models" / (time.strftime("%Y%m%d-%H%M%S") + ".joblib")
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path, compress=3)
    if MODEL_TARGET == "gcs":
        from google.cloud import storage

        storage.Client().bucket(GCS_BUCKET_NAME).blob(GCS_MODEL_PREFIX + path.name).upload_from_filename(
            str(path)
        )
    elif MODEL_TARGET == "mlflow":
        import mlflow.sklearn

        mlflow.sklearn.log_model(model, name="model", registered_model_name=MLFLOW_MODEL_NAME)
    return path


def load_model(stage="Production"):
    if MODEL_TARGET == "mlflow":
        import mlflow.sklearn

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        try:
            return mlflow.sklearn.load_model(f"models:/{MLFLOW_MODEL_NAME}/{stage}")
        except Exception:
            pass
    elif MODEL_TARGET == "gcs":
        from google.cloud import storage

        bucket = storage.Client().bucket(GCS_BUCKET_NAME)
        blobs = [b for b in bucket.list_blobs(prefix=GCS_MODEL_PREFIX) if b.name.endswith(".joblib")]
        if not blobs:
            return None
        path = Path(LOCAL_REGISTRY_PATH) / "models" / "download.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        max(blobs, key=lambda b: b.updated).download_to_filename(str(path))
        return joblib.load(path)
    files = sorted((Path(LOCAL_REGISTRY_PATH) / "models").glob("*.joblib"))
    return joblib.load(files[-1]) if files else None


def save_results(metrics, figures=None, artifacts=None, json_artifacts=None):
    directory = Path(LOCAL_REGISTRY_PATH) / "metrics" / time.strftime("%Y%m%d-%H%M%S")
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {"metrics.json": metrics, **(json_artifacts or {})}
    for name, value in payloads.items():
        (directory / name).write_text(json.dumps(make_json_serializable(value), indent=2))
    for name, figure in (figures or {}).items():
        figure.savefig(directory / f"{name}.png", bbox_inches="tight")
    for name, value in (artifacts or {}).items():
        (directory / name).write_text(value)
    if MODEL_TARGET == "mlflow":
        import mlflow

        mlflow.log_metrics(metrics)
        mlflow.log_artifacts(str(directory))
    return directory


def mlflow_run(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if MODEL_TARGET != "mlflow":
            return func(*args, **kwargs)
        import mlflow

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT)
        with mlflow.start_run():
            return func(*args, **kwargs)

    return wrapper


def mlflow_transition_model(current_stage, new_stage):
    if MODEL_TARGET == "mlflow":
        from mlflow.tracking import MlflowClient

        client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
        versions = client.get_latest_versions(MLFLOW_MODEL_NAME, stages=[current_stage])
        if versions:
            client.transition_model_version_stage(MLFLOW_MODEL_NAME, versions[0].version, new_stage)


def prepare_features(df, reference_date=None, historical_data=None):
    date = pd.Timestamp(reference_date if reference_date is not None else CURRENT_DATE).normalize()
    cleaned = data_cleaning(df, predict=True)
    if (cleaned["invoice_sent"] > date).any():
        raise ValueError("Invoices cannot be issued after the forecast reference date.")
    if (cleaned["invoice_paid"].notna() & (cleaned["invoice_paid"] <= date)).any():
        raise ValueError("Upload outstanding invoices only; this batch contains paid invoices.")
    history = load_historical_data() if historical_data is None else historical_data
    featured = engineer_features(cleaned.copy(), history, date)
    X, _ = preprocess(featured, inference=True)
    return X, featured


def predict(model, df, reference_date=None, historical_data=None):
    X, invoices = prepare_features(df, reference_date, historical_data)
    probabilities = public_probabilities(model, model.predict_proba(X))
    return {
        "week_bucket": np.argmax(probabilities, axis=1) + 1,
        "probabilities": probabilities,
        "invoices": invoices,
    }
