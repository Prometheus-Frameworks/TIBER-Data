from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from src.team_state.compute import build_team_state_artifact
from src.team_state.contract import TeamStateValidationError, validate_artifact_shape


@pytest.fixture
def pbp_fixture() -> pl.DataFrame:
    return pl.read_json(Path("team-state/fixtures/pbp_fixture.json"))


def test_artifact_shape_validates(pbp_fixture: pl.DataFrame) -> None:
    artifact = build_team_state_artifact(pbp_fixture, season=2025, through_week=1)
    validate_artifact_shape(artifact)
    assert artifact["artifact"] == "tiber_team_state_v0_1"
    assert len(artifact["teams"]) == 2


def test_missing_required_top_level_field_fails_validation(pbp_fixture: pl.DataFrame) -> None:
    artifact = build_team_state_artifact(pbp_fixture, season=2025, through_week=1)
    del artifact["definitions"]
    with pytest.raises(TeamStateValidationError):
        validate_artifact_shape(artifact)


def test_empty_input_returns_no_crash_and_empty_teams(pbp_fixture: pl.DataFrame) -> None:
    empty = pbp_fixture.filter(pl.col("posteam") == "NOPE")
    artifact = build_team_state_artifact(empty, season=2025, through_week=1)
    assert artifact["teams"] == []
    assert artifact["source"]["gamesIncluded"] == 0


def test_partial_data_omits_pace_without_crashing(pbp_fixture: pl.DataFrame) -> None:
    partial = pbp_fixture.drop("game_seconds_remaining")
    artifact = build_team_state_artifact(partial, season=2025, through_week=1)
    assert artifact["teams"]
    assert artifact["teams"][0]["features"]["paceSecondsPerPlay"] is None
    assert any(
        "paceSecondsPerPlay omitted" in note
        for note in artifact["teams"][0]["stability"]["notes"]
    )


def test_missing_required_feature_key_fails_validation(pbp_fixture: pl.DataFrame) -> None:
    artifact = build_team_state_artifact(pbp_fixture, season=2025, through_week=1)
    del artifact["teams"][0]["features"]["neutralPassRate"]
    with pytest.raises(TeamStateValidationError, match="features missing required keys"):
        validate_artifact_shape(artifact)


def test_missing_required_source_key_fails_validation(pbp_fixture: pl.DataFrame) -> None:
    artifact = build_team_state_artifact(pbp_fixture, season=2025, through_week=1)
    del artifact["source"]["seasonType"]
    with pytest.raises(TeamStateValidationError, match="source missing required keys"):
        validate_artifact_shape(artifact)
