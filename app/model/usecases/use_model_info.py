from typing import Any

from app.model.model_schema import ModelInfoOut
from config.settings import settings


def execute(model: Any, metrics: Any, policy: Any) -> ModelInfoOut:
    """Versión, variables y umbrales del modelo que está cargado"""
    info = metrics.model_dump() if metrics else {}
    return ModelInfoOut(
        loaded=model is not None,
        version=info.get("version"),
        model_name=info.get("model_name"),
        model_type=info.get("model_type"),
        feature_set=info.get("feature_set"),
        feature_set_label=info.get("feature_set_label"),
        features=info.get("features") or [],
        trained_at=info.get("trained_at"),
        split=info.get("split"),
        threshold=policy.high,
        risk_levels={
            "medium": policy.medium,
            "high": policy.high,
            "source": policy.source,
        },
        threshold_criterion=info.get("threshold_criterion"),
        sha256=info.get("sha256"),
        limits={
            "max_batch_rows": settings.max_batch_rows,
            "max_upload_mb": settings.max_upload_mb,
            "rate_limit_per_minute": settings.rate_limit_per_minute,
        },
    )
