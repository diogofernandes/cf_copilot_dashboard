from cf_copilot.ml_logic.model import NUMERIC_FEATURES, CATEGORICAL_FEATURES


def preprocess(df, inference=False):
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    X["customer_avg_delay"] = X["customer_avg_delay"].fillna(0)
    X["days_since_last_invoice"] = X["days_since_last_invoice"].fillna(-1)
    return X, None if inference else df["week_bucket"].astype(int)
