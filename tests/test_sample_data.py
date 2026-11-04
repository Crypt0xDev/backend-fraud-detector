"""Comprueba que los CSV de data/sample sigan sirviendo para probar la API"""

from pathlib import Path

import pandas as pd
import pytest
from test_predictions import upload

from app.prediction.prediction_schema import Transaction
from app.prediction.usecases.use_prediction_csv import transactions_adapter
from config.settings import settings

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
VALID_FILES = ["transactions_1k.csv", "transactions_10k.csv"]


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DIR / name)


@pytest.mark.parametrize("name", VALID_FILES)
def test_muestras_tienen_columnas_de_paysim(name):
    frame = read(name)
    assert set(Transaction.model_fields) <= set(frame.columns)
    assert "isFraud" in frame.columns
    assert len(frame) <= settings.max_batch_rows


@pytest.mark.parametrize("name", VALID_FILES)
def test_muestras_pasan_el_schema(name):
    frame = read(name)
    rows = frame.astype(object).where(frame.notna(), None).to_dict("records")
    assert len(transactions_adapter.validate_python(rows)) == len(frame)


@pytest.mark.parametrize("name", VALID_FILES)
def test_fraude_sigue_el_patron_de_paysim(name):
    fraud = read(name).query("isFraud == 1")
    assert 0.01 <= len(fraud) / len(read(name)) <= 0.05
    assert set(fraud["type"]) <= {"TRANSFER", "CASH_OUT"}
    assert (fraud["newbalanceOrig"] == 0).all()


def test_muestra_1k_se_procesa_por_lote(client, analyst):
    content = (SAMPLE_DIR / "transactions_1k.csv").read_bytes()
    response = upload(client, analyst, content, "transactions_1k.csv")
    assert response.status_code == 200
    assert len(response.json()["predictions"]) == 1_000


def test_muestra_invalida_devuelve_422(client, analyst):
    content = (SAMPLE_DIR / "transactions_invalid.csv").read_bytes()
    response = upload(client, analyst, content, "transactions_invalid.csv")
    assert response.status_code == 422
    # 5 filas rotas a propósito; puede haber más de un error por fila
    failed_rows = {error["loc"][0] for error in response.json()["detail"]}
    assert failed_rows == {1, 2, 3, 4, 5}
