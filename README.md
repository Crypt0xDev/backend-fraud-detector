<div align="center">

# 🛡️ Backend Fraud Detector

**API REST que detecta transacciones financieras sospechosas con Machine Learning**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.4-EB5E28)](https://xgboost.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-listo-2496ED?logo=docker&logoColor=white)](#-docker)
[![License: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](#-licencia)

[![Demo en Hugging Face](https://img.shields.io/badge/🤗%20Demo-Hugging%20Face-FFD21E)](https://huggingface.co/spaces/Crypt0xDev/backend-fraud-detector)

[Demo](https://huggingface.co/spaces/Crypt0xDev/backend-fraud-detector) · [Entrenamiento del modelo](https://github.com/Crypt0xDev/ml-fraud-training) · [Frontend](https://github.com/Crypt0xDev/frontend-fraud-detector)

</div>

---

## 📖 Sobre el proyecto

Sistema inteligente en Python que analiza transacciones financieras y detecta posibles fraudes con un modelo **XGBoost** entrenado con el dataset [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1/data) (6,3 millones de transacciones).

Permite analizar transacciones sueltas o un CSV completo, explica por qué el modelo marcó una alerta, guarda el historial y controla el acceso con usuarios, roles y permisos.

> 🚀 La versión desplegada está en **[Hugging Face](https://huggingface.co/spaces/Crypt0xDev/backend-fraud-detector)**. Este repositorio tiene el código fuente.

## 📑 Contenido

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Tecnologías](#-tecnologías)
- [Inicio rápido](#-inicio-rápido)
- [Variables de entorno](#-variables-de-entorno)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Roles y permisos](#-roles-y-permisos)
- [Scripts](#-scripts)
- [Docker](#-docker)
- [Proyectos relacionados](#-proyectos-relacionados)
- [Licencia](#-licencia)

## ✨ Características

| | |
|---|---|
| 🔍 **Detección de fraude** | Probabilidad de fraude y nivel de riesgo (bajo, medio, alto) por transacción |
| 💡 **Explicación** | Qué variables subieron o bajaron el score de cada predicción |
| 📄 **Análisis de CSV** | Sube un CSV de PaySim de hasta 10.000 filas y descarga los resultados |
| 🗂️ **Historial** | Lotes y predicciones guardados por usuario, con estadísticas por día |
| 🔐 **Roles y permisos** | Usuario root y roles con permisos por módulo |
| 📊 **Métricas del modelo** | Métricas, experimentos y perfil del dataset para el dashboard |
| 🛡️ **Seguridad** | JWT, contraseñas con scrypt, límite de peticiones y de intentos de login |

## 🏗️ Arquitectura

```mermaid
flowchart LR
    F[Frontend<br/>Next.js] -->|HTTP + JWT| A[FastAPI<br/>/api/v1]
    A --> M[Modelo XGBoost<br/>ml/artifacts]
    A --> D[(PostgreSQL<br/>Supabase)]
    A --> S[(Almacenamiento CSV<br/>Supabase Storage o disco)]
    T[ml-fraud-training] -.->|pipeline.joblib<br/>metrics.json| M
```

Cada módulo de `app/` tiene sus propias rutas, esquemas, entidades y casos de uso, así que se puede cambiar uno sin tocar los demás.

## 🧰 Tecnologías

| Área | Herramientas |
|---|---|
| API | FastAPI 0.143, Uvicorn, Pydantic 2 + pydantic-settings |
| Machine Learning | XGBoost 3.4, scikit-learn 1.9, pandas 3, NumPy |
| Base de datos | PostgreSQL (local o Supabase), SQLAlchemy 2.1, psycopg 3 |
| Seguridad | PyJWT (tokens), scrypt (contraseñas) |
| Herramientas | uv, ruff, Docker |

## 🚀 Inicio rápido

### Requisitos

- [uv](https://docs.astral.sh/uv/) (instala Python 3.14 automáticamente)
- PostgreSQL: local o Supabase. Sin `DATABASE_URL` no hay login ni historial
- Artefactos del modelo en `ml/artifacts/`. Sin `pipeline.joblib`, `/predict` responde 503

### 1. Instalar uv

<details>
<summary><b>macOS / Linux</b></summary>

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

Cierra y abre la terminal después de instalar.

### 2. Instalar y ejecutar

<details open>
<summary><b>macOS / Linux</b></summary>

```bash
git clone https://github.com/Crypt0xDev/backend-fraud-detector.git
cd backend-fraud-detector
uv venv --python 3.14 .venv
uv pip install --python .venv -r requirements-dev.txt
cp .env.example .env
uv run uvicorn main:app --reload
```

</details>

<details>
<summary><b>Windows (cmd)</b></summary>

```cmd
git clone https://github.com/Crypt0xDev/backend-fraud-detector.git
cd backend-fraud-detector
uv venv --python 3.14 .venv
uv pip install --python .venv -r requirements-dev.txt
copy .env.example .env
uv run uvicorn main:app --reload
```

</details>

> [!NOTE]
> Copia `.env.example` solo la primera vez; si lo repites sobrescribe tu `.env`.
>
> `requirements-dev.txt` instala la API más ruff y pytest. En el servidor solo hace falta `requirements.txt`.

### 3. Activar y desactivar el entorno virtual (opcional)

`uv run` ya usa `.venv` sin activarlo. Actívalo solo si quieres usar `python` o `uvicorn` directamente.

| Sistema | Activar | Desactivar |
|---|---|---|
| macOS / Linux | `source .venv/bin/activate` | `deactivate` |
| Windows (cmd) | `.venv\Scripts\activate.bat` | `deactivate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` | `deactivate` |

Con el entorno activado, la API se inicia con `uvicorn main:app --reload`.

> [!TIP]
> Si PowerShell bloquea el script, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 4. Abrir

| | URL |
|---|---|
| API | http://localhost:8000/api/v1 |
| Documentación (Swagger) | http://localhost:8000/docs |

## ⚙️ Variables de entorno

Todas están en [`.env.example`](.env.example).

- Generar el valor de `JWT_SECRET` (también sirve para `ADMIN_PASSWORD` y `USER_PASSWORD`):

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

- Calcular `MODEL_SHA256` (opcional; la API no carga el modelo si fue modificado):

```bash
uv run python -c "import hashlib; print(hashlib.sha256(open('ml/artifacts/pipeline.joblib','rb').read()).hexdigest())"
```

- Copiar de Supabase:
  - `DATABASE_URL`: Connect → Transaction pooler
  - `SUPABASE_URL` y `SUPABASE_SECRET_KEY`: Project Settings → API Keys

> [!IMPORTANT]
> Nunca subas tu `.env` al repositorio: tiene contraseñas y claves.

## 📁 Estructura del proyecto

```text
backend-fraud-detector/
├── main.py                  # Punto de entrada: base, modelo y rutas
├── requirements.txt         # Dependencias de la API
├── requirements-dev.txt     # Las de la API más ruff y pytest
├── app/                     # Un módulo por carpeta (rutas, esquemas, entidades, usecases/)
│   ├── auth/                # Login, sesión (/auth/me) y control de permisos
│   ├── user/                # Usuarios (solo el root los gestiona)
│   ├── role/                # Roles con sus permisos
│   ├── module/              # Secciones del menú (se usan desde role/)
│   ├── permission/          # Acciones: ver, crear, editar, eliminar
│   ├── prediction/          # Análisis de transacciones y CSV, e historial
│   ├── batch/               # Lotes, descargas y estadísticas
│   ├── model/               # Estado, métricas y experimentos del modelo
│   └── visualization/       # Perfil del dataset y muestra para gráficos
├── config/
│   ├── settings.py          # Variables de entorno
│   ├── database.py          # Conexión a PostgreSQL
│   ├── routes.py            # Registro central de rutas
│   ├── error_handlers.py    # Convierte los errores de los casos de uso en respuestas HTTP
│   ├── entities.py          # Importa todas las entidades
│   ├── create_default_records.py  # Ejecuta los seeders al iniciar
│   └── seeders/             # Datos iniciales
├── utils/                   # Tokens, contraseñas, errores, límites, archivos y carga del modelo
├── ml/artifacts/            # Archivos del modelo entrenado
├── tests/                   # Pruebas con pytest contra la API real
└── .vscode/                 # Configuración de VS Code del proyecto y extensiones recomendadas
```

## 🔐 Roles y permisos

- **root**: puede hacer todo. Es el único que gestiona usuarios y roles y ve los datos de todos.
- **Los demás usuarios** tienen los permisos de sus roles y solo ven sus propios lotes y predicciones. Un usuario puede tener varios roles; sus permisos se suman.

## 🛠️ Scripts

- Crear un usuario o cambiar su contraseña (por ejemplo, si se olvidó la del root). La pide en la terminal y cierra las sesiones abiertas de ese usuario:

```bash
uv run python -m app.user.create_user <usuario> [--role admin|user]
```

- Revisar y formatear el código:

```bash
uv run ruff check .
uv run ruff format .
```

- Correr las pruebas. Por defecto usan SQLite en un archivo temporal, sin tocar tu base:

```bash
uv run pytest
```

- Correr las pruebas contra PostgreSQL. Usa una base solo para pruebas: **se borran todas sus tablas**:

```bash
TEST_DATABASE_URL="postgresql://usuario:clave@localhost:5432/fraud_test" uv run pytest
```

GitHub Actions corre ruff y las pruebas en cada push a `main`, y solo si pasan se publica en Hugging Face.

## 🐳 Docker

```bash
docker build -t backend-fraud-detector .
```

<details open>
<summary><b>macOS / Linux / PowerShell</b></summary>

```bash
docker run -p 8000:8000 -v ${PWD}/ml/artifacts:/app/ml/artifacts:ro -v ${PWD}/storage:/app/storage --env-file .env backend-fraud-detector
```

</details>

<details>
<summary><b>Windows (cmd)</b></summary>

```cmd
docker run -p 8000:8000 -v %cd%/ml/artifacts:/app/ml/artifacts:ro -v %cd%/storage:/app/storage --env-file .env backend-fraud-detector
```

</details>

## 🔗 Proyectos relacionados

| Repositorio | Descripción |
|---|---|
| [ml-fraud-training](https://github.com/Crypt0xDev/ml-fraud-training) | Análisis de datos, entrenamiento y comparación de modelos |
| [frontend-fraud-detector](https://github.com/Crypt0xDev/frontend-fraud-detector) | Dashboard en Next.js, React, TypeScript y Tailwind CSS |

## 📄 Licencia

[MIT](LICENSE) - Universidad Nacional de San Martín - Tarapoto - Perú
