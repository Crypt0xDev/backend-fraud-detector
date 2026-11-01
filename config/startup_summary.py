import logging
import sys
from typing import Any
from urllib.parse import urlsplit

from config import database
from config.settings import API_PREFIX, Settings
from utils.storage import LocalStorage, SupabaseStorage

logger = logging.getLogger(__name__)

WIDTH = 60

def describe_database(database_url: str | None, engine: Any) -> str:
    if not database_url or engine is None:
        return "no configurada (login e historial no disponibles)"
    url = urlsplit(database_url)
    name = url.path.lstrip("/") or "postgres"
    where = "Supabase" if "supabase" in (url.hostname or "") else "PostgreSQL local"
    return f"{where} · {name} en {url.hostname}:{url.port or 5432}"

def describe_storage(storage: Any) -> str:
    if isinstance(storage, LocalStorage):
        return f"local · {storage.root}"
    if isinstance(storage, SupabaseStorage):
        return f"Supabase · bucket {storage.bucket}"
    return "desactivado (los lotes no se guardan)"

def describe_model(model: Any, metrics: Any, policy: Any) -> list[str]:
    if model is None:
        return ["no cargado (/predict responde 503)"]
    info = metrics.model_dump() if metrics is not None else {}
    name = " · ".join(
        str(part) for part in (info.get("version"), info.get("model_name")) if part
    )
    lines = [name or type(model).__name__]
    trained = info.get("threshold")
    if trained is not None and abs(trained - policy.high) > 1e-9:
        lines.append(f"umbral {policy.high} (el modelo se entrenó con {trained})")
    else:
        lines.append(f"umbral {policy.high}")
    if info.get("pr_auc") is not None:
        lines.append(f"PR-AUC {info['pr_auc']:.4f}")
    return [" · ".join(lines)]

def describe_sample(sample: Any) -> str:
    if sample is None:
        return "no disponible (falta ml/artifacts/sample.csv)"
    return f"muestra de {len(sample):,} transacciones".replace(",", ".")

def build_summary(state: Any, settings: Settings) -> str:
    api = f"{settings.api_public_url.rstrip('/')}{API_PREFIX}"
    rows = [
        ("Base de datos", describe_database(settings.database_url, database.engine)),
        ("Archivos", describe_storage(state.storage)),
        *(
            ("Modelo", line)
            for line in describe_model(state.model, state.metrics, state.policy)
        ),
        ("Visualización", describe_sample(getattr(state, "sample", None))),
        ("API", api),
        ("Docs", f"{settings.api_public_url.rstrip('/')}/docs"),
    ]
    title = " Fraud Detector API "
    lines = [title.center(WIDTH, "=")]
    lines += [f"  {label:<14}: {value}" for label, value in rows]
    lines.append("=" * WIDTH)
    return "\n".join(lines)

def log_startup_summary(state: Any, settings: Settings) -> None:
    if logger.isEnabledFor(logging.INFO):
        print(build_summary(state, settings), file=sys.stderr, flush=True)
