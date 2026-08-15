import importlib.util
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_team_published_depth_chart_pilot.py"
SPEC = importlib.util.spec_from_file_location("depth_chart_pilot_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

DEFAULT_PUBLICATION = object()
SOURCE_BYTES = b"test-only official depth-chart bytes\n"
RECEIPT_PATH = "data/raw/depth_charts/test-only/source.html"


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _snapshot_fixture(
    receipt_root: Path,
    *,
    date: str | None = "2026-08-02",
    published_at: str | None | object = DEFAULT_PUBLICATION,
    archive_status: str = "stored_immutable",
    source_bytes: bytes = SOURCE_BYTES,
    receipt_name: str = "source.html",
) -> dict:
    if published_at is DEFAULT_PUBLICATION:
        published_at = "2026-08-02T17:51:47Z" if date else None
    receipt_path = (
        f"data/raw/depth_charts/test-only/{receipt_name}"
        if archive_status == "stored_immutable"
        else None
    )
    if receipt_path is not None:
        source_path = receipt_root / receipt_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(source_bytes)
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
        "published_at": published_at,
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
                "byte_length": len(source_bytes),
                "sha256": sha256(source_bytes).hexdigest(),
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
                        "decoded_marker_legend_reference": None,
                        "player_id": None,
                        "identity_status": "unresolved_not_attempted",
                        "identity_resolution_method": None,
                    }
                ],
            }
        ],
    }


def _advance(prior: dict | None, candidate: dict, receipt_root: Path) -> dict | None:
    return validator.advance_latest(prior, candidate, receipt_root=receipt_root)


def test_candidate_registry_receipts_and_explicit_manifest_validate() -> None:
    report = validator.validate_pilot_files()
    manifest = _load(
        "data/candidate/depth_charts/normalized_candidate_manifest_2026-08-10.json"
    )
    assert report["registry_team_count"] == 32
    assert report["observation_receipt_count"] == 6
    assert report["format_probe_count"] == 4
    assert report["normalized_candidate_count"] == len(manifest["candidate_snapshot_paths"])
    assert manifest["candidate_snapshot_paths"] == []
    assert report["terminal_decision"].endswith("followup")


def test_registry_contains_explicit_missing_and_unchecked_states() -> None:
    registry = _load("data/candidate/depth_charts/official_source_registry_v0.json")
    by_team = {team["team_id"]: team for team in registry["teams"]}
    assert by_team["BUF"]["coverage_state"] == "not_yet_published"
    assert by_team["BUF"]["last_checked_at"] is not None
    assert by_team["BAL"]["coverage_state"] == "monitoring_degraded"
    assert by_team["BAL"]["last_checked_at"] is None


def test_official_allowlist_and_team_coupling_reject_adversarial_hosts() -> None:
    assert validator.official_source_allowed("https://www.commanders.com/team/depth-chart")
    assert validator.official_source_allowed("https://static.clubs.nfl.com/image/upload/x.jpg")
    assert validator.official_source_allowed_for_team(
        "ARI", "https://static.clubs.nfl.com/image/upload/cardinals/chart.jpg"
    )
    assert not validator.official_source_allowed_for_team(
        "WAS", "https://static.clubs.nfl.com/image/upload/cardinals/chart.jpg"
    )
    assert not validator.official_source_allowed_for_team(
        "ARI", "https://static.clubs.nfl.com/image/upload/commanders/chart.jpg"
    )
    assert not validator.official_source_allowed_for_team(
        "ARI", "https://www.commanders.com/team/depth-chart"
    )
    assert not validator.official_source_allowed("https://www.espn.com/nfl/depth")
    assert not validator.official_source_allowed("http://www.azcardinals.com/team/depth-chart")
    assert not validator.official_source_allowed("https://azcardinals.com.example.net/chart")
    assert not validator.official_source_allowed("https://commanders.com@azcardinals.com/chart")
    assert not validator.official_source_allowed("https://azcardinals.com:444/chart")
    assert not validator.official_source_allowed_for_team(
        "ARI", "https://static.clubs.nfl.com/image/upload/cardinals/../other/chart.jpg"
    )


def test_registry_rejects_globally_official_but_wrong_team_host() -> None:
    registry = _load("data/candidate/depth_charts/official_source_registry_v0.json")
    registry["teams"][0]["official_depth_chart_page_candidate"] = (
        "https://www.commanders.com/team/depth-chart"
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_registry(registry)


@pytest.mark.parametrize(
    ("field", "bad_url"),
    [
        ("canonical", "https://www.commanders.com/team/depth-chart"),
        ("receipt", "https://www.espn.com/nfl/depth-chart"),
        ("receipt", "https://www.commanders.com/team/depth-chart"),
    ],
)
def test_snapshot_rejects_third_party_or_wrong_team_urls(
    tmp_path: Path, field: str, bad_url: str
) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    if field == "canonical":
        snapshot["canonical_source_url"] = bad_url
    else:
        snapshot["source_receipts"][0]["source_url"] = bad_url
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_snapshot_requires_exact_canonical_receipt(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["canonical_source_url"] = "https://www.azcardinals.com/another-official-page"
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_snapshot_rejects_team_id_drift(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["team_id"] = "WAS"
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_snapshot_schema_retains_unresolved_identity_and_raw_markers(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    assert entry["player_id"] is None
    assert entry["identity_status"] == "unresolved_not_attempted"
    assert entry["raw_markers"] == ["bracketed"]
    assert entry["decoded_marker_meanings"] == []
    assert entry["decoded_marker_legend_reference"] is None


def test_snapshot_schema_rejects_dropped_identity_state(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    del snapshot["rows"][0]["entries"][0]["player_id"]
    with pytest.raises(ValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_snapshot_validator_rejects_unresolved_identity_with_fake_id(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["rows"][0]["entries"][0]["player_id"] = "invented-id"
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_snapshot_rejects_ambiguous_identity_with_chosen_id(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    entry["identity_status"] = "ambiguous_multiple_matches"
    entry["player_id"] = "chosen-despite-ambiguity"
    entry["identity_resolution_method"] = "test-only alias candidates"
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_snapshot_rejects_resolved_identity_without_explicit_method(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    entry["identity_status"] = "resolved_exact"
    entry["player_id"] = "canonical-test-player"
    entry["identity_resolution_method"] = None
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_v0_rejects_decoded_marker_meaning_without_binding(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    entry["decoded_marker_meanings"] = ["test-only meaning"]
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_v0_rejects_even_apparently_official_legend_decoding(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    entry["decoded_marker_meanings"] = ["test-only meaning"]
    entry["decoded_marker_legend_reference"] = {
        "receipt_id": "test-only-receipt",
        "source_url": "https://www.azcardinals.com/test-only",
        "source_locator": "test-only legend block",
        "legend_text_raw": "Test-only exact legend text",
    }
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_v0_rejects_unused_or_fabricated_legend_binding(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    entry = snapshot["rows"][0]["entries"][0]
    entry["decoded_marker_legend_reference"] = {
        "receipt_id": "test-only-receipt",
        "source_url": "https://www.azcardinals.com/test-only",
        "source_locator": "test-only legend block",
        "legend_text_raw": "Test-only exact legend text",
    }
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_decoded_legend_cannot_rely_on_rights_blocked_hash_only_receipt(
    tmp_path: Path,
) -> None:
    snapshot = _snapshot_fixture(tmp_path, archive_status="blocked_rights_unresolved")
    snapshot["normalization_status"] = "quarantined"
    snapshot["verification_status"] = "blocked_rights_unresolved"
    snapshot["reviewed_at"] = None
    entry = snapshot["rows"][0]["entries"][0]
    entry["decoded_marker_meanings"] = ["test-only meaning"]
    entry["decoded_marker_legend_reference"] = {
        "receipt_id": "test-only-receipt",
        "source_url": "https://www.azcardinals.com/test-only",
        "source_locator": "test-only legend block",
        "legend_text_raw": "Test-only exact legend text",
    }
    with pytest.raises((ValidationError, validator.PilotValidationError)):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_complete_candidate_requires_nonempty_structural_evidence(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["rows"] = []
    snapshot["transcription"].update(
        {
            "source_row_count": 0,
            "normalized_row_count": 0,
            "source_entry_count": 0,
            "normalized_entry_count": 0,
        }
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_complete_candidate_rejects_zero_source_counts(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["transcription"]["source_entry_count"] = 0
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_complete_candidate_rejects_dropped_source_row_and_cannot_advance(
    tmp_path: Path,
) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    dropped = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        source_bytes=b"dropped-row candidate bytes\n",
        receipt_name="dropped-row.html",
    )
    dropped["snapshot_id"] = "dropped-row"
    dropped["transcription"]["source_row_count"] = 2
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(dropped, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(dropped, receipt_root=tmp_path)
    assert _advance(prior, dropped, tmp_path)["snapshot_id"] == "prior"


def test_complete_candidate_rejects_dropped_source_entry_and_cannot_advance(
    tmp_path: Path,
) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    dropped = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        source_bytes=b"dropped-entry candidate bytes\n",
        receipt_name="dropped-entry.html",
    )
    dropped["snapshot_id"] = "dropped-entry"
    dropped["transcription"]["source_entry_count"] = 2
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(dropped, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(dropped, receipt_root=tmp_path)
    assert _advance(prior, dropped, tmp_path)["snapshot_id"] == "prior"


def test_lossy_reconciliation_must_remain_partial_and_cannot_advance(tmp_path: Path) -> None:
    partial = _snapshot_fixture(tmp_path)
    partial["normalization_status"] = "partial"
    partial["verification_status"] = "candidate_unreviewed"
    partial["reviewed_at"] = None
    partial["transcription"]["source_entry_count"] = 2
    validator.validate_snapshot(partial, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(partial, receipt_root=tmp_path)


def test_complete_candidate_cannot_rely_on_hash_only_receipt(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path, archive_status="remote_hash_pinned")
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_candidate_helpers_full_validate_and_fail_closed(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    invalid = _snapshot_fixture(tmp_path, date="2026-08-10")
    invalid["snapshot_id"] = "invalid"
    del invalid["canonical_source_url"]
    assert not validator.candidate_can_advance(invalid, receipt_root=tmp_path)
    assert _advance(prior, invalid, tmp_path)["snapshot_id"] == "prior"


def test_stored_immutable_receipt_must_exist(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    (tmp_path / RECEIPT_PATH).unlink()
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)
    assert not validator.candidate_can_advance(snapshot, receipt_root=tmp_path)


def test_stored_immutable_receipt_byte_length_and_hash_are_recomputed(tmp_path: Path) -> None:
    wrong_length = _snapshot_fixture(tmp_path)
    wrong_length["source_receipts"][0]["byte_length"] += 1
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(wrong_length, receipt_root=tmp_path)

    wrong_hash = _snapshot_fixture(tmp_path)
    wrong_hash["source_receipts"][0]["sha256"] = "0" * 64
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(wrong_hash, receipt_root=tmp_path)


def test_immutable_receipt_path_cannot_escape_repository_root(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    snapshot["source_receipts"][0]["immutable_receipt_path"] = (
        "data/raw/depth_charts/../../outside.html"
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


def test_rights_blocked_or_undated_candidate_cannot_advance_latest(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path, date="2026-08-02")
    prior["snapshot_id"] = "prior"

    blocked = _snapshot_fixture(
        tmp_path, date="2026-08-10", archive_status="blocked_rights_unresolved"
    )
    blocked["snapshot_id"] = "blocked"
    blocked["normalization_status"] = "quarantined"
    blocked["verification_status"] = "blocked_rights_unresolved"
    blocked["reviewed_at"] = None
    assert _advance(prior, blocked, tmp_path)["snapshot_id"] == "prior"

    undated = _snapshot_fixture(tmp_path, date=None)
    undated["snapshot_id"] = "undated"
    undated["verification_status"] = "candidate_undated_source"
    assert _advance(prior, undated, tmp_path)["snapshot_id"] == "prior"


def test_newer_rights_cleared_candidate_advances_but_stale_does_not(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path, date="2026-08-02")
    prior["snapshot_id"] = "prior"
    newer = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        published_at="2026-08-10T11:00:00Z",
        source_bytes=b"newer official bytes\n",
        receipt_name="newer.html",
    )
    newer["snapshot_id"] = "newer"
    assert _advance(prior, newer, tmp_path)["snapshot_id"] == "newer"

    stale = _snapshot_fixture(
        tmp_path,
        date="2026-08-01",
        published_at="2026-08-11T23:59:59Z",
        source_bytes=b"stale official bytes\n",
        receipt_name="stale.html",
    )
    stale["snapshot_id"] = "stale"
    assert _advance(prior, stale, tmp_path)["snapshot_id"] == "prior"


def test_unchanged_evidence_hash_never_advances_on_newer_metadata(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path, date="2026-08-02")
    prior["snapshot_id"] = "prior"
    metadata_only = _snapshot_fixture(
        tmp_path, date="2026-08-10", published_at="2026-08-10T18:00:00Z"
    )
    metadata_only["snapshot_id"] = "metadata-only"
    assert _advance(prior, metadata_only, tmp_path)["snapshot_id"] == "prior"


@pytest.mark.parametrize("drift_field", ["team", "season"])
def test_latest_replacement_cannot_cross_snapshot_stream(
    tmp_path: Path, drift_field: str
) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    candidate = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        source_bytes=b"different stream bytes\n",
        receipt_name=f"different-{drift_field}.html",
    )
    candidate["snapshot_id"] = "different-stream"
    if drift_field == "team":
        candidate["team_id"] = "WAS"
        candidate["team_abbr"] = "WAS"
        candidate["canonical_source_url"] = "https://www.commanders.com/test-only"
        candidate["source_receipts"][0]["source_url"] = (
            "https://www.commanders.com/test-only"
        )
    else:
        candidate["season"] = 2027
    assert validator.candidate_can_advance(candidate, receipt_root=tmp_path)
    assert _advance(prior, candidate, tmp_path)["snapshot_id"] == "prior"


def test_null_chart_date_cannot_advance_even_with_later_publication_clock(
    tmp_path: Path,
) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    undated = _snapshot_fixture(
        tmp_path,
        date=None,
        published_at="2026-08-10T18:00:00Z",
        source_bytes=b"undated published bytes\n",
        receipt_name="undated-published.html",
    )
    undated["snapshot_id"] = "undated-published"
    assert not validator.candidate_can_advance(undated, receipt_root=tmp_path)
    assert _advance(prior, undated, tmp_path)["snapshot_id"] == "prior"


def test_same_chart_date_uses_full_timezone_aware_publication_clock(tmp_path: Path) -> None:
    prior = _snapshot_fixture(
        tmp_path, date="2026-08-02", published_at="2026-08-02T17:30:00Z"
    )
    prior["snapshot_id"] = "prior"
    later = _snapshot_fixture(
        tmp_path,
        date="2026-08-02",
        published_at="2026-08-02T18:00:00Z",
        source_bytes=b"later publication bytes\n",
        receipt_name="later.html",
    )
    later["snapshot_id"] = "later"
    assert _advance(prior, later, tmp_path)["snapshot_id"] == "later"

    same_instant = _snapshot_fixture(
        tmp_path,
        date="2026-08-02",
        published_at="2026-08-02T19:30:00+02:00",
        source_bytes=b"same instant bytes\n",
        receipt_name="same-instant.html",
    )
    same_instant["snapshot_id"] = "same-instant"
    assert _advance(prior, same_instant, tmp_path)["snapshot_id"] == "prior"


def test_observation_clock_never_selects_latest(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    candidate = _snapshot_fixture(
        tmp_path,
        source_bytes=b"observation-only change bytes\n",
        receipt_name="observation-only.html",
    )
    candidate["snapshot_id"] = "candidate"
    candidate["observed_at"] = "2026-12-31T23:59:59Z"
    candidate["source_receipts"][0]["observed_at"] = "2026-12-31T23:59:59Z"
    assert _advance(prior, candidate, tmp_path)["snapshot_id"] == "prior"


def test_invalid_prior_is_retained_instead_of_silently_replaced(tmp_path: Path) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    prior["canonical_source_url"] = "https://www.commanders.com/team/depth-chart"
    candidate = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        source_bytes=b"candidate bytes\n",
        receipt_name="candidate.html",
    )
    candidate["snapshot_id"] = "candidate"
    assert _advance(prior, candidate, tmp_path)["snapshot_id"] == "prior"


def test_hash_run_classification_never_auto_advances() -> None:
    old_hash = "0" * 64
    new_hash = "1" * 64
    assert (
        validator.classify_source_hash_run(old_hash, old_hash)
        == "stable_observation_only_no_snapshot_no_health_claim"
    )
    assert (
        validator.classify_source_hash_run(
            old_hash, new_hash, changed_candidate_parse_succeeded=False
        )
        == "changed_hash_parse_quarantined_no_advance"
    )
    assert (
        validator.classify_source_hash_run(
            old_hash, new_hash, changed_candidate_parse_succeeded=True
        )
        == "changed_hash_requires_full_validation_no_advance"
    )
    assert (
        validator.classify_source_hash_run(old_hash, new_hash)
        == "changed_hash_pending_parse_no_advance"
    )
    assert validator.classify_source_hash_run(old_hash, None) == "monitor_degraded_no_advance"
    with pytest.raises(validator.PilotValidationError):
        validator.classify_source_hash_run("not-a-hash", old_hash)


def test_observation_ledger_narrows_same_probe_hash_claim() -> None:
    ledger = _load(
        "data/candidate/depth_charts/source_observation_receipts_2026-08-10.json"
    )
    validator.validate_receipts(ledger)
    assert ledger["comparison_scope"]["independent_monitor_run"] is False
    assert ledger["comparison_scope"]["comparison_run_id_recorded"] is False
    assert ledger["comparison_scope"]["comparison_clock_recorded"] is False
    assert all(
        receipt["same_probe_disposition"] == "same_probe_hash_stable_no_snapshot"
        for receipt in ledger["receipts"]
    )


def test_observation_ledger_rejects_team_host_mismatch() -> None:
    ledger = _load(
        "data/candidate/depth_charts/source_observation_receipts_2026-08-10.json"
    )
    ledger["receipts"][0]["team_abbr"] = "WAS"
    with pytest.raises(validator.PilotValidationError):
        validator.validate_receipts(ledger)


def test_candidate_manifest_rejects_unlisted_file(tmp_path: Path) -> None:
    manifest = _load(
        "data/candidate/depth_charts/normalized_candidate_manifest_2026-08-10.json"
    )
    audit = _load("docs/audits/official-depth-chart-pilot-readiness-2026-08-10.json")
    candidate_directory = tmp_path / manifest["candidate_root"]
    candidate_directory.mkdir(parents=True)
    (candidate_directory / "unlisted.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(validator.PilotValidationError):
        validator.validate_candidate_manifest(manifest, audit, repository_root=tmp_path)


def test_deterministic_diff_is_empty_for_identical_snapshot(tmp_path: Path) -> None:
    snapshot = _snapshot_fixture(tmp_path)
    assert validator.deterministic_snapshot_diff(snapshot, deepcopy(snapshot)) == {
        "added": [],
        "removed": [],
        "changed": [],
    }


def test_deterministic_diff_orders_added_records_by_semantic_key(tmp_path: Path) -> None:
    before = _snapshot_fixture(tmp_path)
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
    assert (by_team["ARI"]["source_row_count"], by_team["ARI"]["source_entry_count"]) == (
        29,
        100,
    )
    assert (by_team["WAS"]["source_row_count"], by_team["WAS"]["source_entry_count"]) == (
        30,
        103,
    )
    assert (by_team["PIT"]["source_row_count"], by_team["PIT"]["source_entry_count"]) == (
        30,
        92,
    )
    assert (by_team["CAR"]["source_row_count"], by_team["CAR"]["source_entry_count"]) == (
        28,
        89,
    )
    assert all(not result["normalization_output_committed"] for result in by_team.values())


REGISTRY_PATH = "data/candidate/depth_charts/official_source_registry_v0.json"

EVIDENCE_FREE_CURRENCY_CLAIM = {
    "latest_verified_snapshot_id": None,
    "latest_verified_snapshot_sha256": None,
    "last_qualifying_effective_date": None,
}


def _registry_with(team_id: str, **overrides: object) -> dict:
    registry = _load(REGISTRY_PATH)
    for team in registry["teams"]:
        if team["team_id"] == team_id:
            team.update(overrides)
            return registry
    raise AssertionError(f"Unknown registry team: {team_id}")


def _without_schema_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the Python invariants so the schema cannot mask a missing check."""

    class _AcceptAll:
        def validate(self, payload: dict) -> None:
            return None

    monkeypatch.setattr(validator, "schema_validator", lambda path: _AcceptAll())


@pytest.mark.parametrize(
    "coverage_state", ["captured_candidate", "verified_current", "superseded"]
)
def test_registry_schema_rejects_evidence_free_currency_claim(coverage_state: str) -> None:
    registry = _registry_with(
        "ARI", coverage_state=coverage_state, **EVIDENCE_FREE_CURRENCY_CLAIM
    )
    with pytest.raises(ValidationError):
        validator.schema_validator(validator.REGISTRY_SCHEMA).validate(registry)


@pytest.mark.parametrize(
    "coverage_state", ["captured_candidate", "verified_current", "superseded"]
)
def test_validator_rejects_evidence_free_currency_claim(
    monkeypatch: pytest.MonkeyPatch, coverage_state: str
) -> None:
    _without_schema_layer(monkeypatch)
    registry = _registry_with(
        "ARI", coverage_state=coverage_state, **EVIDENCE_FREE_CURRENCY_CLAIM
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_registry(registry)


def test_partial_snapshot_evidence_cannot_satisfy_a_currency_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _without_schema_layer(monkeypatch)
    registry = _registry_with(
        "ARI",
        coverage_state="verified_current",
        latest_verified_snapshot_id="ari-2026-08-02",
        latest_verified_snapshot_sha256=None,
        last_qualifying_effective_date=None,
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_registry(registry)


@pytest.mark.parametrize("monitor_status", ["manual_probe_healthy", "manual_probe_blocked"])
def test_registry_schema_rejects_observed_status_without_clock(monitor_status: str) -> None:
    registry = _registry_with(
        "ARI",
        monitor_status=monitor_status,
        coverage_state="official_source_discovered",
        last_checked_at=None,
    )
    with pytest.raises(ValidationError):
        validator.schema_validator(validator.REGISTRY_SCHEMA).validate(registry)


@pytest.mark.parametrize("monitor_status", ["manual_probe_healthy", "manual_probe_blocked"])
def test_validator_rejects_observed_status_without_clock(
    monkeypatch: pytest.MonkeyPatch, monitor_status: str
) -> None:
    _without_schema_layer(monkeypatch)
    registry = _registry_with(
        "ARI",
        monitor_status=monitor_status,
        coverage_state="official_source_discovered",
        last_checked_at=None,
    )
    with pytest.raises(validator.PilotValidationError):
        validator.validate_registry(registry)


def test_never_probed_teams_stay_clock_exempt() -> None:
    registry = _registry_with(
        "BAL",
        monitor_status="not_checked_in_bounded_pilot",
        coverage_state="monitoring_degraded",
        last_checked_at=None,
    )
    validator.validate_registry(registry)


def test_declared_datetime_formats_are_actually_enforced() -> None:
    checker = validator.pilot_format_checker()
    for declared_format in validator.REQUIRED_SCHEMA_FORMATS:
        assert declared_format in checker.checkers


@pytest.mark.parametrize(
    "malformed",
    ["2026-08-10T12:00:00", "not-a-timestamp", "2026-13-45T99:99:99Z", "2026-08-10"],
)
def test_malformed_observation_clock_is_rejected_at_schema_time(malformed: str) -> None:
    registry = _registry_with("ARI", last_checked_at=malformed)
    with pytest.raises(ValidationError):
        validator.schema_validator(validator.REGISTRY_SCHEMA).validate(registry)
    with pytest.raises(ValidationError):
        validator.validate_registry(registry)


@pytest.mark.parametrize(
    "malformed", ["2026-08-02T17:51:47", "not-a-timestamp", "2026-13-45T99:99:99Z"]
)
def test_malformed_publication_clock_is_rejected_at_schema_time(
    tmp_path: Path, malformed: str
) -> None:
    snapshot = _snapshot_fixture(tmp_path, published_at=malformed)
    with pytest.raises(ValidationError):
        validator.validate_snapshot(snapshot, receipt_root=tmp_path)


@pytest.mark.parametrize(
    "malformed", ["2026-08-02T17:51:47", "not-a-timestamp", "2026-13-45T99:99:99Z"]
)
def test_malformed_publication_clock_retains_prior_instead_of_raising(
    tmp_path: Path, malformed: str
) -> None:
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    candidate = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        published_at=malformed,
        source_bytes=b"malformed clock bytes\n",
        receipt_name="malformed-clock.html",
    )
    candidate["snapshot_id"] = "candidate"
    assert validator.candidate_can_advance(candidate, receipt_root=tmp_path) is False
    assert _advance(prior, candidate, tmp_path)["snapshot_id"] == "prior"


def test_schema_valid_but_unparseable_clock_still_retains_prior(tmp_path: Path) -> None:
    """Lowercase RFC3339 stays schema-valid, so retention must not depend on the parser."""
    lowercase_rfc3339 = "2026-08-10t17:51:47z"
    assert validator.pilot_format_checker().conforms(lowercase_rfc3339, "date-time")
    prior = _snapshot_fixture(tmp_path)
    prior["snapshot_id"] = "prior"
    candidate = _snapshot_fixture(
        tmp_path,
        date="2026-08-10",
        published_at=lowercase_rfc3339,
        source_bytes=b"lowercase clock bytes\n",
        receipt_name="lowercase-clock.html",
    )
    candidate["snapshot_id"] = "candidate"
    assert validator.candidate_can_advance(candidate, receipt_root=tmp_path) is False
    assert _advance(prior, candidate, tmp_path)["snapshot_id"] == "prior"
