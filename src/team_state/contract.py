from __future__ import annotations

from typing import Any


class TeamStateValidationError(ValueError):
    pass


REQUIRED_TOP_LEVEL = ["generatedAt", "artifact", "source", "definitions", "teams"]
REQUIRED_TEAM_KEYS = ["team", "sample", "features", "stability"]


def validate_artifact_shape(artifact: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in artifact]
    if missing:
        raise TeamStateValidationError(f"Artifact missing required keys: {missing}")

    if artifact["artifact"] != "tiber_team_state_v0_1":
        raise TeamStateValidationError("Artifact name must be 'tiber_team_state_v0_1'.")

    if not isinstance(artifact["teams"], list):
        raise TeamStateValidationError("Artifact teams field must be a list.")

    for index, team_row in enumerate(artifact["teams"]):
        missing_team_keys = [key for key in REQUIRED_TEAM_KEYS if key not in team_row]
        if missing_team_keys:
            raise TeamStateValidationError(
                f"Team row at index {index} missing required keys: {missing_team_keys}"
            )
