---
title: Fraud Detector API
emoji: 🛡️
colorFrom: indigo
colorTo: gray
sdk: docker
app_port: 8000
pinned: false
---

# Backend Fraud Detector

API for the Fraud Detector project.

## Setup

- Requiere Python 3.14 y pip
- Requiere PostgreSQL: local o de Supabase
- Requiere PostgreSQL: local o de Supabase
- Los CSV de los lotes se guardan en STORAGE

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API en `http://localhost:8000/api/v1`, Swagger en `/docs`.

## Scripts

```bash
python -m app.user.create_user <usuario> [--role admin|user]
pytest
ruff check .
ruff format .
```

## Docker

```bash
docker build -t backend-fraud-detector .
docker run -p 8000:8000 -v ./ml/artifacts:/app/ml/artifacts:ro -v ./storage:/app/storage --env-file .env backend-fraud-detector
```

# Licencia

[MIT](LICENSE) - Universidad Nacional de San Martín - Tarapoto - Perú
