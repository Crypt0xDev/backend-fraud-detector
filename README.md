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
| `MAX_UPLOAD_MB` | `20` | Tamaño máximo del CSV |
| `DATABASE_URL` | vacío | PostgreSQL de Supabase. Sin ella, login y endpoints protegidos responden 503 |
| `SUPABASE_URL` | vacío | URL del proyecto (`https://<ref>.supabase.co`) |
| `SUPABASE_SECRET_KEY` | vacío | Secret key (`sb_secret_…`) o `service_role`. Solo en el backend |
| `SUPABASE_BUCKET` | `batches` | Bucket privado de los lotes; se crea al arrancar si no existe |
| `JWT_SECRET` | aleatoria | Clave de firma de los tokens (mín. 32 caracteres). Sin ella, las sesiones se pierden al reiniciar |
| `JWT_EXPIRE_MINUTES` | `480` | Duración de la sesión |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | vacío | Usuario inicial; se crea al arrancar si no existe y nunca se sobrescribe |
| `FRAUD_THRESHOLD` | `0.5` | Probabilidad a partir de la cual se marca fraude |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` o `ERROR` |

`joblib` ejecuta código al cargar, así que en producción conviene fijar `MODEL_SHA256`:

```bash
python -c "import hashlib; print(hashlib.sha256(open('ml/artifacts/pipeline.joblib', 'rb').read()).hexdigest())"
```

Al arrancar, el modelo se descarta (y queda en el log) si el archivo está corrupto, no tiene `predict_proba`, el hash no coincide o espera columnas que la API no tiene.

## Contrato del modelo

El pipeline recibe un DataFrame con las columnas que declare en `feature_names_in_`, elegidas entre las de PaySim (`step`, `type`, `amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`) y las que calcula la API:

- `errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg`
- `errorBalanceDest = oldbalanceDest + amount - newbalanceDest`
- `hour = step % 24`

`metrics.json` es un objeto con claves opcionales: `model_name`, `trained_at`, `threshold`, `roc_auc`, `pr_auc`, `precision`, `recall`, `f1`, `accuracy` y `confusion_matrix` (`[[tn, fp], [fn, tp]]`). Las claves extra se devuelven tal cual. Si no cumple el formato, `/metrics` responde 503.

## Supabase

- `DATABASE_URL`: *Connect* → *Transaction pooler* (puerto `6543`), con `?sslmode=require`.
- `SUPABASE_URL` y `SUPABASE_SECRET_KEY`: *Project Settings* → *API Keys*.

Las tablas `users` y `batches` se crean al arrancar con RLS activado, para que la API pública de Supabase no pueda leerlas. Cada `POST /predict/csv` guarda el CSV original y el de predicciones en `<bucket>/<batch_id>/` y registra el lote; si Storage falla, la predicción se devuelve igual con `batch_id: null`.

## Usuarios

No hay registro público. El primer usuario puede venir de `ADMIN_USERNAME`/`ADMIN_PASSWORD`; el resto se crea (o se le cambia la contraseña) por comando:

```bash
python -m app.user.create_user ana
```

`/predict`, `/predict/csv`, `/metrics` y `/batches` requieren `Authorization: Bearer <token>`; el token se obtiene en `POST /auth/login` (formulario con `username` y `password`). En Swagger se usa el botón *Authorize*.

## Uso

```bash
uvicorn main:app --reload
```

API en `http://localhost:8000/api/v1`, Swagger en `/docs`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/auth/login` | Devuelve un JWT |
| `GET` | `/auth/me` | Usuario de la sesión |
| `GET` | `/health` | Estado de la API y si el modelo y las métricas están cargados |
| `GET` | `/metrics` | Contenido de `metrics.json` |
| `POST` | `/predict` | Predice un lote de transacciones en JSON |
| `POST` | `/predict/csv` | Predice un CSV con columnas de PaySim (campo `file`) y lo guarda en el historial |
| `GET` | `/batches` | Historial de lotes del usuario |
| `GET` | `/batches/{id}/files/{input\|predictions}` | URL firmada (5 min) para descargar un CSV |
| `DELETE` | `/batches/{id}` | Borra el lote y sus archivos |

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=ana&password=..." | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transactions": [{"step": 1, "type": "TRANSFER", "amount": 1000.0,
       "oldbalanceOrg": 1000.0, "newbalanceOrig": 0.0,
       "oldbalanceDest": 0.0, "newbalanceDest": 0.0}]}'
```

```json
{"threshold": 0.5, "predictions": [{"fraud_probability": 0.83, "is_fraud": true}]}
```

`type` admite `CASH_IN`, `CASH_OUT`, `DEBIT`, `PAYMENT` y `TRANSFER`; `nameOrig` y `nameDest` son opcionales. El CSV puede ser el de PaySim tal cual: las columnas extra como `isFraud` se ignoran.

## Estructura

- `main.py`: crea la app y ejecuta el arranque (base de datos, seeders, Storage, modelo).
- `config/`: `settings.py` (variables de entorno), `database.py` (pool de Postgres y tablas), `routes.py` (registro central de rutas) y `create_default_records.py` (ejecuta los seeders).
- `seeders/`: datos iniciales, como el usuario de `ADMIN_USERNAME`.
- `utils/`: autenticación (`auth.py`), contraseñas, JWT, cliente de Supabase Storage y carga del modelo.
- `app/<módulo>/`: `<módulo>_route.py` (HTTP), `<módulo>_schema.py`, `<módulo>_repository.py` (SQL) y `usecases/use_<módulo>_<acción>.py` (un caso de uso por archivo).
  - `auth/`: login y sesión. `user/`: tabla de usuarios y el comando `create_user`. `prediction/`: predicción y variables derivadas. `batch/`: historial de lotes. `model/`: `/health` y `/metrics`.

## Desarrollo

```bash
pytest
ruff check .
ruff format .
```

Los tests usan base de datos y Storage en memoria. Para probar también contra PostgreSQL, define `TEST_DATABASE_URL` (crea y borra usuarios `pytest-*`).

## Docker

La imagen no incluye el modelo si `ml/artifacts/` está vacío al construirla; lo habitual es montarlo como volumen:

```bash
docker build -t backend-fraud-detector .
docker run -p 8000:8000 -v ./ml/artifacts:/app/ml/artifacts:ro --env-file .env backend-fraud-detector
docker exec -it <contenedor> python -m app.user.create_user ana
```

El contenedor corre sin root y tiene un `HEALTHCHECK` sobre `/health`.
