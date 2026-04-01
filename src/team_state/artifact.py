from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.team_state.contract import validate_artifact_shape


def write_artifact(artifact: dict[str, Any], output_path: Path) -> Path:
    validate_artifact_shape(artifact)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return output_path
