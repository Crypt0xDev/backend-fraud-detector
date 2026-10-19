from typing import Any

from app.model.model_schema import ExperimentOut
from app.model.usecases.use_model_experiment_list import (
    execute as list_experiment_execute,
)
from utils.errors import NotFoundError


def execute(experiments: dict | None, metrics: Any, version: str) -> ExperimentOut:
    found = list_experiment_execute(experiments=experiments, metrics=metrics)
    experiment = next((e for e in found.experiments if e.version == version), None)
    if experiment is None:
        raise NotFoundError("El experimento no existe")
    return experiment
