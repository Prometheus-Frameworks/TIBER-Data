from __future__ import annotations

from pathlib import Path


def ensure_directories(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def should_write(path: Path, overwrite: bool) -> bool:
    return overwrite or not path.exists()
