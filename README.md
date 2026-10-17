# Backend Fraud Detector

API for the Fraud Detector project.

## Setup

- Requiere Python 3.14 y [uv](https://docs.astral.sh/uv/)
- Requiere `pipeline.joblib` y `metrics.json` en `ml/artifacts/`
- Requiere una base de datos de Supabase (ver `.env.example`)

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API en `http://localhost:8000/api/v1`, Swagger en `/docs`.

## Scripts

```bash
python -m app.user.create_user <usuario>
pytest
ruff check .
ruff format .
```

## Docker

```bash
docker build -t backend-fraud-detector .
docker run -p 8000:8000 -v ./ml/artifacts:/app/ml/artifacts:ro --env-file .env backend-fraud-detector
```
