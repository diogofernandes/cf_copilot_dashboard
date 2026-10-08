"""Canonical invoice input and public payment buckets."""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("doc_id", "cust_number", "total_open_amount", "invoice_sent", "due_in_date")


def parse_date(values):
    text = values.astype("string").str.replace(r"\.0$", "", regex=True)
    compact = text.str.fullmatch(r"\d{8}", na=False)
    result = pd.to_datetime(text.where(~compact), errors="coerce", format="mixed")
    result.loc[compact] = pd.to_datetime(text.loc[compact], format="%Y%m%d", errors="coerce")
    return result


def normalize_invoices(df, inference=False):
    df = df.copy()
    df.columns = df.columns.str.strip()
    if df.columns.duplicated().any():
        raise ValueError("Duplicate column names are not supported.")
    df = df.rename(
        columns={
            "baseline_create_date": "invoice_sent",
            "clear_date": "invoice_paid",
            "buisness_year": "business_year",
            "document type": "document_type",
        }
    )
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    if df.empty:
        raise ValueError("Upload at least one invoice.")
    if len(df) > 10000 and inference:
        raise ValueError("Maximum upload is 10,000 invoices.")
    for col in ("doc_id", "cust_number"):
        if df[col].isna().any():
            raise ValueError(f"{col} cannot be empty.")
        df[col] = df[col].astype("string").str.replace(r"\.0$", "", regex=True)
    if df["doc_id"].duplicated().any():
        if inference:
            raise ValueError("doc_id must be unique within an upload.")
        df = df.drop_duplicates("doc_id", keep="last")
    df["total_open_amount"] = pd.to_numeric(df["total_open_amount"], errors="coerce")
    if (~np.isfinite(df["total_open_amount"]) | (df["total_open_amount"] < 0)).any():
        raise ValueError("Amounts must be finite and non-negative.")
    for col in ("invoice_sent", "due_in_date"):
        df[col] = parse_date(df[col])
        if df[col].isna().any():
            raise ValueError(f"{col} contains invalid dates.")
    if (df["due_in_date"] < df["invoice_sent"]).any():
        raise ValueError("Due dates cannot precede invoice dates.")
    if "invoice_paid" not in df:
        df["invoice_paid"] = pd.NaT
    else:
        original = df["invoice_paid"]
        df["invoice_paid"] = parse_date(original)
        supplied = original.notna() & original.astype(str).str.strip().ne("")
        if (supplied & df["invoice_paid"].isna()).any():
            raise ValueError("invoice_paid contains invalid dates.")
    if (df["invoice_paid"].notna() & (df["invoice_paid"] < df["invoice_sent"])).any():
        raise ValueError("Payment dates cannot precede invoice dates.")
    currency = df.get("invoice_currency", pd.Series("USD", index=df.index)).fillna("USD").str.upper()
    if not currency.isin(["USD", "CAD"]).all():
        raise ValueError("Supported currencies are USD and CAD.")
    year = df["invoice_sent"].dt.year
    rates = year.map({2018: 0.771, 2019: 0.754, 2020: 0.745}).fillna(0.75)
    df["total_open_amount"] = df["total_open_amount"] * np.where(currency.eq("CAD"), rates, 1)
    df["invoice_currency"] = "USD"
    df["name_customer"] = df.get("name_customer", df["cust_number"]).fillna(df["cust_number"]).astype(str)
    return df.reset_index(drop=True)


def payment_bucket(days):
    """Internal classes 0–6: days 1–7, 8–14, …, 36–42, and 43+."""
    return np.clip((np.asarray(days, dtype=int) - 1) // 7, 0, 6)


def public_probabilities(model, probabilities):
    result = np.zeros((len(probabilities), 7))
    classes = np.asarray(model.classes_, dtype=int)
    if not set(classes).issubset(set(range(7))):
        raise ValueError("Unsupported model classes. Retrain using the current schema.")
    result[:, classes] = probabilities
    result /= result.sum(axis=1, keepdims=True)
    return result
