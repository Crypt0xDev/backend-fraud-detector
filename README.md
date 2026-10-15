# Backend Fraud Detector

API de detección de fraude entrenada con [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1). FastAPI + scikit-learn/XGBoost.

## Setup

- Requiere Python 3.14 y [uv](https://docs.astral.sh/uv/).
- El modelo se entrena en otro repo: copia `pipeline.joblib` y `metrics.json` a `ml/artifacts/` (están fuera de git). Sin ellos la API arranca, pero `/predict` y `/metrics` responden 503.
- Usa las mismas versiones de scikit-learn y XGBoost que el repo de entrenamiento; si no, el pipeline puede no cargar o predecir distinto.

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv -r requirements.txt
cp .env.example .env
```

Activa el entorno antes de los comandos siguientes: `.venv\Scripts\activate` en Windows o `source .venv/bin/activate` en Linux/macOS.

## Configuración

Variables en `.env` (ver `.env.example`):

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes permitidos, separados por comas |
| `MODEL_PATH` | `ml/artifacts/pipeline.joblib` | Pipeline entrenado |
| `METRICS_PATH` | `ml/artifacts/metrics.json` | Métricas del entrenamiento |
| `MODEL_SHA256` | vacío | Hash esperado del pipeline; si no coincide, no se carga |
| `MAX_BATCH_ROWS` | `10000` | Máximo de transacciones por petición |
| `FRAUD_THRESHOLD` | `0.5` | Probabilidad a partir de la cual se marca fraude |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` o `ERROR` |

`joblib` ejecuta código al cargar, así que en producción conviene fijar `MODEL_SHA256`:

```bash
python -c "import hashlib; print(hashlib.sha256(open('ml/artifacts/pipeline.joblib', 'rb').read()).hexdigest())"
```

Al arrancar, el modelo se descarta (y queda en el log) si el archivo está corrupto, no tiene `predict_proba`, el hash no coincide o espera columnas que la API no recibe.

## Uso

```bash
uvicorn main:app --reload
```

API en `http://localhost:8000/api/v1`, Swagger en `/docs`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Estado de la API y si el modelo y las métricas están cargados |
| `GET` | `/metrics` | Contenido de `metrics.json` |
| `POST` | `/predict` | Predice un lote de transacciones en JSON |
| `POST` | `/predict/csv` | Predice un CSV con columnas de PaySim (campo `file`) |

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"transactions": [{"step": 1, "type": "TRANSFER", "amount": 1000.0,
       "oldbalanceOrg": 1000.0, "newbalanceOrig": 0.0,
       "oldbalanceDest": 0.0, "newbalanceDest": 0.0}]}'
```

```json
{"threshold": 0.5, "predictions": [{"fraud_probability": 0.83, "is_fraud": true}]}
```

`type` admite `CASH_IN`, `CASH_OUT`, `DEBIT`, `PAYMENT` y `TRANSFER`; `nameOrig` y `nameDest` son opcionales. El CSV puede ser el de PaySim tal cual: las columnas extra como `isFraud` se ignoran.

## Desarrollo

```bash
pytest
ruff check .
ruff format .
```

GitHub Actions ejecuta ruff, pytest y el build de Docker en cada push a `main` y en cada PR.

## Docker

La imagen no incluye el modelo si `ml/artifacts/` está vacío al construirla; lo habitual es montarlo como volumen:

```bash
docker build -t backend-fraud-detector .
docker run -p 8000:8000 -v ./ml/artifacts:/app/ml/artifacts:ro --env-file .env backend-fraud-detector
```

El contenedor corre sin root y tiene un `HEALTHCHECK` sobre `/health`.
