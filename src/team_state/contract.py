from __future__ import annotations

from typing import Any


class TeamStateValidationError(ValueError):
    pass


REQUIRED_TOP_LEVEL = ["generatedAt", "artifact", "source", "definitions", "teams"]
REQUIRED_SOURCE_KEYS = ["provider", "season", "throughWeek", "seasonType", "gamesIncluded", "notes"]
REQUIRED_TEAM_KEYS = ["team", "sample", "features", "stability"]
REQUIRED_SAMPLE_KEYS = ["games", "plays", "neutralPlays", "earlyDownPlays", "redZonePlays", "drives"]
REQUIRED_FEATURE_KEYS = [
    "neutralPassRate",
    "earlyDownPassRate",
    "earlyDownSuccessRate",
    "redZonePassRate",
    "redZoneTdEfficiency",
    "explosivePlayRate",
    "driveSustainRate",
    "paceSecondsPerPlay",
]
REQUIRED_STABILITY_KEYS = ["sampleFlag", "confidenceBand", "notes"]


def _ensure_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TeamStateValidationError(f"Artifact field '{field_name}' must be an object.")
    return value


def validate_artifact_shape(artifact: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in artifact]
    if missing:
        raise TeamStateValidationError(f"Artifact missing required keys: {missing}")

    if artifact["artifact"] != "tiber_team_state_v0_1":
        raise TeamStateValidationError("Artifact name must be 'tiber_team_state_v0_1'.")

    source = _ensure_object(artifact["source"], "source")
    missing_source_keys = [key for key in REQUIRED_SOURCE_KEYS if key not in source]
    if missing_source_keys:
        raise TeamStateValidationError(
            f"Artifact source missing required keys: {missing_source_keys}"
        )

    if not isinstance(artifact["teams"], list):
        raise TeamStateValidationError("Artifact teams field must be a list.")

    for index, team_row in enumerate(artifact["teams"]):
        team_row = _ensure_object(team_row, f"teams[{index}]")
        missing_team_keys = [key for key in REQUIRED_TEAM_KEYS if key not in team_row]
        if missing_team_keys:
            raise TeamStateValidationError(
                f"Team row at index {index} missing required keys: {missing_team_keys}"
            )

        sample = _ensure_object(team_row["sample"], f"teams[{index}].sample")
        missing_sample_keys = [key for key in REQUIRED_SAMPLE_KEYS if key not in sample]
        if missing_sample_keys:
            raise TeamStateValidationError(
                f"Team row at index {index} sample missing required keys: {missing_sample_keys}"
            )

        features = _ensure_object(team_row["features"], f"teams[{index}].features")
        missing_feature_keys = [key for key in REQUIRED_FEATURE_KEYS if key not in features]
        if missing_feature_keys:
            raise TeamStateValidationError(
                "Team row at index "
                f"{index} features missing required keys: {missing_feature_keys}"
            )

        stability = _ensure_object(team_row["stability"], f"teams[{index}].stability")
        missing_stability_keys = [key for key in REQUIRED_STABILITY_KEYS if key not in stability]
        if missing_stability_keys:
            raise TeamStateValidationError(
                "Team row at index "
                f"{index} stability missing required keys: {missing_stability_keys}"
            )
