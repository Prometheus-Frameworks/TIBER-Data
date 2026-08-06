import json
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK_PATH = ROOT / "exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.json"
CONFLICT_PATH = ROOT / "exports/candidates/identity_crosswalk/rookie_2023_identity_conflicts_v0.1.0.json"
MANIFEST_PATH = ROOT / "exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.manifest.json"


def _module(name: str, path: str):
    spec = spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _module("rookie_2023_builder", "scripts/build_rookie_2023_identity_crosswalk_candidate.py")


@pytest.fixture(scope="module")
def validator():
    return _module("rookie_2023_validator", "scripts/validate_rookie_2023_identity_crosswalk_candidate.py")


@pytest.fixture()
def payloads():
    return (
        json.loads(CROSSWALK_PATH.read_text(encoding="utf-8")),
        json.loads(CONFLICT_PATH.read_text(encoding="utf-8")),
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
    )


def test_committed_candidate_validates_and_rebuilds_deterministically(validator) -> None:
    report, errors = validator.validate_committed()
    assert errors == []
    assert report["valid"] is True


@pytest.mark.skipif(
    not (ROOT.parent / "TIBER-Rookies").exists() or not (ROOT.parent / "TIBER-Forecast").exists(),
    reason="sibling source repositories are not available in this checkout",
)
def test_cross_repo_source_blobs_and_forecast_row_pins_reproduce(validator) -> None:
    assert validator.validate_cross_repo_sources(
        ROOT.parent / "TIBER-Rookies",
        ROOT.parent / "TIBER-Forecast",
    ) == []


def test_forecast_assertion_fingerprint_is_bound_to_exact_seed_row(validator) -> None:
    seed_line = (
        "  { player_id: '00-0038543', player_name: 'Puka Nacua', position: 'WR', "
        "team_2024: 'LAR', games_2024: 11, ppr_2024: 211.0, receptions_2024: 79, "
        "targets_2024: 106, rush_attempts_2024: 8, ppr_2025_actual: 314.7 },\n"
    )
    assertion = {
        "assertion_id": "forecast-run1-subject-puka-nacua",
        "assertion_kind": "subject_identity_conflict",
        "non_name_fingerprint": {
            "season": 2024,
            "position": "WR",
            "canonical_team": "LAR",
            "games_played": 11,
            "receptions": 79,
            "targets": 106,
        },
    }

    assert validator.validate_forecast_assertion_seed_binding(assertion, seed_line) == []

    tampered = deepcopy(assertion)
    tampered["non_name_fingerprint"]["targets"] = 105
    errors = validator.validate_forecast_assertion_seed_binding(tampered, seed_line)
    assert any("fingerprint differs" in error for error in errors)


def test_census_has_all_80_unique_players_and_expected_positions(payloads) -> None:
    crosswalk, _, _ = payloads
    rows = crosswalk["records"]
    assert len(rows) == 80
    assert len({row["overall_pick"] for row in rows}) == 80
    assert len({row["crosswalk_row_id"] for row in rows}) == 80
    assert len({row["core_identity"]["gsis_id"] for row in rows}) == 80
    assert len({row["core_identity"]["rookies_slug"] for row in rows}) == 80
    assert crosswalk["coverage_summary"]["position_counts"] == {
        "QB": 14,
        "RB": 18,
        "TE": 15,
        "WR": 33,
    }


def test_data_source_player_resolution_is_exact_gsis_only_with_explicit_four_row_gap(payloads) -> None:
    crosswalk, _, _ = payloads
    missing = {
        row["core_identity"]["gsis_id"]
        for row in crosswalk["records"]
        if row["core_identity"]["tiber_data_source_player_id"] is None
    }
    assert missing == {"00-0038406", "00-0038637", "00-0039046", "00-0039107"}
    resolved = [
        row
        for row in crosswalk["records"]
        if row["core_identity"]["tiber_data_source_player_id"] is not None
    ]
    assert len(resolved) == 76
    assert all(
        row["core_identity"]["tiber_data_source_player_id"]
        == row["core_identity"]["gsis_id"]
        for row in resolved
    )
    assert all(
        row["core_identity"]["data_identity_corroboration"]["status"]
        == "exact_gsis_and_draft_metadata_agree"
        for row in resolved
    )
    assert all(row["core_identity"]["join_method"] == "exact_gsis_only" for row in crosswalk["records"])
    assert all(row["core_identity"]["tiber_canonical_player_id"] is None for row in crosswalk["records"])
    assert crosswalk["coverage_summary"]["tiber_canonical_player_id_resolved_count"] == 0
    assert crosswalk["coverage_summary"]["tiber_canonical_player_id_unresolved_count"] == 80


def test_data_coverage_distinguishes_draft_season_from_later_only(payloads) -> None:
    crosswalk, _, _ = payloads
    statuses = crosswalk["coverage_summary"]["tiber_data_source_player_id_status_counts"]
    assert statuses == {
        "exact_gsis_source_verified_in_2023_reg": 68,
        "exact_gsis_source_verified_in_later_promoted_reg_only": 8,
        "unresolved_no_governed_data_record": 4,
    }


def test_display_name_is_not_a_join_key(payloads, validator) -> None:
    crosswalk, _, _ = payloads
    assert "display_name" not in crosswalk["join_contract"]["allowed_player_join_keys"]
    assert "display_name" in crosswalk["join_contract"]["forbidden_player_join_keys"]
    with pytest.raises(validator.ValidationFailure, match="exact GSIS"):
        validator.resolve_core_identity(crosswalk, "Puka Nacua")


def test_descriptor_differences_stay_audit_only(payloads) -> None:
    crosswalk, _, _ = payloads
    rows = {row["core_identity"]["gsis_id"]: row for row in crosswalk["records"]}
    assert rows["00-0038976"]["data_history_audit_context"]["descriptor_variances"][0]["identity_effect"] == "none"
    assert any(
        variance["field"] == "position_context" and variance["identity_effect"] == "none"
        for variance in rows["00-0038590"]["data_history_audit_context"]["descriptor_variances"]
    )


def test_puka_forecast_conflict_preserves_both_ids_and_fails_closed(payloads, validator) -> None:
    crosswalk, conflicts, _ = payloads
    puka = validator.resolve_core_identity(crosswalk, "00-0039075")
    link = puka["forecast_link"]
    assert link["status"] == "conflict_blocked"
    assert link["resolved_forecast_row_identity"] is None
    assert link["subject_assertions"][0]["forecast_raw_player_id"] == "00-0038543"
    assert puka["identity_aliases"] == []
    assert conflicts["puka_required_conflict"] == {
        "forecast_raw_gsis": "00-0038543",
        "governed_gsis": "00-0039075",
        "status": "unresolved_fail_closed",
        "resolution": None,
        "note": "00-0038543 remains the governed GSIS for Jaxon Smith-Njigba; it is never a Puka alias.",
    }
    with pytest.raises(validator.ValidationFailure, match="conflict-blocked"):
        validator.resolve_forecast_identity(crosswalk, "forecast-run1-subject-puka-nacua")


def test_all_forecast_conflicts_and_collision_exposures_are_explicit(payloads) -> None:
    crosswalk, conflicts, _ = payloads
    assert crosswalk["coverage_summary"]["forecast_subject_link_counts"] == {
        "resolved": 0,
        "conflict_blocked": 8,
        "not_present": 72,
    }
    assert crosswalk["coverage_summary"]["forecast_census_risk_counts"] == {
        "conflict_blocked": 11,
        "no_known_run1_subject_or_collision": 69,
    }
    assert conflicts["summary"] == {
        "subject_identity_conflicts": 8,
        "raw_id_collision_findings": 5,
        "unique_forecast_source_rows": 11,
        "affected_census_rows": 11,
        "resolved_conflicts": 0,
        "open_conflicts": 13,
    }
    assert all(item["status"] == "unresolved" and item["resolution"] is None for item in conflicts["conflicts"])
    subject_assertions = [
        assertion
        for row in crosswalk["records"]
        for assertion in row["forecast_link"]["subject_assertions"]
    ]
    assert all(item["association_status"] == "needs_operator_review" for item in subject_assertions)
    assert all(item["association_method"] == "explicit_candidate_override_unique_non_name_fingerprint" for item in subject_assertions)


def test_tank_dell_override_is_explicit_and_lineage_complete(payloads) -> None:
    crosswalk, _, _ = payloads
    override = crosswalk["explicit_name_overrides"][0]
    assert override["key_namespace"] == "gsis"
    assert override["key_value"] == "00-0038977"
    assert override["upstream_display_name"] == "Nathaniel Dell"
    assert override["target_rookies_slug"] == "wr-tank-dell"
    assert override["resolution_effect"] == "slug_assertion_lineage_only"
    assert len(override["lineage"]) == 2
    assert all(item["git_commit"] and item["git_blob"] and item["sha256"] for item in override["lineage"])


def test_rams_alias_policy_is_directional_scoped_and_lac_stays_distinct(builder, payloads) -> None:
    crosswalk, _, _ = payloads
    assert builder.normalize_team_code("LA", source_namespace="tiber_data_player_season", season=2024) == (
        "LAR",
        "tiber-data-candidate-la-to-lar-supported-2023-2025",
    )
    assert builder.normalize_team_code("LAR", source_namespace="nflverse_draft_results", season=2023) == (
        "LAR",
        "canonical-code-idempotent",
    )
    assert builder.normalize_team_code("LAC", source_namespace="tiber_data_player_season", season=2024) == (
        "LAC",
        "canonical-code-idempotent",
    )
    with pytest.raises(builder.BuildFailure, match="unrecognized or unscoped"):
        builder.normalize_team_code("LA", source_namespace="unknown", season=2024)
    with pytest.raises(builder.BuildFailure, match="unrecognized or unscoped"):
        builder.normalize_team_code("LA", source_namespace="tiber_data_player_season", season=2016)
    with pytest.raises(builder.BuildFailure, match="unrecognized or unscoped"):
        builder.normalize_team_code("LA", source_namespace="tiber_data_player_season", season=2022)
    policy = crosswalk["canonical_team_code_policy"]
    assert policy["canonical_rams_code"] == "LAR"
    assert policy["rams_alias_policy"]["reverse_emission_allowed"] is False
    assert policy["rams_alias_policy"]["supported_source_seasons"] == [2023, 2024, 2025]
    assert policy["rams_alias_policy"]["exact_gsis_draft_metadata_evidence_count"] == 3


def test_validator_rejects_duplicate_gsis(payloads, validator) -> None:
    crosswalk, conflicts, manifest = deepcopy(payloads)
    crosswalk["records"][1]["core_identity"]["gsis_id"] = crosswalk["records"][0]["core_identity"]["gsis_id"]
    errors = validator.validate_payloads(crosswalk, conflicts, manifest)
    assert "duplicate gsis_id" in errors


def test_validator_rejects_open_conflict_resolution(payloads, validator) -> None:
    crosswalk, conflicts, manifest = deepcopy(payloads)
    puka = next(row for row in crosswalk["records"] if row["core_identity"]["gsis_id"] == "00-0039075")
    puka["forecast_link"]["resolved_forecast_row_identity"] = "forecast:00-0038543"
    errors = validator.validate_payloads(crosswalk, conflicts, manifest)
    assert any("resolves a Forecast conflict" in error for error in errors)


def test_manifest_binds_downstream_to_version_and_hash(payloads, builder) -> None:
    crosswalk, conflicts, manifest = payloads
    crosswalk_hash = builder.sha256(builder.serialize(crosswalk))
    assert manifest["downstream_binding"] == {
        "required_version": "0.1.0",
        "required_crosswalk_sha256": crosswalk_hash,
        "fail_on_mismatch": True,
        "allowed_identity_edge": "gsis_to_tiber_data_source_player_id",
        "tiber_canonical_player_id_edge_authorized": False,
    }
    assert conflicts["crosswalk_ref"]["sha256"] == crosswalk_hash


def test_candidate_authorizes_no_promotion_or_forecast_mutation(payloads) -> None:
    crosswalk, conflicts, manifest = payloads
    assert crosswalk["promotion_authorized"] is False
    assert crosswalk["forecast_mutation_authorized"] is False
    assert manifest["promotion_authorized"] is False
    assert conflicts["impacted_artifact_inventory"]["tiber_forecast"]["mutation_authorized"] is False
    assert crosswalk["consumer_readiness"]["emitted_forecast_artifacts"] == (
        "emitted_artifact_identity_remediation_requires_operator_decision"
    )
