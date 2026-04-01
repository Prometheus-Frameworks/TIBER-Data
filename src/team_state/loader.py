from __future__ import annotations

from pathlib import Path
from typing import Any

import nflreadpy

from src.utils.frames import require_polars


def load_pbp_for_season(
    season: int,
    through_week: int | None = None,
    pbp_path: str | None = None,
) -> Any:
    pl = require_polars()
    if pbp_path:
        path = Path(pbp_path)
        if path.suffix == ".parquet":
            frame = pl.read_parquet(path)
        elif path.suffix == ".csv":
            frame = pl.read_csv(path)
        elif path.suffix == ".json":
            frame = pl.read_json(path)
        else:
            raise ValueError(f"Unsupported pbp file extension: {path.suffix}")
    else:
        frame = nflreadpy.load_pbp(seasons=[season])

    filtered = frame.filter((pl.col("season") == season) & (pl.col("season_type") == "REG"))
    if through_week is not None:
        filtered = filtered.filter(pl.col("week") <= through_week)
    return filtered
