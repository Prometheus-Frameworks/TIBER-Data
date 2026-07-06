import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "promote_player_season_coverage_v0_2021_2025.py"
    spec = spec_from_file_location("promote_player_season_coverage_v0_2021_2025", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_validator_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "validate_player_season_coverage_v0.py"
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(player_id: str, season: int, position: str = "QB") -> dict:
    return {
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "position": position,
        "identity_confidence": "source_verified",
        "season": season,
        "season_type": "REG",
        "generated_at": "2026-07-06T00:00:00Z",
        "source_refs": [
            {
                "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                "observed_at": "2026-07-06T00:00:00Z",
                "confidence": "source_verified",
            }
        ],
        "teams": ["KC"],
        "primary_team": "KC",
        "weeks_observed": 17,
        "coverage_status": "full_season",
        "coverage_notes": "17 of up to 18 REG week numbers observed.",
        "missing_fields": [],
        "usage_summary": {},
    }


def _candidate(seasons: list[int]) -> dict:
    return {
        "artifact_id": "player_season_coverage_2021_2025.source_backed",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": "2026-07-06T00:00:00Z",
        "seasons": seasons,
        "season_type_scope": ["REG"],
        "row_grain": "player_id + season + season_type",
        "records": [_record(f"00-{s}", s) for s in seasons],
        "merged_from": [{"path": "fake/2021.json", "sha256": "a" * 64, "seasons_contributed": [2021], "record_count": 1}],
    }


def test_build_promoted_payload_happy_path() -> None:
    module = _load_module()
    validator = _load_validator_module()
    candidate = _candidate([2021, 2022])
    sha = "deadbeef" * 8
    promoted = module.build_promoted_payload(candidate, sha, sha, validator, module.PRIOR_PROMOTED_SHA256)
    assert promoted["status"] == "promoted_governed_artifact"
    assert promoted["promotion_review"] == "TIBER-Data#202"
    assert promoted["source_candidate"]["sha256"] == sha
    assert promoted["prior_promoted_artifact"]["promotion_review"] == "TIBER-Data#192"
    assert promoted["counts"]["records"] == 2
    assert "records" in promoted


def test_build_promoted_payload_rejects_sha_mismatch() -> None:
    module = _load_module()
    validator = _load_validator_module()
    candidate = _candidate([2021, 2022])
    with pytest.raises(SystemExit, match="does not match the pin"):
        module.build_promoted_payload(candidate, "a" * 64, "b" * 64, validator, module.PRIOR_PROMOTED_SHA256)


def test_build_promoted_payload_rejects_validator_errors() -> None:
    module = _load_module()
    validator = _load_validator_module()
    candidate = _candidate([2021, 2022])
    del candidate["records"][0]["source_refs"]
    sha = "deadbeef" * 8
    with pytest.raises(SystemExit, match="candidate validator reported"):
        module.build_promoted_payload(candidate, sha, sha, validator, module.PRIOR_PROMOTED_SHA256)


def test_build_promoted_payload_rejects_out_of_scope_position() -> None:
    module = _load_module()
    validator = _load_validator_module()
    candidate = _candidate([2021, 2022])
    candidate["records"][0]["position"] = "K"
    sha = "deadbeef" * 8
    with pytest.raises(SystemExit, match="outside promoted scope"):
        module.build_promoted_payload(candidate, sha, sha, validator, module.PRIOR_PROMOTED_SHA256)


def test_build_promoted_payload_rejects_prior_promoted_drift() -> None:
    module = _load_module()
    validator = _load_validator_module()
    candidate = _candidate([2021, 2022])
    sha = "deadbeef" * 8
    with pytest.raises(SystemExit, match="does not match the expected prior sha256"):
        module.build_promoted_payload(candidate, sha, sha, validator, "0" * 64)


def test_check_envelope_scope_catches_bad_season_type() -> None:
    module = _load_module()
    records = [{"season_type": "POST", "position": "QB"}]
    errors = module.check_envelope_scope(records)
    assert any("season_type" in e for e in errors)


def test_current_pin_matches_committed_promoted_artifact() -> None:
    """Regression guard: PRIOR_PROMOTED_SHA256 must track whatever is actually committed
    at exports/promoted/nfl/player_season_coverage_v0.json until this script is actually run."""
    import hashlib

    module = _load_module()
    if not module.PROMOTED_PATH.exists():
        pytest.skip("promoted artifact not present in this environment")
    payload = json.loads(module.PROMOTED_PATH.read_text(encoding="utf-8"))
    if payload.get("promotion_review") != "TIBER-Data#192":
        pytest.skip("promoted artifact has already moved past the #192 lineage point this script assumes")
    actual_sha = hashlib.sha256(module.PROMOTED_PATH.read_bytes()).hexdigest()
    assert actual_sha == module.PRIOR_PROMOTED_SHA256


def test_pinned_candidate_sha_matches_committed_merged_candidate() -> None:
    import hashlib

    module = _load_module()
    if not module.CANDIDATE_PATH.exists():
        pytest.skip("merged candidate not built in this environment")
    actual_sha = hashlib.sha256(module.CANDIDATE_PATH.read_bytes()).hexdigest()
    assert actual_sha == module.PINNED_CANDIDATE_SHA256
