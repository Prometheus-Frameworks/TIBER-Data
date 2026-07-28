"""Tests for the governed TIBER-Data #228 scoring reconciliation evidence."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "reconcile_player_season_coverage_ppr_v1.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("reconcile_ppr_v1", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECONCILE = _load_module()


def _row() -> dict:
    return {
        "player_id": "00-test",
        "player_name": "Test Player",
        "position": "RB",
        "identity_confidence": "source_verified",
        "season": 2024,
        "season_type": "REG",
        "weeks_observed": 15,
        "coverage_status": "full_season",
        "production_summary": {
            "season_ppr": 0,
            "passing": {
                "passing_yards": 0,
                "passing_tds": 0,
                "interceptions": 0,
            },
            "rushing": {
                "rushing_yards": 0,
                "rushing_tds": 0,
            },
            "receiving": {
                "receiving_yards": 0,
                "receiving_tds": 0,
            },
        },
        "usage_summary": {"receptions": 0},
    }


def _artifact(outputs: dict[Path, bytes]) -> dict:
    return json.loads(outputs[RECONCILE.RECONCILIATION_PATH])


def _set_path(row: dict, path: tuple[str, ...], value: object) -> None:
    target = row
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def test_profile_hash_is_stable_and_covers_exact_operator_profile():
    assert (
        RECONCILE.PROFILE_SHA256
        == "b1404afb1c7c6c9760b36090e5a84ef3fd2a29dfe8ba2e2fe0efb98d0ac6622e"
    )
    profile = RECONCILE.SCORING_PROFILE
    assert profile["profile_id"] == "tiber-generic-full-ppr-v1"
    assert profile["league_specific"] is False
    assert profile["regular_season_only"] is True
    assert profile["supported_positions"] == ["QB", "RB", "WR", "TE"]
    assert profile["bonuses"] == "none"
    assert profile["scoring"] == {
        "reception": "1",
        "receiving_yard": "0.1",
        "receiving_touchdown": "6",
        "rushing_yard": "0.1",
        "rushing_touchdown": "6",
        "passing_yard": "0.04",
        "passing_touchdown": "4",
        "interception": "-2",
    }
    assert (
        hashlib.sha256(RECONCILE.canonical_json_bytes(profile)).hexdigest()
        == RECONCILE.PROFILE_SHA256
    )


def test_contract_binds_profile_terms_to_paths_and_defines_status_precedence():
    contract = json.loads(RECONCILE.build_outputs()[RECONCILE.CONTRACT_PATH])
    assert contract["profile"]["canonical_json_rule"].endswith(
        "profile.definition only"
    )
    assert contract["component_bindings"] == [
        {
            "component_name": component["name"],
            "profile_term": component["profile_term"],
            "source_path": ".".join(component["path"]),
            "weight": str(component["weight"]),
            "input_type": "finite_integer_valued_json_number",
        }
        for component in RECONCILE.COMPONENTS
    ]
    status_contract = contract["reconciliation_status_contract"]
    assert [item["status"] for item in status_contract["ordered_precedence"]] == [
        "unsupported_position",
        "identity_unresolved",
        "regular_season_scope_unresolved",
        "season_incomplete",
        "component_missing",
        "source_total_missing",
        "reconciled_exact",
        "reconciled_within_tolerance",
        "scoring_mismatch",
    ]
    assert set(status_contract["status_definitions"]) == set(
        RECONCILE.RECONCILIATION_STATES
    )
    fixed_reason_codes = status_contract["reason_code_vocabulary"]["fixed"]
    emitted_fixed_codes = {
        reason_code
        for item in status_contract["ordered_precedence"]
        for reason_code in item["reason_codes"]
        if "<" not in reason_code
    }
    assert emitted_fixed_codes == set(fixed_reason_codes)


def test_genuine_zero_is_observed_and_never_treated_as_missing():
    evidence = RECONCILE.evaluate_row(_row(), 0)
    assert evidence["reconciliation_status"] == "reconciled_exact"
    assert evidence["derived_generic_ppr"] == "0.00"
    assert evidence["promoted_source_season_ppr"] == "0.00"
    assert evidence["component_availability"] == "complete"
    assert evidence["missing_components"] == []
    assert evidence["observed_zero_components"] == sorted(
        component["name"] for component in RECONCILE.COMPONENTS
    )


def test_missing_component_is_null_not_zero_filled():
    row = _row()
    row["usage_summary"]["receptions"] = None
    evidence = RECONCILE.evaluate_row(row, 0)
    assert evidence["reconciliation_status"] == "component_missing"
    assert evidence["component_values"]["receptions"] is None
    assert evidence["derived_generic_ppr"] is None
    assert evidence["missing_components"] == ["usage_summary.receptions"]


def test_missing_source_total_remains_missing():
    row = _row()
    row["production_summary"]["season_ppr"] = None
    evidence = RECONCILE.evaluate_row(row, 0)
    assert evidence["reconciliation_status"] == "source_total_missing"
    assert evidence["promoted_source_season_ppr"] is None
    assert evidence["derived_generic_ppr"] == "0.00"


@pytest.mark.parametrize(
    "path",
    [component["path"] for component in RECONCILE.COMPONENTS],
)
def test_numeric_strings_are_rejected_for_every_scoring_component(path):
    row = _row()
    _set_path(row, path, "1")
    with pytest.raises(RECONCILE.ReconciliationError, match="finite JSON number"):
        RECONCILE.evaluate_row(row, 0)


@pytest.mark.parametrize(
    "path",
    [component["path"] for component in RECONCILE.COMPONENTS],
)
def test_fractional_values_are_rejected_for_every_scoring_component(path):
    row = _row()
    _set_path(row, path, 1.5)
    with pytest.raises(
        RECONCILE.ReconciliationError, match="integer-valued JSON number"
    ):
        RECONCILE.evaluate_row(row, 0)


def test_integral_json_float_components_and_fractional_source_total_are_valid():
    row = _row()
    row["usage_summary"]["receptions"] = 1.0
    row["production_summary"]["season_ppr"] = 1.004
    evidence = RECONCILE.evaluate_row(row, 0)
    assert evidence["component_values"]["receptions"] == "1"
    assert evidence["promoted_source_season_ppr"] == "1.00"
    assert evidence["reconciliation_status"] == "reconciled_exact"


def test_numeric_string_source_total_is_rejected():
    row = _row()
    row["production_summary"]["season_ppr"] = "0"
    with pytest.raises(RECONCILE.ReconciliationError, match="finite JSON number"):
        RECONCILE.evaluate_row(row, 0)


def test_reconciliation_status_precedence_resolves_colliding_failures():
    unsupported = _row()
    unsupported["position"] = "K"
    unsupported["identity_confidence"] = "unresolved"
    unsupported["weeks_observed"] = 19
    unsupported["usage_summary"]["receptions"] = None
    assert (
        RECONCILE.evaluate_row(unsupported, 0)["reconciliation_status"]
        == "unsupported_position"
    )

    unresolved = _row()
    unresolved["identity_confidence"] = "unresolved"
    unresolved["weeks_observed"] = 19
    unresolved["usage_summary"]["receptions"] = None
    assert (
        RECONCILE.evaluate_row(unresolved, 0)["reconciliation_status"]
        == "identity_unresolved"
    )

    out_of_scope = _row()
    out_of_scope["weeks_observed"] = 19
    out_of_scope["usage_summary"]["receptions"] = None
    assert (
        RECONCILE.evaluate_row(out_of_scope, 0)["reconciliation_status"]
        == "regular_season_scope_unresolved"
    )


def test_rounding_boundary_normalizes_residue_but_rejects_one_cent_delta():
    residue = _row()
    residue["production_summary"]["passing"]["passing_yards"] = 1
    residue["production_summary"]["season_ppr"] = 0.044
    residue_evidence = RECONCILE.evaluate_row(residue, 0)
    assert residue_evidence["derived_generic_ppr"] == "0.04"
    assert residue_evidence["absolute_delta"] == "0.00"
    assert residue_evidence["absolute_delta_unrounded"] == "0.004"
    assert residue_evidence["reconciliation_status"] == "reconciled_exact"

    one_cent = copy.deepcopy(residue)
    one_cent["production_summary"]["season_ppr"] = 0.045
    one_cent_evidence = RECONCILE.evaluate_row(one_cent, 0)
    assert one_cent_evidence["absolute_delta"] == "0.01"
    assert one_cent_evidence["absolute_delta_unrounded"] == "0.005"
    assert one_cent_evidence["reconciliation_status"] == "scoring_mismatch"


def test_large_scoring_mismatch_is_preserved_not_tuned_away():
    row = _row()
    row["usage_summary"]["receptions"] = 1
    row["production_summary"]["season_ppr"] = 3
    evidence = RECONCILE.evaluate_row(row, 0)
    assert evidence["derived_generic_ppr"] == "1.00"
    assert evidence["promoted_source_season_ppr"] == "3.00"
    assert evidence["signed_delta_derived_minus_source"] == "-2.00"
    assert evidence["reconciliation_status"] == "scoring_mismatch"
    assert "delta_not_attributable_from_promoted_component_set" in evidence[
        "reason_codes"
    ]


def test_week_18_is_valid_and_invalid_week_count_fails_closed():
    week_18 = _row()
    week_18["weeks_observed"] = 18
    evidence = RECONCILE.evaluate_row(week_18, 0)
    assert evidence["season_completeness"] == "full_season"
    assert evidence["week_scope"]["week_18_included"] is True
    assert evidence["week_scope"]["status"] == "declared_regular_season_aggregate"

    invalid = copy.deepcopy(week_18)
    invalid["weeks_observed"] = 19
    invalid_evidence = RECONCILE.evaluate_row(invalid, 0)
    assert invalid_evidence["season_completeness"] == "irreconcilable"
    assert (
        invalid_evidence["reconciliation_status"]
        == "regular_season_scope_unresolved"
    )
    assert "weeks_observed_outside_0_18" in invalid_evidence["reason_codes"]


def test_declared_completeness_conflict_is_irreconcilable():
    row = _row()
    row["weeks_observed"] = 1
    evidence = RECONCILE.evaluate_row(row, 0)
    assert evidence["season_completeness"] == "irreconcilable"
    assert (
        "coverage_status_conflicts_with_weeks_observed"
        in evidence["reason_codes"]
    )


def test_exact_source_and_manifest_bytes_are_pinned_and_unmodified():
    assert RECONCILE.sha256_path(RECONCILE.SOURCE_PATH) == RECONCILE.SOURCE_SHA256
    assert (
        RECONCILE.sha256_path(RECONCILE.SOURCE_MANIFEST_PATH)
        == RECONCILE.SOURCE_MANIFEST_SHA256
    )
    manifest = json.loads(RECONCILE.SOURCE_MANIFEST_PATH.read_text())
    assert manifest["promoted_artifact_sha256"] == RECONCILE.SOURCE_SHA256


def test_population_reconciliation_covers_every_source_row():
    artifact = _artifact(RECONCILE.build_outputs())
    rows = artifact["records"]
    assert len(rows) == 3016
    assert artifact["summaries"]["row_count"] == 3016
    assert sum(artifact["summaries"]["reconciliation_status_counts"].values()) == 3016
    assert sum(artifact["summaries"]["season_completeness_counts"].values()) == 3016
    assert all(
        row["reconciliation_status"] in RECONCILE.RECONCILIATION_STATES
        for row in rows
    )
    assert all(
        row["season_completeness"] in RECONCILE.COMPLETENESS_STATES
        for row in rows
    )
    assert (
        len(
            {
                (
                    row["source_row_key"]["player_id"],
                    row["source_row_key"]["season"],
                    row["source_row_key"]["season_type"],
                )
                for row in rows
            }
        )
        == 3016
    )


def test_population_counts_and_discrepancy_distribution_are_exact():
    artifact = _artifact(RECONCILE.build_outputs())
    summary = artifact["summaries"]
    assert summary["reconciliation_status_counts"] == {
        "reconciled_exact": 2186,
        "scoring_mismatch": 830,
    }
    assert summary["source_total_conforming_rows"] == 2186
    assert summary["source_total_conformance_rate"] == "72.48%"
    assert summary["source_total_mismatch_rate"] == "27.52%"
    assert summary["mismatch_delta"] == {
        "signed_min": "-12.00",
        "signed_max": "14.00",
        "integer_multiple_of_two_count": 830,
        "evaluated_mismatch_count": 830,
    }
    assert {
        season: values["source_total_mismatch_rows"]
        for season, values in summary["by_season"].items()
    } == {
        "2021": 168,
        "2022": 165,
        "2023": 177,
        "2024": 160,
        "2025": 160,
    }


def test_every_profile_component_and_source_total_is_available():
    artifact = _artifact(RECONCILE.build_outputs())
    summary = artifact["summaries"]
    assert set(summary["component_missing_counts"].values()) == {0}
    assert summary["source_total_missing_count"] == 0
    assert artifact["usability"] == {
        "candidate_generic_ppr_component_evidence": "usable",
        "promoted_source_total_profile_identity": "partially_supported_not_equivalent",
        "required_downstream_action": (
            "Forecast/operator must separately decide whether to admit the "
            "component-derived target; this evidence grants no admission."
        ),
    }


def test_output_bundle_is_byte_deterministic_and_committed_outputs_are_current():
    first = RECONCILE.build_outputs()
    second = RECONCILE.build_outputs()
    assert first == second
    assert RECONCILE._check_outputs(first) == []


def test_evidence_manifest_hashes_every_non_manifest_output():
    outputs = RECONCILE.build_outputs()
    manifest = json.loads(outputs[RECONCILE.EVIDENCE_MANIFEST_PATH])
    declared = {item["path"]: item for item in manifest["outputs"]}
    expected_paths = {
        str(path.relative_to(REPO_ROOT))
        for path in outputs
        if path != RECONCILE.EVIDENCE_MANIFEST_PATH
    }
    assert set(declared) == expected_paths
    for path, content in outputs.items():
        if path == RECONCILE.EVIDENCE_MANIFEST_PATH:
            continue
        item = declared[str(path.relative_to(REPO_ROOT))]
        assert item["sha256"] == hashlib.sha256(content).hexdigest()
        assert item["bytes"] == len(content)


def test_source_semantics_pin_is_corroboration_not_historical_release_claim():
    semantics = RECONCILE._source_semantics()
    corroboration = semantics["semantic_corroboration"]
    assert corroboration["commit"] == "0489133d85c5f11682572d9436c4a7b371a789aa"
    assert corroboration["blob_sha"] == "c54e875f9898ef9a4bbd5e7dd879c6e3c2abbc0a"
    assert "not claimed as the exact historical" in corroboration["provenance_limit"]
    assert "special_teams_touchdowns" in corroboration[
        "observed_formula_families_outside_candidate_profile"
    ]


def test_terminal_decision_is_ready_without_forecast_authorization():
    artifact = _artifact(RECONCILE.build_outputs())
    assert artifact["terminal_decision"] == "scoring_reconciliation_evidence_ready"
    manifest = json.loads(
        RECONCILE.build_outputs()[RECONCILE.EVIDENCE_MANIFEST_PATH]
    )
    assert manifest["invariants"]["source_bytes_modified"] is False
    assert manifest["invariants"]["forecast_authorized"] is False
    assert manifest["invariants"]["promotion_attempted"] is False
