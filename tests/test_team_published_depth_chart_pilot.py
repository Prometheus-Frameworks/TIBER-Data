import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_team_published_depth_chart_pilot.py"
SPEC = importlib.util.spec_from_file_location("depth_chart_pilot_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _snapshot_fixture(
    *, date: str | None = "2026-08-02", archive_status: str = "stored_immutable"
) -> dict:
    receipt_path = (
        "data/raw/depth_charts/test-only/source.html"
        if archive_status == "stored_immutable"
        else None
    )
    return {
        "artifact_type": "team_published_depth_chart_snapshot",
        "contract_version": "team_published_depth_chart_snapshot_v0",
        "snapshot_id": "test-only-ari-2026-08-02",
        "assertion_scope": "team_published_depth_chart_as_of",
        "team_id": "ARI",
        "team_abbr": "ARI",
        "season": 2026,
        "phase": "preseason",
        "chart_as_of": date,
        "published_at": "2026-08-02T17:51:47Z" if date else None,
        "observed_at": "2026-08-10T15:01:41Z",
        "publisher": "test-only official-team fixture",
        "publishing_department": None,
        "source_assertion_label_raw": "unofficial",
        "canonical_source_url": "https://www.azcardinals.com/test-only",
        "source_receipts": [
            {
                "receipt_id": "test-only-receipt",
                "role": "publication",
                "source_url": "https://www.azcardinals.com/test-only",
                "observed_at": "2026-08-10T15:01:41Z",
                "mime_type": "text/html",
                "byte_length": 10,
                "sha256": "0" * 64,
                "etag": None,
                "last_modified": None,
                "archive_status": archive_status,
                "immutable_receipt_path": receipt_path,
            }
        ],
        "transcription": {
            "method": "official_html_table",
            "version": "test-only-v0",
            "transcriber": "test-only",
            "source_row_count": 1,
            "normalized_row_count": 1,
            "source_entry_count": 1,
            "normalized_entry_count": 1,
        },
        "normalization_status": "complete",
        "verification_status": "candidate_structurally_validated",
        "previous_snapshot_id": None,
        "supersedes_snapshot_id": None,
        "validation_warnings": [],
        "reviewed_at": "2026-08-10T15:01:41Z",
        "rows": [
            {
                "unit": "offense",
                "row_instance_id": "offense-wr-01",
                "source_position_label_raw": "WR",
                "normalized_position": "WR",
                "source_row_reference": "test-only:row:1",
                "entries": [
                    {
                        "display_column": 1,
                        "display_order_within_column": 1,
                        "alternative_group_id": None,
                        "jersey_number": 0,
                        "raw_player_name": "Test Only Player",
                        "raw_source_text": "0 Test Only Player",
                        "raw_markers": ["bracketed"],
                        "decoded_marker_meanings": [],
                        "player_id": None,
                        "identity_status": "unresolved_not_attempted",
                        "identity_resolution_method": None,
                    }
                ],
            }
        ],
    }


def test_candidate_registry_and_receipt_ledger_validate() -> None:
    report = validator.validate_pilot_files()
    assert report["registry_team_count"] == 32
    assert report["observation_receipt_count"] == 6
    assert report["format_probe_count"] == 4
    assert report["normalized_candidate_count"] == 0
    assert report["terminal_decision"].endswith("followup")


def test_registry_contains_explicit_missing_and_unchecked_states() -> None:
    registry = _load("data/candidate/depth_charts/official_source_registry_v0.json")
    by_team = {team["team_id"]: team for team in registry["teams"]}
    assert by_team["BUF"]["coverage_state"] == "not_yet_published"
    assert by_team["BUF"]["last_checked_at"] is not None
    assert by_team["BAL"]["coverage_state"] == "monitoring_degraded"
    assert by_team["BAL"]["last_checked_at"] is None


def test_official_allowlist_rejects_third_party_and_insecure_urls() -> None:
    assert validator.official_source_allowed("https://www.commanders.com/team/depth-chart")
    assert validator.official_source_allowed("https://static.clubs.nfl.com/image/upload/example.jpg")
    assert not validator.official_source_allowed("https://www.espn.com/nfl/depth")
    assert not validator.official_source_allowed("http://www.azcardinals.com/team/depth-chart")
    assert not validator.official_source_allowed("https://azcardinals.com.example.net/chart")


def test_snapshot_schema_retains_unresolved_identity_and_raw_markers() -> None:
    snapshot = _snapshot_fixture()
    validator.validate_snapshot(snapshot)
    entry = snapshot["rows"][0]["entries"][0]
    assert entry["player_id"] is None
    assert entry["identity_status"] == "unresolved_not_attempted"
    assert entry["raw_markers"] == ["bracketed"]
    assert entry["decoded_marker_meanings"] == []


def test_snapshot_schema_rejects_dropped_identity_state() -> None:
    snapshot = _snapshot_fixture()
    del snapshot["rows"][0]["entries"][0]["player_id"]
    with pytest.raises(ValidationError):
        validator.validate_snapshot(snapshot)


def test_snapshot_validator_rejects_unresolved_identity_with_fake_id() -> None:
    snapshot = _snapshot_fixture()
    snapshot["rows"][0]["entries"][0]["player_id"] = "invented-id"
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot)


def test_rights_blocked_or_undated_candidate_cannot_advance_latest() -> None:
    prior = _snapshot_fixture(date="2026-08-02")
    prior["snapshot_id"] = "prior"

    blocked = _snapshot_fixture(date="2026-08-10", archive_status="blocked_rights_unresolved")
    blocked["snapshot_id"] = "blocked"
    blocked["normalization_status"] = "quarantined"
    blocked["verification_status"] = "blocked_rights_unresolved"
    blocked["reviewed_at"] = None
    assert validator.advance_latest(prior, blocked)["snapshot_id"] == "prior"

    undated = _snapshot_fixture(date=None)
    undated["snapshot_id"] = "undated"
    undated["verification_status"] = "candidate_undated_source"
    assert validator.advance_latest(prior, undated)["snapshot_id"] == "prior"


def test_newer_rights_cleared_candidate_advances_but_stale_does_not() -> None:
    prior = _snapshot_fixture(date="2026-08-02")
    prior["snapshot_id"] = "prior"
    newer = _snapshot_fixture(date="2026-08-10")
    newer["snapshot_id"] = "newer"
    assert validator.advance_latest(prior, newer)["snapshot_id"] == "newer"

    stale = _snapshot_fixture(date="2026-08-01")
    stale["snapshot_id"] = "stale"
    assert validator.advance_latest(prior, stale)["snapshot_id"] == "prior"


def test_deterministic_diff_is_empty_for_identical_snapshot() -> None:
    snapshot = _snapshot_fixture()
    assert validator.deterministic_snapshot_diff(snapshot, deepcopy(snapshot)) == {
        "added": [],
        "removed": [],
        "changed": [],
    }


def test_deterministic_diff_orders_added_records_by_semantic_key() -> None:
    before = _snapshot_fixture()
    after = deepcopy(before)
    template = deepcopy(after["rows"][0]["entries"][0])
    second = deepcopy(template)
    second.update(
        {
            "display_column": 3,
            "raw_player_name": "Test Only Player C",
            "raw_source_text": "0 Test Only Player C",
        }
    )
    first = deepcopy(template)
    first.update(
        {
            "display_column": 2,
            "raw_player_name": "Test Only Player B",
            "raw_source_text": "0 Test Only Player B",
        }
    )
    after["rows"][0]["entries"].extend([second, first])
    after["transcription"]["normalized_entry_count"] = 3
    diff = validator.deterministic_snapshot_diff(before, after)
    assert [record["key"][2] for record in diff["added"]] == [2, 3]


def test_audit_records_exact_format_probe_counts_without_candidate_claim() -> None:
    audit = _load("docs/audits/official-depth-chart-pilot-readiness-2026-08-10.json")
    by_team = {result["team_abbr"]: result for result in audit["format_probe_results"]}
    assert (by_team["ARI"]["source_row_count"], by_team["ARI"]["source_entry_count"]) == (29, 100)
    assert (by_team["WAS"]["source_row_count"], by_team["WAS"]["source_entry_count"]) == (30, 103)
    assert (by_team["PIT"]["source_row_count"], by_team["PIT"]["source_entry_count"]) == (30, 92)
    assert (by_team["CAR"]["source_row_count"], by_team["CAR"]["source_entry_count"]) == (28, 89)
    assert all(not result["normalization_output_committed"] for result in by_team.values())
