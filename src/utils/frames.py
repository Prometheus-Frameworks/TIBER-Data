from __future__ import annotations

import importlib
from typing import Any


class DependencyError(RuntimeError):
    """Raised when optional ETL dependencies are unavailable."""


def require_polars() -> Any:
    try:
        return importlib.import_module("polars")
    except ModuleNotFoundError as exc:
        raise DependencyError(
            "polars is required to run the TIBER-Data pipeline. Install project dependencies first."
        ) from exc
