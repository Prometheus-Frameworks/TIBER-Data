from __future__ import annotations

import copy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "promote_team_week_raw_v0_2024_candidate.py"
    )
    spec = spec_from_file_location("promote_team_week_raw_v0_2024_candidate", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return _load_module()


def _candidate():
    return {
        "artifact": "team_week_raw_v0",
        "generatedAt": "2026-06-25T19:20:51+00:00",
        "season": 2024,
        "sourceArtifacts": ["nflverse-data:pbp/play_by_play_2024"],
        "metadata": {
            "provenanceStatus": "partial_real_data",
            "provenanceNotes": [
                "provenanceStatus is partial_real_data: pressureRateAllowed is deferred-null.",
                "No governance marker is set by this build. governanceStatus is 'ungoverned'.",
                "Team code 'LA' is canonicalized to 'LAR'.",
            ],
            "inputSources": [
                {
                    "source": "https://example.invalid/pbp_2024.parquet",
                    "sourceType": "nflverse",
                    "checksum": {"algorithm": "sha256", "value": "a" * 64},
                }
            ],
            "coverage": {
                "season": 2024,
                "expectedTeams": ["KC", "BAL"],
                "presentTeams": ["KC", "BAL"],
                "missingTeams": [],
                "unexpectedTeams": [],
                "weeks": [1],
                "expectedWeeks": [1],
                "isFullLeague": True,
                "isFullRegularSeasonCalendar": True,
                "expectedTeamGameRows": 2,
                "actualTeamGameRows": 2,
                "byeWeeksHandled": True,
            },
            "governance": {
                "governanceStatus": "ungoverned",
                "governanceSource": "not_set",
                "notes": "No human promotion review has been performed.",
            },
            "deferredFields": ["pressureRateAllowed"],
            "deferredFieldReasons": {"pressureRateAllowed": "no governed source"},
            "fieldReadiness": {"pressureRateAllowed": "deferred", "redZoneTdRate": "partial_nulls"},
            "validationReportPath": "exports/.../candidate.validation.json",
            "lineageManifestPath": "data/manifests/candidate.manifest.json",
        },
        "rows": [
            {"season": 2024, "week": 1, "teamCode": "KC", "opponentCode": "BAL",
             "pressureRateAllowed": None, "redZoneTdRate": None},
            {"season": 2024, "week": 1, "teamCode": "BAL", "opponentCode": "KC",
             "pressureRateAllowed": None, "redZoneTdRate": 0.5},
        ],
    }


def _validation_report():
    return {
        "report": "team_week_raw_v0_2024_real_source_candidate_validation",
        "season": 2024,
        "rowCount": 2,
        "teamCount": 2,
        "allPassed": True,
        "checks": [
            {"name": "all_32_teams_present", "passed": True, "details": {}},
            {"name": "source_checksums_present", "passed": True, "details": {}},
            {"name": "pressure_field_readiness_deferred", "passed": True, "details": {}},
            {"name": "non_governed_status", "passed": True,
             "details": {"provenanceStatus": "partial_real_data", "governanceStatus": "ungoverned"}},
        ],
    }


def _manifest():
    return {
        "artifact": "team_week_raw_v0_2024_real_source_candidate",
        "season": 2024,
        "sources": [{"sourceName": "nflverse play-by-play", "checksum": {"algorithm": "sha256", "value": "a" * 64}}],
        "governanceStatus": "ungoverned",
        "governanceSource": "not_set",
        "notes": ["No governed_real_data claim is made or implied by this manifest."],
    }


# --- verify_promotable ---

def test_verify_promotable_passes_for_good_candidate(mod):
    assert mod.verify_promotable(_candidate(), _validation_report()) == []


def test_verify_promotable_flags_nonnull_pressure(mod):
    art = _candidate()
    art["rows"][0]["pressureRateAllowed"] = 0.3
    issues = mod.verify_promotable(art, _validation_report())
    assert any("pressureRateAllowed is non-null" in i for i in issues)


def test_verify_promotable_flags_zero_filled_deferred_field(mod):
    art = _candidate()
    art["rows"][0]["pressureRateAllowed"] = 0  # zero-fill of a deferred field
    issues = mod.verify_promotable(art, _validation_report())
    assert any("deferred field" in i for i in issues)


def test_verify_promotable_flags_missing_checksum(mod):
    art = _candidate()
    del art["metadata"]["inputSources"][0]["checksum"]
    issues = mod.verify_promotable(art, _validation_report())
    assert any("missing a checksum" in i for i in issues)


def test_verify_promotable_flags_failed_data_check(mod):
    report = _validation_report()
    report["checks"][0]["passed"] = False
    issues = mod.verify_promotable(_candidate(), report)
    assert any("all_32_teams_present" in i for i in issues)


def test_verify_promotable_ignores_governance_checks(mod):
    # non_governed_status failing must NOT block (it is the pre-promotion check)
    report = _validation_report()
    report["checks"][-1]["passed"] = False
    assert mod.verify_promotable(_candidate(), report) == []


# --- promote_artifact ---

def test_promote_artifact_sets_explicit_marker_and_keeps_rows(mod):
    art = _candidate()
    before_rows = copy.deepcopy(art["rows"])
    promoted = mod.promote_artifact(art)
    assert promoted["metadata"]["provenanceStatus"] == "governed_real_data"
    gov = promoted["metadata"]["governance"]
    assert gov["governanceStatus"] == "governed"
    assert gov["governanceSource"] == "explicit_marker"
    assert "TIBER-Data#179" in gov["reviewRefs"]
    # rows (incl. pressure null) are untouched
    assert promoted["rows"] == before_rows
    # original artifact not mutated
    assert art["metadata"]["provenanceStatus"] == "partial_real_data"


def test_promote_artifact_drops_stale_nongoverned_notes(mod):
    promoted = mod.promote_artifact(_candidate())
    notes = promoted["metadata"]["provenanceNotes"]
    assert not any("No governance marker is set" in n for n in notes)
    assert not any("provenanceStatus is partial_real_data" in n for n in notes)
    # non-governance note is preserved; governance marker note is appended once
    assert any("LA" in n for n in notes)
    assert sum(1 for n in notes if n == mod.GOVERNANCE_MARKER_NOTE) == 1


def test_promote_artifact_is_idempotent(mod):
    once = mod.promote_artifact(_candidate())
    twice = mod.promote_artifact(once)
    assert once == twice


# --- promote_validation_report ---

def test_promote_validation_report_swaps_governance_check(mod):
    promoted_art = mod.promote_artifact(_candidate())
    report = mod.promote_validation_report(_validation_report(), promoted_art)
    names = [c["name"] for c in report["checks"]]
    assert "non_governed_status" not in names
    assert names.count("governance_marker_consistent") == 1
    assert report["allPassed"] is True
    assert report["promotion"]["decision"] == "governed_real_data"
    assert "TIBER-Data#179" in report["promotion"]["reviewRefs"]


def test_promote_validation_report_is_idempotent(mod):
    promoted_art = mod.promote_artifact(_candidate())
    once = mod.promote_validation_report(_validation_report(), promoted_art)
    twice = mod.promote_validation_report(once, promoted_art)
    assert [c["name"] for c in once["checks"]] == [c["name"] for c in twice["checks"]]
    assert twice["checks"].count  # sanity
    assert sum(1 for c in twice["checks"] if c["name"] == "governance_marker_consistent") == 1


# --- promote_manifest ---

def test_promote_manifest_records_explicit_marker(mod):
    man = mod.promote_manifest(_manifest())
    assert man["governanceStatus"] == "governed"
    assert man["governanceSource"] == "explicit_marker"
    assert man["promotion"]["decision"] == "governed_real_data"
    assert "TIBER-Data#179" in man["promotion"]["reviewRefs"]
