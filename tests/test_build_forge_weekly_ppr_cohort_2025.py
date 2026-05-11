import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_forge_weekly_ppr_cohort_2025.py"
    )
    spec = spec_from_file_location("build_forge_weekly_ppr_cohort_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _number_or_zero(value):
    return 0 if value is None else value


def _ppr_from_artifact_row(row):
    return round(
        _number_or_zero(row["passingYards"]) / 25
        + _number_or_zero(row["passingTDs"]) * 4
        + _number_or_zero(row["interceptions"]) * -2
        + _number_or_zero(row["rushingYards"]) / 10
        + _number_or_zero(row["rushingTDs"]) * 6
        + _number_or_zero(row["receivingYards"]) / 10
        + _number_or_zero(row["receivingTDs"]) * 6
        + _number_or_zero(row["receptions"])
        + _number_or_zero(row["fumblesLost"]) * -2,
        2,
    )


def test_build_cohort_fails_clearly_when_source_backed_input_missing(tmp_path) -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="Missing source-backed 2025 player-week PPR input"):
        module.build_cohort(
            source_path=tmp_path / "missing.json", roster_source_path=tmp_path / "roster.json"
        )


def test_build_cohort_fails_clearly_when_requested_player_cannot_be_resolved(
    tmp_path, monkeypatch
) -> None:
    module = _load_module()
    source_path = tmp_path / "source.json"
    source_path.write_text(
        json.dumps(
            {
                "provenance": "nflreadpy.load_player_stats",
                "source_path": "nflverse player stats via nflreadpy",
                "generated_from": ["test"],
                "records": [
                    {
                        "season": 2025,
                        "week": 1,
                        "player_id": "other-player",
                        "player_name": "Other Player",
                        "team": "BUF",
                        "position": "QB",
                        "opponent": "NYJ",
                        "receptions": 0,
                        "receiving_yards": 0,
                        "receiving_tds": 0,
                        "rushing_attempts": 0,
                        "rushing_yards": 0,
                        "rushing_tds": 0,
                        "passing_yards": 1,
                        "passing_tds": 0,
                        "interceptions": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REQUESTED_PLAYERS", (("missing-player", "Missing Player"),))

    with pytest.raises(ValueError, match="Requested player cannot be resolved"):
        module.build_cohort(source_path=source_path, roster_source_path=tmp_path / "roster.json")


def test_committed_cohort_artifact_builds_and_is_source_backed() -> None:
    module = _load_module()
    artifact_path = Path("data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    rebuilt = module.build_cohort()

    module.validate_cohort(artifact)
    assert artifact == rebuilt
    assert artifact["artifactId"] == "forge_player_weekly_ppr_2025.cohort.v1"
    assert artifact["schemaVersion"] == "cohort.v1"
    assert artifact["season"] == 2025
    assert artifact["scoringFormat"] == "PPR"
    assert 20 <= artifact["playerCount"] <= 50
    assert len(artifact["players"]) == artifact["playerCount"]
    assert artifact["source"]["provider"] == "nflverse via nflreadpy"
    assert artifact["source"]["file"] == (
        "data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json"
    )
    assert artifact["source"]["provenance"] == "nflreadpy.load_player_stats"
    assert artifact["asOf"]
    assert artifact["sourceUpdatedAt"]
    assert artifact["buildId"]

    serialized = json.dumps(artifact).lower()
    assert "offline_fixture" not in serialized
    assert "sample" not in serialized
    assert "offline" not in serialized


def test_all_players_have_source_metadata_and_valid_weekly_formula() -> None:
    artifact = json.loads(
        Path("data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json").read_text(
            encoding="utf-8"
        )
    )

    positions = {player["position"] for player in artifact["players"]}
    assert {"QB", "RB", "WR", "TE"}.issubset(positions)

    for player in artifact["players"]:
        assert player["source"]["provider"]
        assert player["source"]["file"]
        assert player["source"]["path"]
        assert player["source"]["provenance"]
        assert player["weeklyRows"]

        weekly_sum = round(sum(row["pprPoints"] for row in player["weeklyRows"]), 2)
        assert player["seasonTotal"]["pprPoints"] == weekly_sum
        assert player["seasonTotal"]["games"] == len(player["weeklyRows"])
        assert player["seasonTotal"]["weeks"] == [row["week"] for row in player["weeklyRows"]]

        for row in player["weeklyRows"]:
            assert row["playerId"] == player["playerId"]
            assert row["opponent"] is not None
            assert row["gameId"] is None or isinstance(row["gameId"], str)
            assert row["fumblesLost"] is None or isinstance(row["fumblesLost"], int)
            assert row["sourceProvider"]
            assert row["sourceFile"]
            assert row["sourcePath"]
            assert row["sourceProvenance"]
            assert row["asOf"]
            assert row["sourceUpdatedAt"]
            assert row["buildId"]
            assert row["pprPoints"] == _ppr_from_artifact_row(row)


def test_jamarr_chase_totals_match_existing_one_player_proof() -> None:
    cohort = json.loads(
        Path("data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json").read_text(
            encoding="utf-8"
        )
    )
    proof = json.loads(
        Path(
            "data/gold/forge/proofs/forge_player_weekly_ppr_2025_jamarr_chase.proof.json"
        ).read_text(encoding="utf-8")
    )

    jamarr = next(player for player in cohort["players"] if player["playerId"] == "00-0036900")
    assert jamarr["playerName"] == proof["playerName"]
    assert jamarr["team"] == proof["team"]
    assert jamarr["position"] == proof["position"]
    assert jamarr["seasonTotal"]["games"] == proof["seasonTotal"]["games"]
    assert jamarr["seasonTotal"]["weeks"] == proof["seasonTotal"]["weeks"]
    assert jamarr["seasonTotal"]["pprPoints"] == proof["seasonTotal"]["pprPoints"]
    assert [row["pprPoints"] for row in jamarr["weeklyRows"]] == [
        row["pprPoints"] for row in proof["records"]
    ]
