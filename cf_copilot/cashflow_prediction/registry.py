import numpy as np
import pandas as pd
from cf_copilot.ml_logic.registry import predict

WEEK_CLASSES = list(range(1, 7))
CLASS_NAMES = list(range(1, 8))


def sharpen_probabilities(probas, temperature=1.0):
    """Identity by default: do not alter probabilities without fitted calibration."""
    if temperature != 1.0:
        raise ValueError(
            "Fit calibration on a separate temporal validation set before changing probabilities."
        )
    return np.asarray(probas)


def predict_cashflow(invoices_df, pipeline, reference_date=None, historical_data=None):
    results = predict(pipeline, invoices_df, reference_date, historical_data)
    table = _build_prediction_table(results["probabilities"], results["invoices"])
    return _aggregate_weekly_forecast(_add_expected_cash_columns(table))


def _build_prediction_table(probas, invoices_df):
    if len(probas) != len(invoices_df):
        raise ValueError("Invoice and prediction row counts differ.")
    return pd.concat(
        [
            invoices_df[["total_open_amount"]].reset_index(drop=True),
            pd.DataFrame(probas, columns=[f"p_{c}" for c in CLASS_NAMES]),
        ],
        axis=1,
    )


def _add_expected_cash_columns(pred_df):
    result = pred_df.copy()
    for week in CLASS_NAMES:
        result[f"expected_cash_{week}"] = result["total_open_amount"] * result[f"p_{week}"]
    return result


def _aggregate_weekly_forecast(pred_df):
    return pd.DataFrame(
        [
            {"week_bucket": w, "forecast_cash": round(float(pred_df[f"expected_cash_{w}"].sum()), 2)}
            for w in CLASS_NAMES
        ]
    )
