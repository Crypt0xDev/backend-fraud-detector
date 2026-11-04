"""Genera CSVs sintéticos con el formato de PaySim para probar la carga por lotes.

Uso:
    python scripts/generate_sample.py

Los datos son inventados (no salen de PaySim), pero siguen sus patrones:
el fraude solo ocurre en TRANSFER y CASH_OUT y suele vaciar la cuenta de origen.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"

# Proporción aproximada de tipos en PaySim
TYPES = ["CASH_OUT", "PAYMENT", "CASH_IN", "TRANSFER", "DEBIT"]
TYPE_WEIGHTS = [0.35, 0.34, 0.22, 0.08, 0.01]


def account(rng: np.random.Generator, prefix: str) -> str:
    return f"{prefix}{rng.integers(100_000_000, 999_999_999)}"


def normal_row(rng: np.random.Generator) -> dict:
    tx_type = rng.choice(TYPES, p=TYPE_WEIGHTS)
    amount = round(float(rng.lognormal(mean=10.5, sigma=1.3)), 2)
    old_orig = round(float(rng.lognormal(mean=10.0, sigma=2.0)), 2)

    if tx_type == "CASH_IN":
        new_orig = round(old_orig + amount, 2)
    else:
        new_orig = round(max(old_orig - amount, 0.0), 2)

    # PAYMENT va a comercios (M...), que en PaySim tienen saldos en 0
    if tx_type == "PAYMENT":
        name_dest = account(rng, "M")
        old_dest = new_dest = 0.0
    else:
        name_dest = account(rng, "C")
        old_dest = round(float(rng.lognormal(mean=11.0, sigma=2.0)), 2)
        delta = -amount if tx_type == "CASH_IN" else amount
        new_dest = round(max(old_dest + delta, 0.0), 2)

    return {
        "type": tx_type,
        "amount": amount,
        "nameOrig": account(rng, "C"),
        "oldbalanceOrg": old_orig,
        "newbalanceOrig": new_orig,
        "nameDest": name_dest,
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        "isFraud": 0,
    }


def fraud_row(rng: np.random.Generator) -> dict:
    # Vacía la cuenta: el monto es todo el saldo de origen
    balance = round(float(rng.lognormal(mean=12.5, sigma=1.5)), 2)
    # Muchos destinos fraudulentos en PaySim no reflejan el ingreso (saldos en 0)
    empty_dest = rng.random() < 0.6
    old_dest = 0.0 if empty_dest else round(float(rng.lognormal(mean=11.0, sigma=2.0)), 2)
    new_dest = 0.0 if empty_dest else round(old_dest + balance, 2)
    return {
        "type": rng.choice(["TRANSFER", "CASH_OUT"]),
        "amount": balance,
        "nameOrig": account(rng, "C"),
        "oldbalanceOrg": balance,
        "newbalanceOrig": 0.0,
        "nameDest": account(rng, "C"),
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        "isFraud": 1,
    }


def edge_rows() -> list[dict]:
    """Casos borde válidos para ver cómo reacciona el modelo"""
    base = {"nameOrig": "C100000001", "nameDest": "C200000001", "isFraud": 0}
    return [
        # Monto enorme
        {**base, "type": "TRANSFER", "amount": 92_445_516.64, "oldbalanceOrg": 92_445_516.64,
         "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0, "isFraud": 1},
        # Todo en cero
        {**base, "type": "CASH_OUT", "amount": 0.0, "oldbalanceOrg": 0.0,
         "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0},
        # Saldo de origen 0 pero monto alto (inconsistencia típica de PaySim)
        {**base, "type": "TRANSFER", "amount": 250_000.0, "oldbalanceOrg": 0.0,
         "newbalanceOrig": 0.0, "oldbalanceDest": 50_000.0, "newbalanceDest": 300_000.0},
        # Sin nombres de cuenta (son opcionales en el schema)
        {**base, "nameOrig": None, "nameDest": None, "type": "DEBIT", "amount": 1_200.5,
         "oldbalanceOrg": 5_000.0, "newbalanceOrig": 3_799.5, "oldbalanceDest": 0.0,
         "newbalanceDest": 1_200.5},
    ]


def build(n_rows: int, fraud_rate: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    edges = edge_rows()
    n_random = n_rows - len(edges)
    n_fraud = round(n_random * fraud_rate)

    rows = [fraud_row(rng) for _ in range(n_fraud)]
    rows += [normal_row(rng) for _ in range(n_random - n_fraud)]
    rows += edges

    frame = pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)
    # step = hora de la simulación (PaySim cubre 743 horas)
    frame.insert(0, "step", np.sort(rng.integers(1, 744, size=len(frame))))
    return frame


def invalid_frame() -> pd.DataFrame:
    """Filas que la API debe rechazar con 422"""
    ok = {"step": 1, "type": "PAYMENT", "amount": 100.0, "nameOrig": "C1", "oldbalanceOrg": 500.0,
          "newbalanceOrig": 400.0, "nameDest": "M1", "oldbalanceDest": 0.0, "newbalanceDest": 0.0}
    return pd.DataFrame([
        ok,
        {**ok, "amount": -50.0},           # monto negativo
        {**ok, "type": "REFUND"},          # tipo que no existe en PaySim
        {**ok, "oldbalanceOrg": None},     # saldo vacío
        {**ok, "step": -1},                # step negativo
        {**ok, "amount": "abc"},           # texto en vez de número
    ])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "transactions_1k.csv": build(1_000, 0.02, SEED),
        "transactions_10k.csv": build(10_000, 0.02, SEED + 1),
        "transactions_invalid.csv": invalid_frame(),
    }
    for name, frame in outputs.items():
        frame.to_csv(OUT_DIR / name, index=False)
        frauds = int(frame["isFraud"].sum()) if "isFraud" in frame else "-"
        print(f"{name}: {len(frame)} filas, fraudes={frauds}")


if __name__ == "__main__":
    main()
