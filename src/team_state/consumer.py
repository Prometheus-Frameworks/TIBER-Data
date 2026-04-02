from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.settings import build_config

ARTIFACT_NAME = "tiber_team_state_v0_1"
ARTIFACT_SOURCE = "tiber-data"


@dataclass(slots=True)
class TeamStateArtifactNotFoundError(Exception):
    season: int
    through_week: int | None
    searched_paths: list[Path]


@dataclass(slots=True)
class TeamStateArtifactInvalidError(Exception):
    path: Path
    reason: str


def _artifact_root() -> Path:
    configured = os.environ.get("TIBER_TEAM_STATE_ARTIFACT_DIR")
    if configured:
        return Path(configured)
    return build_config().base_dir / "team-state" / "artifacts"


def _candidate_paths(season: int, through_week: int | None) -> list[Path]:
    root = _artifact_root()
    candidates: list[str] = []
    if through_week is not None:
        candidates.append(f"{ARTIFACT_NAME}_{season}_through_week_{through_week}.json")
    candidates.extend(
        [
            f"{ARTIFACT_NAME}_{season}.json",
            f"{ARTIFACT_NAME}.json",
            f"{ARTIFACT_NAME}.sample.json",
        ]
    )
    return [root / file_name for file_name in candidates]


def load_team_state_artifact(season: int, through_week: int | None = None) -> tuple[dict[str, Any], Path]:
    searched_paths = _candidate_paths(season=season, through_week=through_week)
    target_path = next((candidate for candidate in searched_paths if candidate.exists()), None)
    if target_path is None:
        raise TeamStateArtifactNotFoundError(
            season=season,
            through_week=through_week,
            searched_paths=searched_paths,
        )

    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TeamStateArtifactInvalidError(path=target_path, reason=str(exc)) from exc

    if not isinstance(payload, dict):
        raise TeamStateArtifactInvalidError(
            path=target_path,
            reason="Artifact payload must be a JSON object.",
        )

    return payload, target_path
