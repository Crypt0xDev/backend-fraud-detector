from typing import Any

from app.model.model_schema import ExperimentOut
from app.model.usecases.use_model_experiment_list import (
    execute as list_experiment_execute,
)


def execute(
    experiments: dict | None, metrics: Any, version: str
) -> ExperimentOut | None:
    found = list_experiment_execute(experiments=experiments, metrics=metrics)
    return next((e for e in found.experiments if e.version == version), None)
