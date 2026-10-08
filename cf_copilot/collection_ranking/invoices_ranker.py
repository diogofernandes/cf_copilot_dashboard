"""Transparent collections heuristic combining amount, lateness and model probability."""

import numpy as np
from cf_copilot.ml_logic.registry import predict


def get_priority_invoices(invoices_df, pipeline, current_date, historical_data=None):
    result = predict(pipeline, invoices_df, current_date, historical_data)
    df = result["invoices"].copy()
    probabilities = result["probabilities"]
    df["risk_score"] = probabilities[:, 4:].sum(axis=1)
    df["predicted_bucket"] = result["week_bucket"]
    df["days_overdue"] = df["days_past_due"].clip(lower=0).astype(int)
    multiplier = np.select(
        [df["days_overdue"].eq(0), df["days_overdue"].lt(7), df["days_overdue"].lt(30)],
        [1.0, 1.2, 1.5],
        default=2.0,
    )
    df["priority_score"] = df["total_open_amount"] * df["risk_score"] * multiplier
    df["risk_category"] = np.select(
        [df["risk_score"] < 0.2, df["risk_score"] < 0.5], ["Low", "Medium"], default="High"
    )
    df["cust_late_ratio"] = df["late_payment_ratio"].fillna(0)
    df["cust_n_transactions"] = df["prev_transaction_count"]
    df = df.sort_values(["priority_score", "doc_id"], ascending=[False, True]).head(10).reset_index(drop=True)
    df["collections_rank"] = np.arange(1, len(df) + 1)
    cols = [
        "collections_rank",
        "doc_id",
        "cust_number",
        "name_customer",
        "total_open_amount",
        "due_in_date",
        "days_past_due",
        "days_overdue",
        "risk_category",
        "risk_score",
        "priority_score",
        "predicted_bucket",
        "cust_late_ratio",
        "cust_n_transactions",
    ]
    return df[cols]
