import pandas as pd

from app.prediction.prediction_schema import Transaction

DERIVED_COLUMNS = ("errorBalanceOrig", "errorBalanceDest", "hour")
AVAILABLE_COLUMNS = (*Transaction.model_fields, *DERIVED_COLUMNS)
DEFAULT_COLUMNS = [c for c in AVAILABLE_COLUMNS if c not in ("nameOrig", "nameDest")]


def build_features(transactions: list[Transaction]) -> pd.DataFrame:
    frame = pd.DataFrame([transaction.model_dump() for transaction in transactions])
    return frame.assign(
        errorBalanceOrig=frame.newbalanceOrig + frame.amount - frame.oldbalanceOrg,
        errorBalanceDest=frame.oldbalanceDest + frame.amount - frame.newbalanceDest,
        hour=frame.step % 24,
    )
