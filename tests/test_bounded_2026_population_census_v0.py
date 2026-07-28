"""Tests for the bounded 2026 population census v0 candidate (TIBER-Data #227)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.build_bounded_2026_population_census_v0 import (
    DATA_SOURCE_PIN,
    ROOKIE_SOURCE_PIN,
    BuildFailure,
    SourcePin,
    build_artifact,
    canonical_json_bytes,
    serialize_artifact,
)
from scripts.validate_bounded_2026_population_census_v0 import validate_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_ARTIFACT = (
    REPO_ROOT / "exports/candidates/population_census/bounded_2026_population_census_v0.json"
)


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode()


def _historical_row(
    player_id: str | None,
    *,
    name: str = "Historical Player",
    team: str | None = "KC",
    observed_at: str = "2026-06-30T00:00:00Z",
    identity_confidence: str | None = None,
    season: int = 2025,
) -> dict:
    teams = [team] if team else []
    return {
        "player_id": player_id,
        "player_name": name,
        "position": "WR",
        "identity_confidence": (
            identity_confidence
            if identity_confidence is not None
            else ("source_verified" if player_id is not None else "unresolved")
        ),
        "season": season,
        "season_type": "REG",
        "teams": teams,
        "primary_team": team,
        "team_unknown": team is None,
        "observed_at": observed_at,
        "source_updated_at": None,
        "source_refs": [
            {
                "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                "source_url": None,
                "observed_at": observed_at,
                "source_updated_at": None,
            }
        ],
    }


def _rookie_row(
    player_id: str | None,
    *,
    name: str = "Rookie Player",
    outcome_status: str | None = "drafted",
    team: str | None = "BUF",
) -> dict:
    outcome_value = (
        {
            "status": outcome_status,
            "nfl_team": team,
            "draft_round": 2,
            "overall_pick": 40,
            "is_udfa": False,
            "source_status": "external_verified",
            "upstream_provenance_status": "source_verified",
        }
        if outcome_status is not None
        else None
    )
    return {
        "player_id": player_id,
        "player_name": name,
        "position": "WR",
        "school": "Example",
        "class_year": 2026,
        "draft_capital": {
            "value": None,
            "provenance": {
                "source_type": "unavailable",
                "source_name": None,
                "source_url": None,
                "last_verified_at": None,
            },
        },
        "age_at_entry": {
            "value": 21,
            "provenance": {
                "source_type": "measured_identity_fact",
                "source_name": "fixture identity source",
                "source_url": None,
                "last_verified_at": "2026-07-01",
            },
        },
        "athletic_testing": {
            "value": None,
            "provenance": {
                "source_type": "unavailable",
                "source_name": None,
                "source_url": None,
                "last_verified_at": None,
            },
        },
        "college_production": {
            "value": None,
            "provenance": {
                "source_type": "unavailable",
                "source_name": None,
                "source_url": None,
                "last_verified_at": None,
            },
        },
        "official_postdraft_outcome": {
            "value": outcome_value,
            "provenance": {
                "source_type": (
                    "official_draft_result" if outcome_value is not None else "unavailable"
                ),
                "source_name": "fixture draft source" if outcome_value else None,
                "source_url": "https://example.test/draft" if outcome_value else None,
                "last_verified_at": "2026-07-02" if outcome_value else None,
            },
        },
    }


def _source_inputs(
    historical_rows: list[dict] | None = None,
    rookie_rows: list[dict] | None = None,
) -> tuple[bytes, bytes, bytes, bytes, SourcePin, SourcePin]:
    historical_rows = historical_rows or [_historical_row("00-0000001")]
    rookie_rows = rookie_rows or [_rookie_row("wr-test-rookie")]
    data_payload = {
        "artifact_id": "player_season_coverage_v0",
        "spec_version": "player_season_coverage_v0_promoted_v1",
        "status": "promoted_governed_artifact",
        "generated_at": "2026-07-06T00:00:00Z",
        "records": historical_rows,
    }
    rookie_payload = {
        "artifact_type": "rookie_transition_profile",
        "schema_version": "rookie-transition-profile-v0.2.0",
        "season": 2026,
        "generated_at": "2026-07-10T12:00:00Z",
        "rows": rookie_rows,
    }
    data_raw = _json_bytes(data_payload)
    rookie_raw = _json_bytes(rookie_payload)
    data_governance_payload = {"promoted_artifact_sha256": hashlib.sha256(data_raw).hexdigest()}
    rookie_governance_payload = {
        "output_files": [
            {
                "path": "rookie.json",
                "sha256": hashlib.sha256(rookie_raw).hexdigest(),
            }
        ]
    }
    data_governance_raw = _json_bytes(data_governance_payload)
    rookie_governance_raw = _json_bytes(rookie_governance_payload)
    data_pin = SourcePin(
        source_artifact_key="fixture_data",
        repository="fixture/TIBER-Data",
        commit="1" * 40,
        path="data.json",
        sha256=hashlib.sha256(data_raw).hexdigest(),
        governance_path="data-manifest.json",
        governance_sha256=hashlib.sha256(data_governance_raw).hexdigest(),
        expected_included_rows=sum(row.get("season") == 2025 for row in historical_rows),
    )
    rookie_pin = SourcePin(
        source_artifact_key="fixture_rookies",
        repository="fixture/TIBER-Rookies",
        commit="2" * 40,
        path="rookie.json",
        sha256=hashlib.sha256(rookie_raw).hexdigest(),
        governance_path="rookie-manifest.json",
        governance_sha256=hashlib.sha256(rookie_governance_raw).hexdigest(),
        expected_included_rows=len(rookie_rows),
    )
    return (
        data_raw,
        data_governance_raw,
        rookie_raw,
        rookie_governance_raw,
        data_pin,
        rookie_pin,
    )


def _build(
    historical_rows: list[dict] | None = None,
    rookie_rows: list[dict] | None = None,
) -> dict:
    (
        data_raw,
        data_governance_raw,
        rookie_raw,
        rookie_governance_raw,
        data_pin,
        rookie_pin,
    ) = _source_inputs(historical_rows, rookie_rows)
    return build_artifact(
        data_raw=data_raw,
        data_governance_raw=data_governance_raw,
        rookie_raw=rookie_raw,
        rookie_governance_raw=rookie_governance_raw,
        data_pin=data_pin,
        rookie_pin=rookie_pin,
        generated_at="2026-07-27T14:00:00Z",
    )


def test_two_builds_are_byte_identical() -> None:
    first = serialize_artifact(_build())
    second = serialize_artifact(_build())
    assert first == second


def test_population_row_ids_are_stable_when_source_order_changes() -> None:
    history = [_historical_row("00-0000001"), _historical_row("00-0000002")]
    rookies = [_rookie_row("wr-one"), _rookie_row("wr-two")]
    forward = _build(history, rookies)
    reverse = _build(list(reversed(history)), list(reversed(rookies)))

    def source_id_to_population_id(payload: dict) -> dict[str, str]:
        return {
            row["source_identity_ref"]["source_player_id"]: row["population_row_id"]
            for row in payload["population_rows"]
        }

    assert source_id_to_population_id(forward) == source_id_to_population_id(reverse)


def test_filtered_historical_rows_keep_original_source_array_indices() -> None:
    data_records = [
        _historical_row("old-0", season=2024),
        _historical_row("keep-1", season=2025),
        _historical_row("old-2", season=2023),
        _historical_row("keep-3", season=2025),
    ]
    payload = _build(data_records, [_rookie_row("rookie-0")])
    row_indices = {
        row["source_identity_ref"]["source_player_id"]: row["source_identity_ref"][
            "source_row_index"
        ]
        for row in payload["population_rows"]
    }
    assert row_indices == {
        "keep-1": 1,
        "keep-3": 3,
        "rookie-0": 0,
    }
    row_hashes = {
        row["source_identity_ref"]["source_player_id"]: row["source_identity_ref"][
            "source_row_sha256"
        ]
        for row in payload["population_rows"]
    }
    assert row_hashes["keep-1"] == hashlib.sha256(canonical_json_bytes(data_records[1])).hexdigest()
    assert row_hashes["keep-3"] == hashlib.sha256(canonical_json_bytes(data_records[3])).hexdigest()
    source_descriptors = {
        source["source_artifact_key"]: source for source in payload["source_artifacts"]
    }
    assert source_descriptors["fixture_data"]["source_row_count"] == 4
    assert source_descriptors["fixture_data"]["included_row_count"] == 2


def test_duplicate_and_cross_source_id_reuse_ledgers_preserve_every_row() -> None:
    history = [
        _historical_row("shared-id", name="First"),
        _historical_row("shared-id", name="Second", team="LV"),
    ]
    rookies = [_rookie_row("shared-id")]
    payload = _build(history, rookies)
    reconciliation = payload["reconciliation"]

    assert payload["population_row_count"] == 3
    assert len({row["population_row_id"] for row in payload["population_rows"]}) == 3
    assert reconciliation["counts"]["duplicate_source_id_groups"] == 1
    assert reconciliation["counts"]["duplicate_resolved_canonical_id_groups"] == 1
    assert reconciliation["counts"]["cross_source_canonical_identity_collision_groups"] is None
    assert reconciliation["counts"]["cross_source_source_id_reuse_groups"] == 1
    assert len(reconciliation["duplicate_source_ids"][0]["population_row_ids"]) == 2
    assert len(reconciliation["cross_source_source_id_reuse"][0]["population_row_ids"]) == 3
    assert {
        row["identity_status"]
        for row in payload["population_rows"]
        if row["population_kind"] == "historical_offense_2025"
    } == {"canonical_id_duplicate_conflict"}
    assert (
        reconciliation["cross_source_canonical_identity_reconciliation"]["status"]
        == "unevaluable_no_exact_cross_namespace_contract"
    )


def test_identical_duplicate_rows_receive_distinct_ids_and_hash_ledger() -> None:
    row = _historical_row("00-duplicate")
    payload = _build([copy.deepcopy(row), copy.deepcopy(row)], [_rookie_row("wr-one")])
    history_rows = [
        item
        for item in payload["population_rows"]
        if item["population_kind"] == "historical_offense_2025"
    ]
    assert len({item["population_row_id"] for item in history_rows}) == 2
    assert payload["reconciliation"]["counts"]["duplicate_source_row_hash_groups"] == 1


def test_rookie_and_missing_identity_rows_are_preserved_without_name_join() -> None:
    payload = _build(
        [_historical_row("00-0000001", name="Same Display Name")],
        [
            _rookie_row("wr-source-only", name="Same Display Name"),
            _rookie_row(None, name="Missing Source ID", outcome_status=None, team=None),
        ],
    )
    rookie_rows = [
        row
        for row in payload["population_rows"]
        if row["population_kind"] == "rookie_transition_2026"
    ]
    assert len(rookie_rows) == 2
    assert all(row["canonical_player_id"] is None for row in rookie_rows)
    assert all(
        row["history_status"] == "history_unresolved_no_exact_crosswalk" for row in rookie_rows
    )
    missing = [row for row in rookie_rows if row["source_identity_ref"]["source_player_id"] is None]
    assert len(missing) == 1
    assert missing[0]["team_assignment"]["team_status"] == "source_unknown"
    assert payload["reconciliation"]["counts"]["missing_identity_rows"] == 1


def test_provisional_historical_identity_is_preserved_but_not_canonicalized() -> None:
    payload = _build(
        [
            _historical_row(
                "provisional-source-id",
                identity_confidence="provisional",
            )
        ],
        [_rookie_row("wr-one")],
    )
    historical = next(
        row
        for row in payload["population_rows"]
        if row["population_kind"] == "historical_offense_2025"
    )
    assert historical["source_identity_ref"]["source_player_id"] == "provisional-source-id"
    assert historical["source_identity_ref"]["source_identity_confidence"] == "provisional"
    assert historical["canonical_player_id"] is None
    assert historical["identity_status"] == "source_id_present_canonical_unresolved"


def test_explicit_free_agent_and_unsigned_states_are_not_replaced() -> None:
    payload = _build(
        [_historical_row("00-free-agent", team="FA")],
        [_rookie_row("wr-unsigned", outcome_status="unsigned", team=None)],
    )
    statuses = {
        row["source_identity_ref"]["source_player_id"]: row["team_assignment"]["team_status"]
        for row in payload["population_rows"]
    }
    assert statuses["00-free-agent"] == "source_explicit_free_agent"
    assert statuses["wr-unsigned"] == "source_explicit_unsigned"


def test_availability_provenance_preserves_field_associations_and_nulls() -> None:
    payload = _build(
        [_historical_row("00-0000001")],
        [_rookie_row("wr-test", outcome_status=None, team=None)],
    )
    by_kind = {row["population_kind"]: row for row in payload["population_rows"]}
    historical_records = by_kind["historical_offense_2025"]["availability_evidence"][
        "provenance_records"
    ]
    assert historical_records[0]["evidence_field"] == "record_envelope"
    assert historical_records[0]["observed_at"] == "2026-06-30T00:00:00Z"
    assert historical_records[1]["evidence_field"] == "source_refs[0]"
    assert (
        historical_records[1]["source_name"] == "nflreadpy.load_player_stats(summary_level='reg')"
    )
    assert historical_records[1]["observed_at"] == "2026-06-30T00:00:00Z"

    rookie_records = {
        record["evidence_field"]: record
        for record in by_kind["rookie_transition_2026"]["availability_evidence"][
            "provenance_records"
        ]
    }
    assert set(rookie_records) == {
        "draft_capital",
        "age_at_entry",
        "athletic_testing",
        "college_production",
        "official_postdraft_outcome",
    }
    outcome = rookie_records["official_postdraft_outcome"]
    assert outcome["value_status"] == "unavailable"
    assert outcome["source_type"] == "unavailable"
    assert outcome["last_verified_at"] is None
    assert outcome["source_url"] is None


def test_source_hash_verification_fails_closed() -> None:
    (
        data_raw,
        data_governance_raw,
        rookie_raw,
        rookie_governance_raw,
        data_pin,
        rookie_pin,
    ) = _source_inputs()
    altered = data_raw.replace(b"Historical Player", b"Altered Player")
    with pytest.raises(BuildFailure, match="content hash mismatch"):
        build_artifact(
            data_raw=altered,
            data_governance_raw=data_governance_raw,
            rookie_raw=rookie_raw,
            rookie_governance_raw=rookie_governance_raw,
            data_pin=data_pin,
            rookie_pin=rookie_pin,
        )


def test_committed_candidate_passes_schema_and_business_validation() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    assert validate_payload(payload) == []
    assert payload["population_row_count"] == 658
    assert payload["coverage_summary"]["by_source"] == {
        DATA_SOURCE_PIN.source_artifact_key: 610,
        ROOKIE_SOURCE_PIN.source_artifact_key: 48,
    }


def test_validator_rejects_duplicate_population_id_and_forecast_field() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    payload["population_rows"][1]["population_row_id"] = payload["population_rows"][0][
        "population_row_id"
    ]
    payload["population_rows"][0]["forecast_value"] = 1.0
    errors = validate_payload(payload)
    assert any("duplicate population_row_id" in error for error in errors)
    assert any("forbidden output field" in error for error in errors)


def test_validator_rejects_duplicate_and_out_of_range_source_indices() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    data_rows = [
        row
        for row in payload["population_rows"]
        if row["source_identity_ref"]["source_artifact_key"] == DATA_SOURCE_PIN.source_artifact_key
    ]

    duplicate = copy.deepcopy(payload)
    duplicate_by_id = {row["population_row_id"]: row for row in duplicate["population_rows"]}
    duplicate_by_id[data_rows[1]["population_row_id"]]["source_identity_ref"][
        "source_row_index"
    ] = data_rows[0]["source_identity_ref"]["source_row_index"]
    duplicate_errors = validate_payload(duplicate)
    assert any(
        "one or more source rows appear more than once" in error for error in duplicate_errors
    )

    out_of_range = copy.deepcopy(payload)
    out_of_range_by_id = {row["population_row_id"]: row for row in out_of_range["population_rows"]}
    out_of_range_by_id[data_rows[0]["population_row_id"]]["source_identity_ref"][
        "source_row_index"
    ] = 3016
    out_of_range_errors = validate_payload(out_of_range)
    assert any("outside source artifact row range" in error for error in out_of_range_errors)


def test_committed_candidate_source_pins_are_exact() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    descriptors = {source["source_artifact_key"]: source for source in payload["source_artifacts"]}
    assert descriptors[DATA_SOURCE_PIN.source_artifact_key]["commit"] == DATA_SOURCE_PIN.commit
    assert descriptors[DATA_SOURCE_PIN.source_artifact_key]["sha256"] == DATA_SOURCE_PIN.sha256
    assert descriptors[ROOKIE_SOURCE_PIN.source_artifact_key]["commit"] == ROOKIE_SOURCE_PIN.commit
    assert descriptors[ROOKIE_SOURCE_PIN.source_artifact_key]["sha256"] == ROOKIE_SOURCE_PIN.sha256


def test_committed_candidate_preserves_original_source_index_ranges() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    by_source: dict[str, list[int]] = {}
    for row in payload["population_rows"]:
        ref = row["source_identity_ref"]
        by_source.setdefault(ref["source_artifact_key"], []).append(ref["source_row_index"])
    assert sorted(by_source[DATA_SOURCE_PIN.source_artifact_key]) == list(range(2406, 3016))
    assert sorted(by_source[ROOKIE_SOURCE_PIN.source_artifact_key]) == list(range(48))


def test_committed_udfa_null_timestamp_remains_bound_to_its_source_notes() -> None:
    payload = json.loads(COMMITTED_ARTIFACT.read_text(encoding="utf-8"))
    daequan = next(
        row
        for row in payload["population_rows"]
        if row["source_identity_ref"]["source_player_id"] == "te-daequan-wright"
    )
    records = {
        record["evidence_field"]: record
        for record in daequan["availability_evidence"]["provenance_records"]
    }
    outcome = records["official_postdraft_outcome"]
    assert outcome["source_type"] == "official_draft_result"
    assert outcome["last_verified_at"] is None
    assert outcome["source_url"] == (
        "https://www.philadelphiaeagles.com/news/eagles-sign-eight-undrafted-free-agents"
    )
    assert "last_verified_at is null" in outcome["notes"]
