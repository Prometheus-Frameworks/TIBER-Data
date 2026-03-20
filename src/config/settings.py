from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PipelineConfig:
    seasons: list[int] = field(default_factory=lambda: [2024])
    base_dir: Path = Path(__file__).resolve().parents[2]
    overwrite: bool = False
    allow_offline_fallback: bool = True

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def silver_dir(self) -> Path:
        return self.data_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.data_dir / "gold"


def build_config(
    seasons: list[int] | None = None,
    overwrite: bool = False,
    allow_offline_fallback: bool | None = None,
) -> PipelineConfig:
    fallback = allow_offline_fallback
    if fallback is None:
        fallback = os.environ.get("TIBER_ALLOW_OFFLINE_FALLBACK", "1") not in {
            "0",
            "false",
            "False",
        }
    config = PipelineConfig(overwrite=overwrite, allow_offline_fallback=fallback)
    if seasons:
        config.seasons = seasons
    return config
