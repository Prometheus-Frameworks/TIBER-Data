from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    module_path = REPO_ROOT / "scripts" / "validate_player_season_coverage_v0.py"
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_record(**overrides) -> dict:
    record = {
        "player_id": "p1",
        "player_name": "Test Player",
        "position": "WR",
        "identity_confidence": "source_verified",
        "season": 2023,
        "season_type": "REG",
        "generated_at": "2026-06-30T00:00:00+00:00",
        "source_refs": [
            {
                "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                "observed_at": "2026-06-30T00:00:00+00:00",
                "confidence": "source_verified",
            }
        ],
        "teams": ["PHI"],
        "primary_team": "PHI",
        "primary_team_rule": None,
        "team_weeks": [{"team": "PHI", "weeks_observed": 10}],
        "team_unknown": False,
        "weeks_observed": 10,
        "games_observed": 10,
        "games_played": 10,
        "games_missed": None,
        "coverage_status": "partial_season",
        "coverage_notes": "10 of 17 REG weeks observed.",
        "missing_fields": ["games_missed"],
        "production_summary": {"season_ppr": 100.0},
        "usage_summary": {
            "targets": 50,
            "snap_share": None,
            "routes_run": None,
            "route_participation": None,
            "red_zone_targets": None,
            "red_zone_carries": None,
        },
        "birth_date": "1998-01-01",
        "season_age": 25.5,
        "draft_year": 2020,
        "rookie_year": 2020,
        "career_year": 4,
    }
    record.update(overrides)
    return record


def _base_payload(records: list[dict]) -> dict:
    return {
        "artifact_id": "test",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": "2026-06-30T00:00:00+00:00",
        "seasons": [2023],
        "season_type_scope": ["REG"],
        "row_grain": "player_id + season + season_type",
        "records": records,
    }


def test_valid_payload_passes() -> None:
    module = _load_module()
    payload = _base_payload([_base_record()])
    errors = module.validate_payload(payload)
    assert errors == []


def test_missing_season_type_fails() -> None:
    module = _load_module()
    record = _base_record()
    del record["season_type"]
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("season_type" in e for e in errors)


def test_invalid_season_type_value_fails() -> None:
    module = _load_module()
    record = _base_record(season_type="WEIRD")
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("season_type" in e for e in errors)


def test_duplicate_grain_fails() -> None:
    module = _load_module()
    payload = _base_payload([_base_record(), _base_record()])
    errors = module.validate_payload(payload)
    assert any("duplicate grain" in e for e in errors)


def test_missing_source_refs_fails() -> None:
    module = _load_module()
    record = _base_record(source_refs=[])
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("source_refs" in e for e in errors)


def test_multi_team_without_primary_team_rule_fails() -> None:
    module = _load_module()
    record = _base_record(teams=["PHI", "DAL"], primary_team_rule=None)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("primary_team_rule" in e for e in errors)


def test_multi_team_with_primary_team_rule_passes() -> None:
    module = _load_module()
    record = _base_record(teams=["PHI", "DAL"], primary_team_rule="most weeks observed")
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert errors == []


def test_active_status_field_present_fails() -> None:
    module = _load_module()
    record = _base_record()
    record["active_status"] = "active"
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("forbidden availability" in e for e in errors)


def test_ownership_status_field_present_fails() -> None:
    module = _load_module()
    record = _base_record()
    record["ownership_status"] = "active_roster"
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("forbidden availability" in e for e in errors)


def test_fixture_source_rejected() -> None:
    module = _load_module()
    record = _base_record(
        source_refs=[
            {
                "source_name": "offline_fixture:data/raw/evidence/whatever.json",
                "observed_at": "2026-06-30T00:00:00+00:00",
                "confidence": "fixture_only",
            }
        ]
    )
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("fixture/scaffold" in e for e in errors)


def test_season_age_fabricated_without_birth_date_fails() -> None:
    module = _load_module()
    record = _base_record(birth_date=None, season_age=25.5)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("fabrication" in e for e in errors)


def test_career_year_fabricated_without_rookie_year_fails() -> None:
    module = _load_module()
    record = _base_record(rookie_year=None, career_year=4)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("fabrication" in e for e in errors)


def test_missing_birth_date_with_null_season_age_passes() -> None:
    module = _load_module()
    record = _base_record(birth_date=None, season_age=None, rookie_year=None, career_year=None)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert errors == []


def test_zero_instead_of_null_for_unavailable_usage_field_fails() -> None:
    module = _load_module()
    record = _base_record()
    record["usage_summary"] = dict(record["usage_summary"], snap_share=0)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert any("snap_share" in e and "null" in e for e in errors)


def test_zero_target_count_is_not_flagged_as_unavailable_violation() -> None:
    """targets=0 is a legitimate zero (e.g. a non-receiver), not in the always-unavailable list."""
    module = _load_module()
    record = _base_record()
    record["usage_summary"] = dict(record["usage_summary"], targets=0)
    payload = _base_payload([record])
    errors = module.validate_payload(payload)
    assert errors == []


def test_wrong_artifact_status_fails() -> None:
    module = _load_module()
    payload = _base_payload([_base_record()])
    payload["status"] = "promoted"
    errors = module.validate_payload(payload)
    assert any("candidate_evidence_artifact_not_promoted" in e for e in errors)


def test_empty_records_fails() -> None:
    module = _load_module()
    payload = _base_payload([])
    errors = module.validate_payload(payload)
    assert any("no records" in e for e in errors)
