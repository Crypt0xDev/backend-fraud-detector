<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:4F46E5,100:0EA5E9&height=200&section=header&text=Fraud%20Detector%20API&fontSize=48&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Detecci%C3%B3n%20de%20fraude%20con%20Machine%20Learning&descAlignY=58&descSize=18" alt="Fraud Detector API" width="100%"/>

<a href="https://huggingface.co/spaces/Crypt0xDev/backend-fraud-detector">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=3000&pause=800&color=4F46E5&center=true&vCenter=true&width=600&lines=%F0%9F%9B%A1%EF%B8%8F+Detecta+transacciones+sospechosas;%E2%9A%A1+Predicciones+en+tiempo+real;%F0%9F%93%84+Analiza+CSV+de+hasta+10.000+filas;%F0%9F%A7%A0+Explica+cada+decisi%C3%B3n+del+modelo" alt="Typing SVG"/>
</a>

<br/>

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.4-EB5E28?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-listo-2496ED?style=for-the-badge&logo=docker&logoColor=white)](#-docker)
[![License: MIT](https://img.shields.io/badge/Licencia-MIT-F59E0B?style=for-the-badge)](#-licencia)

<a href="https://huggingface.co/spaces/Crypt0xDev/backend-fraud-detector"><img src="https://img.shields.io/badge/🤗_Demo-Hugging_Face-FFD21E?style=flat-square" alt="Demo"/></a>
<a href="https://github.com/Crypt0xDev/ml-fraud-training"><img src="https://img.shields.io/badge/🧠_Entrenamiento-del_modelo-8B5CF6?style=flat-square" alt="Entrenamiento"/></a>
<a href="https://github.com/Crypt0xDev/frontend-fraud-detector"><img src="https://img.shields.io/badge/💻_Frontend-Next.js-000000?style=flat-square" alt="Frontend"/></a>

</div>

---

## 📖 Sobre el proyecto

Analiza transacciones financieras y detecta posibles fraudes con un modelo **XGBoost** entrenado con el dataset [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1/data) (**6,3 millones** de transacciones).

<table>
  <tr>
    <td align="center" width="25%">🔍<br/><b>Predicción</b><br/><sub>Probabilidad y nivel de riesgo, con las variables que influyeron</sub></td>
    <td align="center" width="25%">📄<br/><b>Lotes CSV</b><br/><sub>Hasta 10.000 filas, con descarga de resultados</sub></td>
    <td align="center" width="25%">🗂️<br/><b>Historial</b><br/><sub>Lotes y predicciones por usuario</sub></td>
    <td align="center" width="25%">🔐<br/><b>Seguridad</b><br/><sub>Roles y permisos, JWT y contraseñas con scrypt</sub></td>
  </tr>
</table>

```mermaid
flowchart LR
    F[💻 Frontend<br/>Next.js] -->|HTTP + JWT| A[⚡ FastAPI<br/>/api/v1]
    A --> M[🧠 Modelo XGBoost<br/>ml/artifacts]
    A --> D[(🐘 PostgreSQL<br/>Supabase)]
    A --> S[(📦 CSV<br/>Supabase Storage o disco)]
```

## 🧰 Tecnologías

<div align="center">

<img src="https://skillicons.dev/icons?i=python,fastapi,sklearn,postgres,supabase,docker,githubactions&theme=dark" alt="Tecnologías"/>

</div>

## 🚀 Inicio rápido

> Necesitas [Python 3.14](https://www.python.org/downloads/), [Git LFS](https://git-lfs.com/) y una base PostgreSQL (local o Supabase).

```cmd
git lfs install
git clone https://github.com/Crypt0xDev/backend-fraud-detector.git
cd backend-fraud-detector
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --reload-include "*.joblib" --reload-include "*.json"
```

Completa `DATABASE_URL` y `JWT_SECRET` en `.env` antes de arrancar. En macOS / Linux activa con `source .venv/bin/activate` y copia con `cp`.

<div align="center">

📚 **Documentación de la API:** http://localhost:8000/docs

</div>

## ⚙️ Variables de entorno

Todas están en [`.env.example`](.env.example). Las principales:

| Variable | Para qué sirve |
| --- | --- |
| `DATABASE_URL` | Sin ella no hay login ni historial. En Supabase: Connect → Transaction pooler |
| `JWT_SECRET` | Secreto usado para firmar los tokens JWT. |
| `SUPABASE_URL` · `SUPABASE_SECRET_KEY` | Project Settings → API Keys |
| `MAX_PREDICT_ROWS` | Límite de transacciones por petición (100 por defecto); los CSV usan su propio límite. |
| `ADMIN_USERNAME` · `ADMIN_PASSWORD` | Admin inicial, solo si no hay ningún root; los demás usuarios se crean desde la API. |
| `TRUSTED_PROXIES` | IPs del frontend (por defecto `127.0.0.1,::1`). Solo a ellas se les cree `X-Forwarded-For` para limitar los intentos de login por IP real; en Docker, pon la IP del contenedor del frontend. |
| `DOCS_ENABLED` | `true` por defecto. Con `false` se apagan `/docs`, `/redoc` y `/openapi.json`; conviene en producción. |

> [!IMPORTANT]
> Nunca subas tu `.env` al repositorio: tiene contraseñas y claves.

## 📁 Estructura

```text
 ┣ 📜 main.py          # Punto de entrada
 ┣ 📂 app/             # Un módulo por carpeta: auth, user, role, prediction, batch, model...
 ┣ 📂 config/          # Variables de entorno, base de datos, rutas y datos iniciales
 ┣ 📂 utils/           # Tokens, contraseñas, límites y carga del modelo
 ┣ 📂 ml/artifacts/    # Modelo entrenado
 ┗ 📂 tests/           # Pruebas con pytest
```

## 🛠️ Comandos

```bash
pytest                                    # pruebas (SQLite temporal, no toca tu base)
pyright main.py app config utils          # revisión de tipos
python -m app.user.create_user <usuario>  # crear usuario o cambiar su contraseña
```


## 🐳 Docker

```bash
docker build -t backend-fraud-detector .
docker run -p 8000:8000 --env-file .env backend-fraud-detector
```

## 📄 Licencia

[MIT](LICENSE) · Universidad Nacional de San Martín · Tarapoto · Perú

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0EA5E9,100:4F46E5&height=120&section=footer" alt="footer" width="100%"/>
