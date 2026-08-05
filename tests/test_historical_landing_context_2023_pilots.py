import json
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, path: str):
    spec = spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _module(
        "historical_landing_context_2023_builder",
        "scripts/build_historical_landing_context_2023_pilots.py",
    )


@pytest.fixture(scope="module")
def validator():
    return _module(
        "historical_landing_context_2023_validator",
        "scripts/validate_historical_landing_context_2023_pilots.py",
    )


@pytest.fixture()
def payloads(builder):
    pilots = {
        team: json.loads((ROOT / path).read_text(encoding="utf-8"))
        for team, path in builder.PILOT_OUTPUT_PATHS.items()
    }
    manifest = json.loads((ROOT / builder.MANIFEST_PATH).read_text(encoding="utf-8"))
    report = json.loads((ROOT / builder.SOURCE_REPORT_JSON_PATH).read_text(encoding="utf-8"))
    return pilots, manifest, report


def test_committed_bundle_validates_and_rebuilds_deterministically(validator) -> None:
    report, errors = validator.validate_committed()
    assert errors == []
    assert report["valid"] is True


@pytest.mark.skipif(
    not (ROOT.parent / "TIBER-Rookies").exists(),
    reason="sibling TIBER-Rookies checkout is unavailable",
)
def test_pinned_rookies_cutoff_references_replay(validator) -> None:
    assert validator.validate_rookies_cutoff_refs(ROOT.parent / "TIBER-Rookies") == []


def test_asserted_data_commit_path_blob_and_hash_pins_replay(validator) -> None:
    assert validator.validate_data_commit_pins(ROOT) == []


def test_exact_three_pilot_identity_cutoff_and_pick_tuples(payloads) -> None:
    pilots, _, _ = payloads
    expected = {
        "BAL": ("00-0039064", "2023-04-27T23:59:59Z", 22),
        "IND": ("00-0038997", "2023-04-28T23:59:59Z", 79),
        "LAR": ("00-0039075", "2023-04-29T23:59:59Z", 177),
    }
    assert set(pilots) == set(expected)
    for team, (gsis, cutoff, pick) in expected.items():
        payload = pilots[team]
        assert payload["context"]["subject"]["gsis_id"] == gsis
        assert payload["context"]["effective_at"] == cutoff
        assert payload["context"]["context_cutoff"] == cutoff
        assert payload["observations"]["draft_assignment"]["overall_pick"] == pick
        assert payload["observations"]["draft_assignment"]["canonical_team"] == team


def test_identity_is_manifest_bound_exact_gsis_only(payloads) -> None:
    pilots, manifest, _ = payloads
    dependency = manifest["identity_dependency"]
    assert dependency == {
        "allowed_edge": "gsis_to_tiber_data_source_player_id",
        "crosswalk_path": (
            "exports/candidates/identity_crosswalk/"
            "rookie_2023_identity_crosswalk_v0.1.0.json"
        ),
        "crosswalk_sha256": "db1a08192aacf604d0be7930147b3e0182c28250bda246c65fbca290ed9a11e2",
        "manifest_path": (
            "exports/candidates/identity_crosswalk/"
            "rookie_2023_identity_crosswalk_v0.1.0.manifest.json"
        ),
        "manifest_sha256": "ff3eacdd8e8f5c1b5ab59911b3f7fd8601cb2e17aadce1ab1c57c1f06e949c2d",
        "tiber_canonical_player_id_edge_authorized": False,
        "version": "0.1.0",
    }
    for payload in pilots.values():
        subject = payload["context"]["subject"]
        assert subject["tiber_data_source_player_id"] == subject["gsis_id"]
        assert subject["tiber_canonical_player_id"] is None
        assert subject["display_name_join_used"] is False
        assert payload["identity_binding"]["allowed_edge"] == dependency["allowed_edge"]


def test_crosswalk_later_history_and_forecast_fields_are_not_projected(
    payloads, validator
) -> None:
    pilots, manifest, report = payloads
    assert validator._walk_forbidden(
        {"pilots": pilots, "manifest": manifest, "report": report}
    ) == []
    serialized = json.dumps(pilots)
    assert "data_history_audit_context" not in serialized
    assert "forecast_link" not in serialized
    assert "00-0038543" not in serialized


def test_lar_preserves_raw_la_and_blocks_unsupported_2022_alias(payloads) -> None:
    pilots, _, _ = payloads
    team = pilots["LAR"]["context"]["team"]
    assert team == {
        "canonical_code": "LAR",
        "draft_source_raw_code": "LAR",
        "prior_season_bound_canonical_code": None,
        "prior_season_normalization_applied": False,
        "prior_season_source_raw_code": "LA",
        "prior_season_team_binding_status": (
            "blocked_2022_alias_outside_issue_237_supported_scope"
        ),
    }
    usage = pilots["LAR"]["observations"]["prior_season_usage"]
    assert usage["support_status"] == "blocked_team_alias_and_source_timing_unproven"
    assert all(row["raw_teams"] == ["LA"] for row in usage["known_single_team_rows"])


def test_prior_usage_rows_are_exact_unadmitted_observations(payloads) -> None:
    pilots, _, _ = payloads
    expected = {
        "BAL": (15, 447, 0.9614, 0.9398),
        "IND": (14, 546, 0.943, 0.9549),
        "LAR": (17, 516, 0.9982, 0.9868),
    }
    for team, values in expected.items():
        usage = pilots[team]["observations"]["prior_season_usage"]
        rows = usage["known_single_team_rows"]
        assert all(row["admitted_to_reconstruction"] is False for row in rows)
        assert all(row["roster_or_depth_inference_allowed"] is False for row in rows)
        assert all(row["temporal"]["known_by_cutoff"] is None for row in rows)
        assert all(row["temporal"]["effective_at"] is None for row in rows)
        assert all(row["temporal"]["effective_period"] == {
            "season": 2022,
            "season_type": "REG",
        } for row in rows)
        subtotal = pilots[team]["deterministic_derivations"][
            "known_single_team_rows_subtotal"
        ]
        assert (
            subtotal["row_count"],
            subtotal["targets"],
            subtotal["target_share_sum"],
            subtotal["air_yards_share_sum"],
        ) == values
        assert subtotal["admitted_to_reconstruction"] is False


def test_multi_team_full_season_rows_are_explicitly_excluded(payloads) -> None:
    pilots, _, _ = payloads
    assert len(pilots["BAL"]["observations"]["prior_season_usage"]["excluded_multi_team_rows"]) == 2
    assert len(pilots["IND"]["observations"]["prior_season_usage"]["excluded_multi_team_rows"]) == 2
    assert pilots["LAR"]["observations"]["prior_season_usage"]["excluded_multi_team_rows"] == []
    for payload in pilots.values():
        for row in payload["observations"]["prior_season_usage"]["excluded_multi_team_rows"]:
            assert len(row["raw_teams"]) > 1
            assert row["admitted_to_team_values"] is False
            assert row["exclusion_reason"] == "full_season_usage_not_split_across_teams"


def test_team_totals_vacancy_and_required_source_families_fail_closed(payloads) -> None:
    pilots, _, _ = payloads
    unavailable = {
        "returning_inventory",
        "offseason_chronology",
        "roster_at_cutoff",
        "quarterback_state",
        "coaching_play_caller_state",
        "prior_season_offense_quality",
        "injury_availability",
    }
    for payload in pilots.values():
        observations = payload["observations"]
        assert observations["prior_season_usage"]["complete_team_distribution"] is False
        assert set(observations["prior_season_usage"]["complete_team_totals"].values()) == {None}
        for group_name in unavailable:
            assert observations[group_name]["value"] is None
            assert observations[group_name]["records"] == []
        vacancy = observations["vacated_opportunity"]
        assert vacancy["vacated_targets"] is None
        assert vacancy["vacated_routes"] is None
        assert vacancy["vacated_snaps"] is None
        assert vacancy["components"] == []


def test_observation_derivation_and_interpretation_boundary_is_structural(payloads) -> None:
    pilots, _, _ = payloads
    for payload in pilots.values():
        assert payload["interpretations"] == {
            "status": "not_in_scope_design_and_evidence_only",
            "records": [],
        }
        assert payload["deterministic_derivations"]["known_single_team_rows_subtotal"][
            "row_kind"
        ] == "deterministic_derivation"
        assert payload["observations"]["draft_assignment"]["row_kind"] == "observation"


def test_manifest_binds_schema_inputs_pilots_and_gap_report(payloads, builder) -> None:
    pilots, manifest, _ = payloads
    assert manifest["promotion_authorized"] is False
    assert manifest["schema"]["governed_contract"] is False
    assert manifest["schema"]["sha256"] == builder.sha256(
        (ROOT / builder.SCHEMA_PATH).read_bytes()
    )
    assert manifest["source_assertions"]["sha256"] == builder.sha256(
        (ROOT / builder.SOURCE_ASSERTIONS_PATH).read_bytes()
    )
    by_team = {item["canonical_team"]: item for item in manifest["pilot_artifacts"]}
    for team, payload in pilots.items():
        assert by_team[team]["sha256"] == builder.sha256(builder.serialize(payload))
    report_ref = manifest["source_availability_report"]
    assert report_ref["json_sha256"] == builder.sha256(
        (ROOT / builder.SOURCE_REPORT_JSON_PATH).read_bytes()
    )
    assert report_ref["markdown_sha256"] == builder.sha256(
        (ROOT / builder.SOURCE_REPORT_MD_PATH).read_bytes()
    )


def test_source_gap_report_covers_all_families_and_explicit_hindsight_exclusions(payloads) -> None:
    _, _, report = payloads
    assert len(report["source_families"]) == 9
    assert report["scope"]["ownership_decision_reserved_for_operator"] is True
    assert report["scope"]["promotion_authorized"] is False
    assert set(report["hindsight_firewall"].values()) == {False}
    assert report["frozen_rookies_reference_audit"]["facts_admitted_from_reference"] is False
    assert len(report["pinned_frozen_rookies_comparison_references"]) == 3
    inventory_paths = {item["path"] for item in report["bounded_repository_inventory"]}
    assert {
        "data/processed/evidence/roster_player_team_map_2025.source_backed.json",
        "exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl",
        "exports/promoted/player_ownership/player_ownership_latest.json",
        "schemas/player_ownership_change_event_v0.schema.json",
    } <= inventory_paths
    team_week = next(
        item
        for item in report["bounded_repository_inventory"]
        if item["path"]
        == "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json"
    )
    assert "governed real data" in team_week["observed_scope"]
    assert team_week["april_2023_admissibility"] == "not_admissible_wrong_season"
    source_ref_ids = {item["source_ref_id"] for item in report["source_registry"]}
    claim_ref_ids = {
        ref_id
        for item in report["source_families"] + report["pilot_findings"]
        for ref_id in item["source_ref_ids"]
    }
    assert claim_ref_ids <= source_ref_ids
    assert any(
        "June 2023 Cooper Kupp" in reason
        for reason in report["frozen_rookies_reference_audit"]["reasons"]
    )


def test_validator_rejects_known_by_cutoff_without_temporal_proof(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    pilots["BAL"]["observations"]["prior_season_usage"]["known_single_team_rows"][0][
        "temporal"
    ]["known_by_cutoff"] = True
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("claims known_by_cutoff without timing proof" in error for error in errors)


def test_validator_rejects_contradictory_after_cutoff_temporal_claim(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    temporal = pilots["BAL"]["observations"]["draft_assignment"]["temporal"]
    temporal.update(
        {
            "effective_at": "2024-01-01T00:00:00Z",
            "source_available_at": "2024-01-01T00:00:00Z",
            "source_updated_at": "2024-01-01T00:00:00Z",
            "known_by_cutoff": True,
            "knowledge_basis": "source_timestamp_after_cutoff",
        }
    )
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("post-cutoff effective_at" in error for error in errors)
    assert any("known_by_cutoff=true conflicts" in error for error in errors)


def test_validator_rejects_post_cutoff_source_time_on_draft_ordinal(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    pilots["BAL"]["observations"]["draft_assignment"]["temporal"][
        "source_available_at"
    ] = "2024-01-01T00:00:00Z"
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("draft-selection ordinal uses a post-cutoff source time" in error for error in errors)


def test_validator_rejects_wrong_prior_season_effective_period(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    usage = pilots["BAL"]["observations"]["prior_season_usage"]
    usage["temporal"]["effective_period"]["season"] = 2025
    usage["known_single_team_rows"][0]["temporal"]["effective_period"]["season"] = 2025
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("usage group has the wrong effective period" in error for error in errors)
    assert any("usage row" in error and "wrong effective period" in error for error in errors)


def test_validator_rejects_post_cutoff_chronology_event_fields(payloads, validator) -> None:
    pilots, _, _ = deepcopy(payloads)
    temporal = {
        "effective_at": "2023-03-01T00:00:00Z",
        "effective_period": None,
        "source_available_at": "2023-03-01T00:00:00Z",
        "source_updated_at": None,
        "known_by_cutoff": True,
        "knowledge_basis": "source_timestamp_on_or_before_cutoff",
    }
    pilots["BAL"]["observations"]["offseason_chronology"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "events": [
            {
                "event_id": "event-after-cutoff",
                "event_type": "signed",
                "player_id": "00-0000001",
                "from_team_code": None,
                "to_team_code": "BAL",
                "effective_at": "2024-01-01T00:00:00Z",
                "reported_at": "2024-01-02T00:00:00Z",
                "needs_verification": False,
                "temporal": temporal,
                "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
            }
        ],
        "temporal": temporal,
        "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
    }
    errors = validator.validate_temporal_semantics(pilots["BAL"], "BAL")
    assert any("post-cutoff effective_at" in error for error in errors)
    assert any("post-cutoff reported_at" in error for error in errors)


def test_missingness_paths_resolve_to_actual_null_or_empty_values(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    for team, payload in pilots.items():
        assert validator.validate_missingness_paths(payload, team) == []
    pilots["IND"]["missingness"][0]["field_path"] = "observations.not_a_real_group.value"
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("missingness path does not resolve" in error for error in errors)


def test_validator_rejects_multi_team_row_in_team_values(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    excluded = pilots["BAL"]["observations"]["prior_season_usage"][
        "excluded_multi_team_rows"
    ][0]
    injected = deepcopy(
        pilots["BAL"]["observations"]["prior_season_usage"]["known_single_team_rows"][0]
    )
    injected["player_id"] = excluded["player_id"]
    injected["source_record_key"]["player_id"] = excluded["player_id"]
    injected["raw_teams"] = excluded["raw_teams"]
    pilots["BAL"]["observations"]["prior_season_usage"]["known_single_team_rows"].append(
        injected
    )
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("is not an exact single-team source row" in error for error in errors)


def test_validator_rejects_source_row_name_position_or_population_drift(
    payloads, validator
) -> None:
    pilots, manifest, report = deepcopy(payloads)
    row = pilots["BAL"]["observations"]["prior_season_usage"]["known_single_team_rows"][0]
    row["player_name_audit_only"] = "Wrong Descriptor"
    row["position"] = "QB"
    pilots["BAL"]["observations"]["prior_season_usage"]["known_single_team_rows"].pop()
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("eligible single-team source-row set mismatch" in error for error in errors)
    assert any("position differs" in error for error in errors)
    assert any("audit name differs" in error for error in errors)


def test_validator_rejects_silent_2022_la_to_lar_normalization(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    team = pilots["LAR"]["context"]["team"]
    team["prior_season_source_raw_code"] = "LAR"
    team["prior_season_normalization_applied"] = True
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("silently normalized" in error for error in errors)


def test_validator_rejects_operator_reserved_terminal_decision(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    manifest["terminal_decision"] = "historical_landing_context_interface_ready_for_pilot"
    errors = validator.validate_payloads(pilots, manifest, report)
    assert any("terminal" in error for error in errors)


def test_validator_rejects_operator_reserved_ownership_decision(payloads, validator) -> None:
    pilots, manifest, report = deepcopy(payloads)
    manifest["ownership_decision"] = "TIBER-Data owns the interface"
    report["ownership_decision"] = "TIBER-Teamstate owns the interface"
    errors = validator.validate_payloads(pilots, manifest, report)
    assert sum("ownership_decision" in error for error in errors) == 2


def test_draft_schema_rejects_uncontracted_fields(payloads, validator) -> None:
    pilots, _, _ = deepcopy(payloads)
    pilots["IND"]["context"]["subject"]["display_name"] = "Josh Downs"
    errors = validator._schema_errors(pilots["IND"])
    assert any("Additional properties are not allowed" in error for error in errors)


def test_draft_schema_can_represent_typed_available_source_families(payloads, validator) -> None:
    pilots, _, _ = deepcopy(payloads)
    payload = pilots["BAL"]
    temporal = {
        "effective_at": "2023-03-01T00:00:00Z",
        "effective_period": None,
        "source_available_at": "2023-03-01T00:00:00Z",
        "source_updated_at": None,
        "known_by_cutoff": True,
        "knowledge_basis": "source_timestamp_on_or_before_cutoff",
    }
    refs = ["tiber-data-player-season-coverage-v0-promoted"]
    roster_member = {
        "player_id": "00-0000001",
        "position": "WR",
        "roster_status": "returning",
        "depth_rank": None,
        "needs_verification": False,
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["returning_inventory"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "receivers": [roster_member],
        "tight_ends": [],
        "running_backs": [],
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["offseason_chronology"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "events": [
            {
                "event_id": "event-1",
                "event_type": "signed",
                "player_id": "00-0000001",
                "from_team_code": None,
                "to_team_code": "BAL",
                "effective_at": "2023-03-01T00:00:00Z",
                "reported_at": "2023-03-01T00:00:00Z",
                "needs_verification": False,
                "temporal": temporal,
                "source_ref_ids": refs,
            }
        ],
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["roster_at_cutoff"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "players": [roster_member],
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["quarterback_state"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "starter_player_id": "00-0000002",
        "competition_player_ids": [],
        "stability_status": "established",
        "availability_status": "available",
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["coaching_play_caller_state"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "head_coach_source_key": "coach-1",
        "offensive_coordinator_source_key": "coach-2",
        "play_caller_source_key": "coach-2",
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["prior_season_offense_quality"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "metrics": [
            {
                "metric_name": "team_targets",
                "value": 500,
                "unit": "targets",
                "temporal": temporal,
                "source_ref_ids": refs,
            }
        ],
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["injury_availability"] = {
        "row_kind": "observation",
        "support_status": "source_backed",
        "needs_verification": False,
        "records": [
            {
                "player_id": "00-0000001",
                "availability_status": "available",
                "injury_label": None,
                "temporal": temporal,
                "source_ref_ids": refs,
            }
        ],
        "temporal": temporal,
        "source_ref_ids": refs,
    }
    payload["observations"]["vacated_opportunity"] = {
        "row_kind": "deterministic_derivation",
        "support_status": "source_backed_complete_components",
        "needs_verification": False,
        "vacated_targets": 10,
        "vacated_target_share": 0.02,
        "vacated_receiving_air_yards": 100,
        "vacated_routes": None,
        "vacated_snaps": None,
        "calculation_method": "sum complete source-backed components",
        "components": [
            {
                "player_id": "00-0000001",
                "departure_event_id": "event-1",
                "targets": 10,
                "target_share": 0.02,
                "receiving_air_yards": 100,
                "source_ref_ids": refs + ["issue-237-crosswalk-candidate"],
            }
        ],
        "temporal": temporal,
        "source_ref_ids": refs + ["issue-237-crosswalk-candidate"],
    }
    assert validator._schema_errors(payload) == []
