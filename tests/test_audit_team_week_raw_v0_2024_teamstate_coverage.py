"""Tests for the #181 governed Teamstate-source coverage audit.

These tests are dependency-free (no polars/nflverse) so the coverage proof is
runnable anywhere. They assert the audit verifies 32-team coverage, the 2024
team-game row count, no duplicate team-week rows, missing-team/week diagnostics,
field-level null counts, governance/source/validation/lineage refs, deterministic
ordering, and that no deferred field is zero-laundered.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "audit_team_week_raw_v0_2024_teamstate_coverage.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_twrv0_coverage", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = _load_module()
REPORT = AUDIT.run_audit()


def _check(name: str) -> dict:
    matches = [c for c in REPORT["checks"] if c["name"] == name]
    assert matches, f"missing check {name}"
    return matches[0]


def test_audit_overall_passes():
    assert REPORT["allPassed"] is True


def test_32_team_coverage():
    assert REPORT["teamCount"] == 32
    c = _check("all_32_nfl_teams_present")
    assert c["passed"] is True
    assert c["details"]["missingTeams"] == []
    assert c["details"]["unexpectedTeams"] == []


def test_expected_2024_team_game_row_count():
    assert REPORT["rowCount"] == 544
    assert _check("expected_team_game_row_count")["passed"] is True
    assert _check("every_team_has_17_played_games")["passed"] is True


def test_no_duplicate_team_week_rows():
    c = _check("no_duplicate_team_week_rows")
    assert c["passed"] is True
    assert c["details"]["duplicateKeys"] == []


def test_missing_team_week_diagnostics_present():
    # The audit must expose explicit missing-team accounting even when empty.
    details = _check("all_32_nfl_teams_present")["details"]
    assert "missingTeams" in details
    assert REPORT["coverageMetadata"]["missingTeams"] == []
    assert REPORT["weeksPresent"] == list(range(1, 19))


def test_field_level_null_counts_reported():
    null_report = REPORT["fieldNullReport"]
    # Offensive environment fields are fully populated.
    assert null_report["epaPerPlay"]["null"] == 0
    assert null_report["successRate"]["null"] == 0
    # redZoneTdRate carries legitimate partial nulls (zero-red-zone-trip rows).
    assert null_report["redZoneTdRate"]["null"] == 11
    assert null_report["redZoneTdRate"]["classification"] == "partial_nulls"
    # Deferred / absent fields are fully null and classified honestly.
    assert null_report["pressureRateAllowed"]["null"] == 544
    assert null_report["pressureRateAllowed"]["classification"] == "deferred"
    assert null_report["fantasyPointsForQB"]["null"] == 544


def test_no_fake_zero_for_deferred_fields():
    c = _check("deferred_fields_never_zero_filled")
    assert c["passed"] is True
    assert c["details"]["violations"] == []
    assert "pressureRateAllowed" in REPORT["deferredFields"]


def test_deterministic_ordering():
    assert _check("deterministic_ordering_week_then_teamcode")["passed"] is True


def test_governance_source_validation_lineage_refs_present():
    assert _check("explicit_governance_marker_agrees_with_provenance")["passed"] is True
    assert _check("source_refs_present")["passed"] is True
    assert _check("source_checksums_present")["passed"] is True
    assert _check("validation_refs_present_and_passing")["passed"] is True
    assert _check("lineage_refs_present")["passed"] is True
    assert _check("promotion_recorded")["passed"] is True
