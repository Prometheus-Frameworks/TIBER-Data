from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_player_season_coverage_2021_2025_merged_candidate.py"
    )
    spec = spec_from_file_location("build_player_season_coverage_2021_2025_merged_candidate", module_path)
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


def _candidate(seasons: list[int], records: list[dict], row_grain: str = "player_id + season + season_type") -> dict:
    return {
        "artifact_id": "fake_candidate",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": "2026-07-06T00:00:00Z",
        "seasons": seasons,
        "season_type_scope": ["REG"],
        "row_grain": row_grain,
        "records": records,
    }


def test_merge_happy_path_concatenates_and_sorts() -> None:
    module = _load_module()
    validator = _load_validator_module()
    c2021 = _candidate([2021], [_record("00-2", 2021), _record("00-1", 2021)])
    c2022_2025 = _candidate([2022], [_record("00-1", 2022)])
    merged = module.build_merged_candidate(c2021, c2022_2025, validator)
    assert merged["status"] == "candidate_evidence_artifact_not_promoted"
    assert merged["seasons"] == [2021, 2022]
    assert [r["player_id"] for r in merged["records"]] == ["00-1", "00-2", "00-1"]
    assert merged["records"][0]["season"] == 2021
    assert merged["records"][-1]["season"] == 2022


def test_merge_rejects_overlapping_seasons() -> None:
    module = _load_module()
    validator = _load_validator_module()
    c1 = _candidate([2022], [_record("00-1", 2022)])
    c2 = _candidate([2022], [_record("00-2", 2022)])
    with pytest.raises(module.MergeFeasibilityError, match="overlapping season"):
        module.build_merged_candidate(c1, c2, validator)


def test_merge_rejects_duplicate_grain_after_concat() -> None:
    module = _load_module()
    validator = _load_validator_module()
    c1 = _candidate([2021], [_record("00-1", 2021)])
    c2 = _candidate([2022], [_record("00-1", 2021)])  # smuggled-in duplicate season/id via c2
    with pytest.raises(module.MergeFeasibilityError, match="Duplicate grain"):
        module.build_merged_candidate(c1, c2, validator)


def test_merge_rejects_row_grain_mismatch() -> None:
    """The schema's own `const` on row_grain already rejects a deviating value via the
    validator-clean check before the merge's own row_grain-equality check would run;
    the dedicated check remains as defense in depth for any future schema relaxation."""
    module = _load_module()
    validator = _load_validator_module()
    c1 = _candidate([2021], [_record("00-1", 2021)], row_grain="player_id + season")
    c2 = _candidate([2022], [_record("00-2", 2022)], row_grain="player_id + season + season_type")
    with pytest.raises(module.MergeFeasibilityError, match="not validator-clean"):
        module.build_merged_candidate(c1, c2, validator)


def test_merge_rejects_season_type_scope_mismatch() -> None:
    module = _load_module()
    validator = _load_validator_module()
    c1 = _candidate([2021], [_record("00-1", 2021)])
    c1["season_type_scope"] = ["REG", "POST"]
    c2 = _candidate([2022], [_record("00-2", 2022)])
    with pytest.raises(module.MergeFeasibilityError, match="season_type_scope mismatch"):
        module.build_merged_candidate(c1, c2, validator)


def test_merge_rejects_invalid_input_candidate() -> None:
    module = _load_module()
    validator = _load_validator_module()
    bad_record = _record("00-1", 2021)
    del bad_record["source_refs"]
    c1 = _candidate([2021], [bad_record])
    c2 = _candidate([2022], [_record("00-2", 2022)])
    with pytest.raises(module.MergeFeasibilityError, match="not validator-clean"):
        module.build_merged_candidate(c1, c2, validator)


def test_load_pinned_rejects_sha_drift(tmp_path) -> None:
    module = _load_module()
    p = tmp_path / "candidate.json"
    p.write_text('{"records": []}', encoding="utf-8")
    with pytest.raises(module.MergeFeasibilityError, match="does not match the pinned value"):
        module._load_pinned(p, "0" * 64, "test candidate")


def test_load_pinned_rejects_missing_file(tmp_path) -> None:
    module = _load_module()
    missing = tmp_path / "nope.json"
    with pytest.raises(module.MergeFeasibilityError, match="not found"):
        module._load_pinned(missing, "0" * 64, "test candidate")


def test_main_refuses_to_write_under_promoted_path(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        module.REPO_ROOT / "exports" / "promoted" / "nfl" / "player_season_coverage_2021_2025.json",
    )

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("must not read source candidates once the promoted-path guard fires")

    monkeypatch.setattr(module, "_load_pinned", _fail_if_called)

    with pytest.raises(module.MergeFeasibilityError, match="promoted path"):
        module.main()


def test_committed_merged_candidate_reconciles_with_known_counts() -> None:
    """Regression check against the actual committed merge output for TIBER-Data#202."""
    import json

    path = (
        Path(__file__).resolve().parents[1]
        / "data/processed/evidence/player_season_coverage_2021_2025.source_backed.json"
    )
    if not path.exists():
        pytest.skip("merged candidate not built in this environment")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["seasons"] == [2021, 2022, 2023, 2024, 2025]
    assert len(payload["records"]) == 3016
    from collections import Counter

    by_season = Counter(r["season"] for r in payload["records"])
    assert dict(by_season) == {2021: 633, 2022: 609, 2023: 576, 2024: 588, 2025: 610}
