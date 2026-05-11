import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "build_forge_2025_ppr_artifacts.py"
    )
    spec = spec_from_file_location("build_forge_2025_ppr_artifacts", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_calculate_ppr_points_uses_documented_formula() -> None:
    module = _load_module()
    row = {
        "passing_yards": 300,
        "passing_tds": 2,
        "interceptions": 1,
        "rushing_yards": 40,
        "rushing_tds": 1,
        "receiving_yards": 25,
        "receiving_tds": 1,
        "receptions": 5,
        "fumbles_lost": 1,
    }

    assert module.calculate_ppr_points(row) == 39.5


def test_build_artifacts_fails_clearly_when_source_backed_input_missing(tmp_path) -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="Missing source-backed 2025 player-week PPR input"):
        module.build_artifacts(
            source_path=tmp_path / "missing.json", roster_source_path=tmp_path / "roster.json"
        )


def test_committed_artifacts_are_source_backed_schema_and_not_fixture_rows() -> None:
    season_path = Path("data/gold/forge/forge_season_player_input_2025.ppr.v1.json")
    weekly_path = Path("data/gold/forge/forge_weekly_player_ppr_2025.v1.json")

    season = json.loads(season_path.read_text(encoding="utf-8"))
    weekly = json.loads(weekly_path.read_text(encoding="utf-8"))

    for artifact in (season, weekly):
        assert artifact["season"] == 2025
        assert artifact["schemaVersion"] == "v1"
        assert artifact["scoringFormat"] == "PPR"
        assert 20 <= artifact["playerCount"] <= 50
        assert (
            artifact["metadata"]["sourceSetId"]
            == "nflreadpy.load_player_stats.2025.regular_season.source_backed"
        )
        assert artifact["metadata"]["asOf"]
        assert artifact["metadata"]["sourceUpdatedAt"]
        assert artifact["metadata"]["buildId"]
        serialized = json.dumps(artifact).lower()
        assert "offline_fixture" not in serialized
        assert "sample" not in serialized

    assert len(season["records"]) == season["playerCount"]
    assert len(weekly["records"]) >= season["playerCount"]
    assert {row["scoringFormat"] for row in season["records"]} == {"PPR"}
    assert {row["scoringFormat"] for row in weekly["records"]} == {"PPR"}
    assert {row["season"] for row in weekly["records"]} == {2025}
    assert all(1 <= row["week"] <= 18 for row in weekly["records"])
    assert {row["position"] for row in season["records"]}.issubset({"QB", "RB", "WR", "TE"})
    assert {row["position"] for row in weekly["records"]}.issubset({"QB", "RB", "WR", "TE"})
