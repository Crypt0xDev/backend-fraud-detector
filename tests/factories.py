import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUMERIC = ["step", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest"]


def make_transaction(**overrides):
    transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 1000.0,
        "nameOrig": "C123",
        "oldbalanceOrg": 1000.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C456",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
    }
    return transaction | overrides


def save_pipeline(path, extra_columns=()):
    rows = pd.DataFrame(
        [
            make_transaction(),
            make_transaction(type="PAYMENT", amount=10.0, newbalanceOrig=990.0),
            make_transaction(type="CASH_OUT", amount=5000.0, oldbalanceOrg=5000.0),
            make_transaction(type="CASH_IN", amount=50.0, newbalanceOrig=1050.0),
        ]
    )
    for column in extra_columns:
        rows[column] = 0.0
    rows = rows[["type", *NUMERIC, *extra_columns]]

    pipeline = Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [("type", OneHotEncoder(handle_unknown="ignore"), ["type"])],
                    remainder="passthrough",
                ),
            ),
            ("model", LogisticRegression()),
        ]
    )
    pipeline.fit(rows, [1, 0, 1, 0])
    joblib.dump(pipeline, path)
    return path
