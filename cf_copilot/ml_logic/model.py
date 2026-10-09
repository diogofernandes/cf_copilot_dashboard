"""Random Forest pipeline aligned with the original project's README."""
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestClassifier

NUMERIC_FEATURES = [
    "invoice_age_days", "days_until_due", "pay_terms_days", "customer_avg_delay",
    "days_since_last_invoice", "invoice_amount_log", "invoice_month_sin",
    "invoice_month", "due_month", "late_payment_ratio", "prev_transaction_count",
    "customer_risk_score", "open_amount",
]
CATEGORICAL_FEATURES = ["invoice_size_cat"]

def initialize_model() -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(categories=[["small", "medium", "large"]],
                                   handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric, NUMERIC_FEATURES),
        ("categorical", categorical, CATEGORICAL_FEATURES),
    ], remainder="drop")
    classifier = RandomForestClassifier(
        n_estimators=160, max_depth=12, min_samples_leaf=2,
        random_state=42, n_jobs=4,
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])

def train_model(model: Pipeline, X: np.ndarray, y: np.ndarray) -> Pipeline:
    model.fit(X, y)
    return model
