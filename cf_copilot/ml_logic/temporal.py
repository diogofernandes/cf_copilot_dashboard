"""Split snapshots by reference date and observable payment labels."""

import pandas as pd


def temporal_split(df, cutoff, horizon_weeks=None):
    cutoff = pd.Timestamp(cutoff)
    train = df[
        (df["reference_date"] <= cutoff) & (df["invoice_paid"].notna()) & (df["invoice_paid"] <= cutoff)
    ].copy()
    test = df[df["reference_date"] > cutoff].copy()
    if horizon_weeks is not None:
        test = test[test["reference_date"] <= cutoff + pd.Timedelta(weeks=horizon_weeks)]
    if train.empty or test.empty:
        raise ValueError("Temporal split needs non-empty training and holdout data.")
    return train, test
