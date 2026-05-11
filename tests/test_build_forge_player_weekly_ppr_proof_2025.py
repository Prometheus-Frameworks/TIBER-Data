import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_forge_player_weekly_ppr_proof_2025.py"
    )
    spec = spec_from_file_location("build_forge_player_weekly_ppr_proof_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_proof_fails_clearly_when_source_backed_input_missing(tmp_path) -> None:
    module = _load_module()

    with pytest.raises(ValueError, match="Missing source-backed 2025 player-week PPR input"):
        module.build_proof(
            source_path=tmp_path / "missing.json", roster_source_path=tmp_path / "roster.json"
        )


def test_committed_jamarr_chase_proof_is_source_backed_and_formula_valid() -> None:
    module = _load_module()
    proof_path = Path(
        "data/gold/forge/proofs/forge_player_weekly_ppr_2025_jamarr_chase.proof.json"
    )
    proof = json.loads(proof_path.read_text(encoding="utf-8"))

    module.validate_proof(proof)

    assert proof["proofType"] == "one_player_source_backed_weekly_ppr_game_log"
    assert proof["playerId"] == "00-0036900"
    assert proof["playerName"] == "Ja'Marr Chase"
    assert proof["team"] == "CIN"
    assert proof["position"] == "WR"
    assert proof["season"] == 2025
    assert proof["scoringFormat"] == "PPR"
    assert proof["source"]["provider"] == "nflverse via nflreadpy"
    assert proof["source"]["file"] == (
        "data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json"
    )
    assert proof["source"]["provenance"] == "nflreadpy.load_player_stats"
    assert proof["asOf"]
    assert proof["sourceUpdatedAt"]
    assert proof["buildId"]
    assert proof["records"]

    weekly_sum = module._round(sum(row["pprPoints"] for row in proof["records"]), 2)
    assert weekly_sum == proof["seasonTotal"]["pprPoints"]

    seen_week_games = set()
    for row in proof["records"]:
        key = (row["week"], row["gameId"], row["opponent"])
        assert key not in seen_week_games
        seen_week_games.add(key)
        assert row["playerId"] == proof["playerId"]
        assert row["playerName"] == proof["playerName"]
        assert row["sourceProvider"]
        assert row["sourceFile"]
        assert row["asOf"]
        assert row["sourceUpdatedAt"]
        assert row["buildId"]

    serialized = json.dumps(proof).lower()
    assert "offline_fixture" not in serialized
    assert "sample" not in serialized
