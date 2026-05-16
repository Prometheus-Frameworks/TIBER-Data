from __future__ import annotations

import ast
import json
from pathlib import Path


def _fixture_data() -> dict[str, list[dict]]:
    source = Path("src/ingest/public.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "FIXTURE_DATA" and node.value is not None:
                return ast.literal_eval(node.value)
    raise AssertionError("FIXTURE_DATA definition not found in src/ingest/public.py")


def _raw_records(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload["records"]


def _weeks(records: list[dict]) -> set[int]:
    return {
        int(record["week"])
        for record in records
        if int(record["season"]) == 2024
    }


def test_w2_to_w6_offline_support_is_not_claimed_reproducible_from_fixture_data() -> None:
    fixture_data = _fixture_data()

    fixture_player_weeks = _weeks(fixture_data["weekly_player_stats"])
    fixture_team_weeks = _weeks(fixture_data["team_week_context"])

    raw_player_weeks = _weeks(
        _raw_records("data/raw/forge/weekly_player_stats.offline_fixture.json")
    )
    raw_team_weeks = _weeks(_raw_records("data/raw/forge/team_week_context.offline_fixture.json"))

    assert fixture_player_weeks == {1}
    assert fixture_team_weeks == {1}
    assert raw_player_weeks == {1, 2, 3, 4, 5, 6}
    assert raw_team_weeks == {1, 2, 3, 4, 5, 6}


def test_offline_support_provenance_manifest_matches_current_source_boundaries() -> None:
    manifest = json.loads(
        Path("data/forge_weekly_offline_support_provenance_manifest.json").read_text(encoding="utf-8")
    )
    fixture_data = _fixture_data()

    fixture_weeks = _weeks(fixture_data["weekly_player_stats"]) & _weeks(
        fixture_data["team_week_context"]
    )
    raw_weeks = _weeks(
        _raw_records("data/raw/forge/weekly_player_stats.offline_fixture.json")
    ) & _weeks(_raw_records("data/raw/forge/team_week_context.offline_fixture.json"))

    assert manifest["reproducibility"]["fixture_reproducible_weeks"] == sorted(fixture_weeks)
    assert manifest["reproducibility"]["legacy_repo_held_weeks"] == sorted(
        raw_weeks - fixture_weeks
    )
    assert manifest["reproducibility"]["blocked_weeks"] == [4, 5, 6]
    assert manifest["reproducibility"]["separate_upstream_proof_reference_weeks"] == [1, 2, 3]


def test_upstream_proof_snapshot_does_not_claim_w4_to_w6_support() -> None:
    manifest = json.loads(
        Path("data/forge_weekly_upstream_w01_w03_atl_det_proof_reference_snapshot_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    player_weeks = _weeks(
        _raw_records(
            "data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.proof_reference_snapshot.json"
        )
    )
    team_weeks = _weeks(
        _raw_records(
            "data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.proof_reference_snapshot.json"
        )
    )

    assert manifest["scope"]["weeks"] == [1, 2, 3]
    assert sorted(player_weeks & team_weeks) == [1, 2, 3]
    assert not ({4, 5, 6} & player_weeks)
    assert not ({4, 5, 6} & team_weeks)
