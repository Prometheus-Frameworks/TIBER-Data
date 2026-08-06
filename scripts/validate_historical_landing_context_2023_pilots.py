#!/usr/bin/env python3
"""Validate the candidate-only TIBER-Data#236 historical landing-context pilots."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_historical_landing_context_2023_pilots as builder  # noqa: E402

EXPECTED_PILOTS = {
    "BAL": {
        "gsis_id": "00-0039064",
        "crosswalk_row_id": "rookie-2023-gsis-00-0039064",
        "rookies_slug": "wr-zay-flowers",
        "overall_pick": 22,
        "cutoff": "2023-04-27T23:59:59Z",
        "raw_prior_team": "BAL",
        "binding": "exact_code_match",
        "row_count": 15,
        "target_subtotal": 447,
        "target_share_sum": 0.9614,
        "air_yards_share_sum": 0.9398,
        "multi_team_count": 2,
    },
    "IND": {
        "gsis_id": "00-0038997",
        "crosswalk_row_id": "rookie-2023-gsis-00-0038997",
        "rookies_slug": "wr-josh-downs",
        "overall_pick": 79,
        "cutoff": "2023-04-28T23:59:59Z",
        "raw_prior_team": "IND",
        "binding": "exact_code_match",
        "row_count": 14,
        "target_subtotal": 546,
        "target_share_sum": 0.943,
        "air_yards_share_sum": 0.9549,
        "multi_team_count": 2,
    },
    "LAR": {
        "gsis_id": "00-0039075",
        "crosswalk_row_id": "rookie-2023-gsis-00-0039075",
        "rookies_slug": "wr-puka-nacua",
        "overall_pick": 177,
        "cutoff": "2023-04-29T23:59:59Z",
        "raw_prior_team": "LA",
        "binding": "blocked_2022_alias_outside_issue_237_supported_scope",
        "row_count": 17,
        "target_subtotal": 516,
        "target_share_sum": 0.9982,
        "air_yards_share_sum": 0.9868,
        "multi_team_count": 0,
    },
}
REQUIRED_MISSING_PATHS = {
    "observations.returning_inventory.value",
    "observations.vacated_opportunity.vacated_targets",
    "observations.offseason_chronology.value",
    "observations.roster_at_cutoff.value",
    "observations.quarterback_state.value",
    "observations.coaching_play_caller_state.value",
    "observations.prior_season_offense_quality.value",
    "observations.injury_availability.value",
    "observations.prior_season_usage.complete_team_totals",
    "observations.prior_season_usage.routes_run",
    "observations.prior_season_usage.snap_share",
    "observations.prior_season_usage.route_participation",
    "observations.prior_season_usage.red_zone_targets",
    "observations.prior_season_usage.red_zone_carries",
    "observations.prior_season_usage.temporal.known_by_cutoff",
}
UNAVAILABLE_GROUPS = {
    "returning_inventory",
    "offseason_chronology",
    "roster_at_cutoff",
    "quarterback_state",
    "coaching_play_caller_state",
    "prior_season_offense_quality",
    "injury_availability",
}
FORBIDDEN_TERMINAL_LITERALS = {
    "historical_landing_context_interface_ready_for_pilot",
    "historical_landing_context_interface_blocked",
    "historical_landing_context_ownership_requires_operator_decision",
}


class ValidationFailure(RuntimeError):
    """Raised by consumer helpers when a candidate cannot be admitted."""


def _load(path: Path) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _all_source_ref_ids(payload: dict[str, Any]) -> set[str]:
    return {item["source_ref_id"] for item in payload.get("source_registry", [])}


def _referenced_source_ids(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        if isinstance(value.get("source_ref_ids"), list):
            refs.extend(value["source_ref_ids"])
        for child in value.values():
            refs.extend(_referenced_source_ids(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_referenced_source_ids(child))
    return refs


def _walk_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {
                "data_history_audit_context",
                "forecast_link",
                "ownership_decision",
                "terminal_decision",
            }:
                errors.append(f"forbidden landing-context key at {child_path}")
            errors.extend(_walk_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_forbidden(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value in FORBIDDEN_TERMINAL_LITERALS:
        errors.append(f"operator-reserved terminal literal emitted at {path}")
    return errors


def _parse_datetime(value: str, path: str) -> tuple[datetime | None, str | None]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None, f"date-time lacks an explicit offset at {path}: {value!r}"
        return parsed, None
    except (TypeError, ValueError):
        return None, f"invalid date-time at {path}: {value!r}"


def _temporal_objects(value: Any, path: str = "$") -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "temporal" and isinstance(child, dict):
                found.append((child_path, child))
            found.extend(_temporal_objects(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_temporal_objects(child, f"{path}[{index}]"))
    return found


def validate_temporal_semantics(payload: dict[str, Any], team: str) -> list[str]:
    errors: list[str] = []
    cutoff_value = payload.get("context", {}).get("context_cutoff")
    cutoff, cutoff_error = _parse_datetime(cutoff_value, f"{team}.context.context_cutoff")
    if cutoff_error:
        return [cutoff_error]
    assert cutoff is not None

    for path, temporal in _temporal_objects(payload):
        parsed: dict[str, datetime | None] = {}
        for field in ("effective_at", "source_available_at", "source_updated_at"):
            value = temporal.get(field)
            if value is None:
                parsed[field] = None
                continue
            parsed_value, parse_error = _parse_datetime(value, f"{team}{path[1:]}.{field}")
            if parse_error:
                errors.append(parse_error)
            parsed[field] = parsed_value

        effective_at = parsed["effective_at"]
        if effective_at is not None and effective_at > cutoff:
            errors.append(f"{team}{path[1:]} has post-cutoff effective_at")

        known = temporal.get("known_by_cutoff")
        basis = temporal.get("knowledge_basis")
        available_at = parsed["source_available_at"]
        updated_at = parsed["source_updated_at"]
        if known is True:
            if basis == "draft_selection_ordinal_at_configured_cutoff":
                if path != "$.observations.draft_assignment.temporal":
                    errors.append(f"{team}{path[1:]} misuses draft-selection ordinal basis")
                if available_at is not None and available_at > cutoff:
                    errors.append(
                        f"{team}{path[1:]} draft-selection ordinal uses a post-cutoff source time"
                    )
            elif basis == "source_timestamp_on_or_before_cutoff":
                if available_at is None or available_at > cutoff:
                    errors.append(
                        f"{team}{path[1:]} claims known_by_cutoff without a pre-cutoff source time"
                    )
            else:
                errors.append(
                    f"{team}{path[1:]} known_by_cutoff=true conflicts with basis {basis}"
                )
            if updated_at is not None and updated_at > cutoff:
                errors.append(f"{team}{path[1:]} uses a post-cutoff source revision")
        elif known is False:
            if basis != "source_timestamp_after_cutoff":
                errors.append(
                    f"{team}{path[1:]} known_by_cutoff=false conflicts with basis {basis}"
                )
            if available_at is None or available_at <= cutoff:
                errors.append(
                    f"{team}{path[1:]} after-cutoff basis lacks a post-cutoff source time"
                )
        elif known is None:
            if basis == "source_timing_unavailable":
                if available_at is not None or updated_at is not None:
                    errors.append(
                        f"{team}{path[1:]} source timing is marked unavailable but timestamps exist"
                    )
            elif basis == "not_applicable_missing_group":
                if any(parsed.values()) or temporal.get("effective_period") is not None:
                    errors.append(
                        f"{team}{path[1:]} missing-group temporal state contains a fact time"
                    )
            else:
                errors.append(f"{team}{path[1:]} null known_by_cutoff conflicts with basis {basis}")
        else:
            errors.append(f"{team}{path[1:]} has invalid known_by_cutoff state")

    chronology = payload.get("observations", {}).get("offseason_chronology", {})
    for index, event in enumerate(chronology.get("events", [])):
        for field in ("effective_at", "reported_at"):
            value = event.get(field)
            if value is None:
                continue
            parsed_value, parse_error = _parse_datetime(
                value, f"{team}.observations.offseason_chronology.events[{index}].{field}"
            )
            if parse_error:
                errors.append(parse_error)
            elif parsed_value is not None and parsed_value > cutoff:
                errors.append(
                    f"{team}.observations.offseason_chronology.events[{index}] "
                    f"has post-cutoff {field}"
                )
    return errors


def _resolve_field_path(payload: dict[str, Any], field_path: str) -> tuple[bool, Any]:
    value: Any = payload
    for part in field_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _is_null_or_empty(value: Any) -> bool:
    if value is None or value == []:
        return True
    if isinstance(value, dict) and value:
        return all(_is_null_or_empty(child) for child in value.values())
    return False


def validate_missingness_paths(payload: dict[str, Any], team: str) -> list[str]:
    errors: list[str] = []
    entries = payload.get("missingness", [])
    paths = [entry.get("field_path") for entry in entries]
    if len(paths) != len(set(paths)):
        errors.append(f"{team} missingness field paths are not unique")
    for index, entry in enumerate(entries):
        field_path = entry.get("field_path")
        if not isinstance(field_path, str):
            errors.append(f"{team} missingness[{index}] lacks a string field_path")
            continue
        exists, value = _resolve_field_path(payload, field_path)
        if not exists:
            errors.append(f"{team} missingness path does not resolve: {field_path}")
        elif not _is_null_or_empty(value):
            errors.append(f"{team} missingness path is not null/empty: {field_path}")
    return errors


def _schema_errors(payload: dict[str, Any]) -> list[str]:
    schema = _load(builder.SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    return [
        f"schema {'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    ]


def _source_record_index() -> dict[tuple[str, int, str], dict[str, Any]]:
    source = _load(builder.PLAYER_SEASON_PATH)
    index: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in source.get("records", []):
        key = (row["player_id"], row["season"], row["season_type"])
        if key in index:
            raise ValidationFailure(f"duplicate governed player-season source key: {key}")
        index[key] = row
    return index


def _validate_usage_rows(
    team: str,
    payload: dict[str, Any],
    source_index: dict[tuple[str, int, str], dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    usage = payload["observations"]["prior_season_usage"]
    raw_team = usage["source_team_raw_code"]
    expected_period = {
        "season": payload["context"]["prior_season"],
        "season_type": "REG",
    }
    if usage.get("temporal", {}).get("effective_period") != expected_period:
        errors.append(f"{team} prior-season usage group has the wrong effective period")
    seen_ids: set[str] = set()
    expected_known = {
        source["player_id"]: source
        for source in source_index.values()
        if source.get("season") == 2022
        and source.get("season_type") == "REG"
        and source.get("teams") == [raw_team]
        and isinstance(source.get("usage_summary", {}).get("targets"), int)
        and source["usage_summary"]["targets"] > 0
    }
    actual_known_ids = {
        row.get("player_id") for row in usage.get("known_single_team_rows", [])
    }
    if actual_known_ids != set(expected_known):
        errors.append(
            f"{team} eligible single-team source-row set mismatch: "
            f"expected {sorted(expected_known)}, "
            f"found {sorted(str(item) for item in actual_known_ids)}"
        )

    for index, row in enumerate(usage["known_single_team_rows"]):
        player_id = row["player_id"]
        if player_id in seen_ids:
            errors.append(f"{team} duplicate prior-season player_id {player_id}")
        seen_ids.add(player_id)
        key = (player_id, 2022, "REG")
        source = source_index.get(key)
        if source is None:
            errors.append(f"{team} usage row {player_id} is orphaned from governed source")
            continue
        if source.get("teams") != [raw_team] or row.get("raw_teams") != [raw_team]:
            errors.append(f"{team} usage row {player_id} is not an exact single-team source row")
        if row.get("position") != source.get("position"):
            errors.append(f"{team} usage row {player_id} position differs from governed source")
        if row.get("player_name_audit_only") != source.get("player_name"):
            errors.append(f"{team} usage row {player_id} audit name differs from governed source")
        expected = {
            "targets": source["usage_summary"]["targets"],
            "receptions": source["usage_summary"]["receptions"],
            "receiving_yards": source["production_summary"]["receiving"]["receiving_yards"],
            "receiving_tds": source["production_summary"]["receiving"]["receiving_tds"],
            "receiving_air_yards": source["usage_summary"]["receiving_air_yards"],
            "target_share": source["usage_summary"]["target_share"],
            "air_yards_share": source["usage_summary"]["air_yards_share"],
        }
        actual = {field: row.get(field) for field in expected}
        if actual != expected:
            errors.append(f"{team} usage row {player_id} differs from governed source")
        if row.get("source_record_key") != {
            "player_id": player_id,
            "season": 2022,
            "season_type": "REG",
        }:
            errors.append(f"{team} usage row {player_id} has wrong source record key")
        temporal = row.get("temporal", {})
        if temporal.get("effective_period") != expected_period:
            errors.append(f"{team} usage row {player_id} has the wrong effective period")
        if temporal.get("known_by_cutoff") is not None:
            errors.append(f"{team} usage row {player_id} claims known_by_cutoff without timing proof")
        if temporal.get("source_available_at") is not None:
            errors.append(f"{team} usage row {player_id} fabricates a source availability timestamp")
        if row.get("admitted_to_reconstruction") is not False:
            errors.append(f"{team} usage row {player_id} is improperly admitted")
        if row.get("roster_or_depth_inference_allowed") is not False:
            errors.append(f"{team} usage row {player_id} permits roster/depth inference")

    expected_excluded = {
        source["player_id"]: source
        for source in source_index.values()
        if source.get("season") == 2022
        and source.get("season_type") == "REG"
        and raw_team in source.get("teams", [])
        and source.get("teams") != [raw_team]
        and isinstance(source.get("usage_summary", {}).get("targets"), int)
        and source["usage_summary"]["targets"] > 0
    }
    actual_excluded = {row["player_id"]: row for row in usage["excluded_multi_team_rows"]}
    if set(actual_excluded) != set(expected_excluded):
        errors.append(
            f"{team} multi-team exclusion ledger mismatch: "
            f"expected {sorted(expected_excluded)}, found {sorted(actual_excluded)}"
        )
    for player_id, row in actual_excluded.items():
        source = expected_excluded.get(player_id)
        if source is None:
            continue
        if row.get("raw_teams") != source["teams"]:
            errors.append(f"{team} excluded row {player_id} does not preserve raw teams")
        if row.get("full_season_targets") != source["usage_summary"]["targets"]:
            errors.append(f"{team} excluded row {player_id} target value drifted")
        if row.get("admitted_to_team_values") is not False:
            errors.append(f"{team} unsplit multi-team row {player_id} was admitted")

    subtotal = payload["deterministic_derivations"]["known_single_team_rows_subtotal"]
    rows = usage["known_single_team_rows"]
    recomputed = {
        "row_count": len(rows),
        "targets": sum(row["targets"] for row in rows),
        "target_share_sum": builder._decimal_sum(rows, "target_share"),
        "air_yards_share_sum": builder._decimal_sum(rows, "air_yards_share"),
    }
    for field, value in recomputed.items():
        if subtotal.get(field) != value:
            errors.append(
                f"{team} diagnostic subtotal {field} mismatch: {subtotal.get(field)} != {value}"
            )
    if subtotal.get("admitted_to_reconstruction") is not False:
        errors.append(f"{team} diagnostic subtotal was admitted as a team fact")

    if any(value is not None for value in usage["complete_team_totals"].values()):
        errors.append(f"{team} complete team totals must remain null")
    if usage.get("complete_team_distribution") is not False:
        errors.append(f"{team} prior-season rows are falsely labeled a complete distribution")
    return errors


def validate_payloads(
    pilots: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    source_report: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    errors.extend(_walk_forbidden({"pilots": pilots, "manifest": manifest, "report": source_report}))
    if set(pilots) != set(EXPECTED_PILOTS):
        errors.append(f"pilot team set mismatch: {sorted(pilots)}")
        return errors

    source_index = _source_record_index()
    seen_gsis: set[str] = set()
    for team, expected in EXPECTED_PILOTS.items():
        payload = pilots[team]
        errors.extend(f"{team}: {error}" for error in _schema_errors(payload))
        errors.extend(validate_temporal_semantics(payload, team))
        errors.extend(validate_missingness_paths(payload, team))
        context = payload.get("context", {})
        subject = context.get("subject", {})
        if context.get("effective_at") != expected["cutoff"]:
            errors.append(f"{team} effective_at differs from configured cutoff")
        if context.get("context_cutoff") != expected["cutoff"]:
            errors.append(f"{team} context_cutoff drifted")
        if context.get("same_day_admission_policy") != (
            "draft_selection_ordinal_only_no_external_same_day_fact_without_sequence_evidence"
        ):
            errors.append(f"{team} same-day firewall is missing")
        if context.get("team", {}).get("canonical_code") != team:
            errors.append(f"{team} canonical team mismatch")
        if context.get("team", {}).get("prior_season_source_raw_code") != expected[
            "raw_prior_team"
        ]:
            errors.append(f"{team} raw prior-season team mismatch")
        if context.get("team", {}).get("prior_season_team_binding_status") != expected[
            "binding"
        ]:
            errors.append(f"{team} prior-season team binding drifted")
        expected_bound_team = None if team == "LAR" else team
        if context.get("team", {}).get("prior_season_bound_canonical_code") != expected_bound_team:
            errors.append(f"{team} prior-season bound canonical code drifted")
        if context.get("team", {}).get("prior_season_normalization_applied") is not False:
            errors.append(f"{team} silently normalized its prior-season source code")

        expected_subject = {
            "gsis_id": expected["gsis_id"],
            "crosswalk_row_id": expected["crosswalk_row_id"],
            "rookies_slug": expected["rookies_slug"],
        }
        for field, value in expected_subject.items():
            if subject.get(field) != value:
                errors.append(f"{team} subject {field} mismatch")
        if subject.get("tiber_data_source_player_id") != expected["gsis_id"]:
            errors.append(f"{team} Data source-player edge is not exact GSIS")
        if subject.get("tiber_canonical_player_id") is not None:
            errors.append(f"{team} fabricated a governed TIBER canonical ID")
        if subject.get("display_name_join_used") is not False:
            errors.append(f"{team} used a forbidden display-name join")
        if subject.get("gsis_id") in seen_gsis:
            errors.append(f"duplicate pilot GSIS {subject.get('gsis_id')}")
        seen_gsis.add(subject.get("gsis_id"))

        identity = payload.get("identity_binding", {})
        assertions = _load(builder.SOURCE_ASSERTIONS_PATH)["identity_dependency"]
        expected_identity = {
            "crosswalk_version": assertions["version"],
            "crosswalk_path": assertions["crosswalk_path"],
            "crosswalk_sha256": assertions["crosswalk_sha256"],
            "manifest_path": assertions["manifest_path"],
            "manifest_sha256": assertions["manifest_sha256"],
            "allowed_edge": "gsis_to_tiber_data_source_player_id",
            "tiber_canonical_player_id_edge_authorized": False,
            "projection_policy": (
                "identity_spine_and_2023_draft_fields_only_no_history_or_forecast_context"
            ),
        }
        if identity != expected_identity:
            errors.append(f"{team} #237 identity binding mismatch")

        draft = payload["observations"]["draft_assignment"]
        if draft.get("overall_pick") != expected["overall_pick"]:
            errors.append(f"{team} overall pick mismatch")
        if draft.get("canonical_team") != team:
            errors.append(f"{team} draft assignment mismatch")
        if draft.get("temporal", {}).get("known_by_cutoff") is not True:
            errors.append(f"{team} draft selection is not admitted at configured cutoff")

        refs = payload.get("source_registry", [])
        ref_ids = [ref.get("source_ref_id") for ref in refs]
        if len(ref_ids) != len(set(ref_ids)):
            errors.append(f"{team} duplicate source_ref_id")
        unknown_refs = set(_referenced_source_ids(payload)) - set(ref_ids)
        if unknown_refs:
            errors.append(f"{team} orphan source refs: {sorted(unknown_refs)}")

        errors.extend(_validate_usage_rows(team, payload, source_index))
        subtotal = payload["deterministic_derivations"]["known_single_team_rows_subtotal"]
        for field in ("row_count", "targets", "target_share_sum", "air_yards_share_sum"):
            expected_field = {
                "row_count": "row_count",
                "targets": "target_subtotal",
                "target_share_sum": "target_share_sum",
                "air_yards_share_sum": "air_yards_share_sum",
            }[field]
            if subtotal.get(field) != expected[expected_field]:
                errors.append(f"{team} expected diagnostic {field} drifted")
        if len(payload["observations"]["prior_season_usage"]["excluded_multi_team_rows"]) != expected[
            "multi_team_count"
        ]:
            errors.append(f"{team} expected multi-team exclusion count drifted")

        for group_name in UNAVAILABLE_GROUPS:
            group = payload["observations"][group_name]
            if group.get("value") is not None or group.get("records") != []:
                errors.append(f"{team} unavailable group {group_name} contains a value")
            if group.get("source_ref_ids") != []:
                errors.append(f"{team} unavailable group {group_name} cites a non-fact source")
        vacated = payload["observations"]["vacated_opportunity"]
        vacated_values = [
            vacated.get("vacated_targets"),
            vacated.get("vacated_target_share"),
            vacated.get("vacated_receiving_air_yards"),
            vacated.get("vacated_routes"),
            vacated.get("vacated_snaps"),
        ]
        if any(value is not None for value in vacated_values) or vacated.get("components") != []:
            errors.append(f"{team} vacated opportunity must remain null and component-free")
        if payload.get("interpretations") != {
            "status": "not_in_scope_design_and_evidence_only",
            "records": [],
        }:
            errors.append(f"{team} emitted an interpretation")

        missing_paths = {item.get("field_path") for item in payload.get("missingness", [])}
        if not REQUIRED_MISSING_PATHS.issubset(missing_paths):
            errors.append(f"{team} missingness ledger is incomplete")
        if team == "LAR" and (
            "context.team.prior_season_bound_canonical_code" not in missing_paths
        ):
            errors.append("LAR omits the blocked 2022 LA-to-LAR binding from missingness")
        if payload.get("promotion_authorized") is not False:
            errors.append(f"{team} authorizes promotion")

    pilot_entries = manifest.get("pilot_artifacts", [])
    if len(pilot_entries) != 3:
        errors.append("manifest must bind exactly three pilot artifacts")
    else:
        by_team = {item.get("canonical_team"): item for item in pilot_entries}
        if set(by_team) != set(pilots):
            errors.append("manifest pilot team set mismatch")
        for team, payload in pilots.items():
            item = by_team.get(team, {})
            path = builder.PILOT_OUTPUT_PATHS[team]
            expected_hash = builder.sha256(builder.serialize(payload))
            if item.get("path") != path.as_posix() or item.get("sha256") != expected_hash:
                errors.append(f"manifest does not bind exact {team} pilot bytes")

    if manifest.get("promotion_authorized") is not False:
        errors.append("manifest authorizes promotion")
    boundary = manifest.get("consumer_boundary", {})
    if boundary.get("ownership_decision_made") is not False:
        errors.append("manifest makes an operator-reserved ownership decision")
    if boundary.get("interpretations_authorized") is not False:
        errors.append("manifest authorizes interpretations")
    if boundary.get("identity_edge") != "gsis_to_tiber_data_source_player_id":
        errors.append("manifest identity edge drifted")

    expected_source_families = {
        "prior_season_targets_shares_air_yards_and_receiving",
        "vacated_targets_and_receiving_opportunity",
        "draft_day_roster_or_depth_chart",
        "offseason_arrivals_and_departures",
        "quarterback_state",
        "coaching_and_play_caller_state",
        "prior_season_offense_quality_volume_personnel_and_scoring",
        "injury_and_availability",
        "draft_results_and_team_assignment",
    }
    actual_families = {item.get("family") for item in source_report.get("source_families", [])}
    if actual_families != expected_source_families:
        errors.append("source availability report does not cover all nine required families")
    report_ref_ids = {
        item.get("source_ref_id") for item in source_report.get("source_registry", [])
    }
    report_claim_refs = {
        ref_id
        for item in source_report.get("source_families", [])
        for ref_id in item.get("source_ref_ids", [])
    } | {
        ref_id
        for item in source_report.get("pilot_findings", [])
        for ref_id in item.get("source_ref_ids", [])
    }
    if report_claim_refs - report_ref_ids:
        errors.append(
            "source availability report has orphan source refs: "
            f"{sorted(report_claim_refs - report_ref_ids)}"
        )
    if len(source_report.get("pinned_frozen_rookies_comparison_references", [])) != 3:
        errors.append("source report must pin all three frozen Rookies comparison refs")
    firewall = source_report.get("hindsight_firewall", {})
    if set(firewall.values()) != {False}:
        errors.append("source report admits a hindsight or modern-history lane")
    if source_report.get("scope", {}).get("ownership_decision_reserved_for_operator") is not True:
        errors.append("source report does not reserve ownership for the operator")
    if source_report.get("scope", {}).get("promotion_authorized") is not False:
        errors.append("source report authorizes promotion")

    return errors


def _git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationFailure(f"cannot read {repo_root}@{commit}:{path}: {detail}")
    return result.stdout


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return sha1(header + raw).hexdigest()


def validate_rookies_cutoff_refs(rookies_repo_root: Path) -> list[str]:
    errors: list[str] = []
    assertions = _load(builder.SOURCE_ASSERTIONS_PATH)
    for pilot in assertions["pilots"]:
        ref = pilot["cutoff_reference"]
        try:
            raw = _git_blob(rookies_repo_root, ref["git_commit"], ref["path"])
        except ValidationFailure as exc:
            errors.append(str(exc))
            continue
        if builder.sha256(raw) != ref["sha256"]:
            errors.append(f"Rookies cutoff reference SHA mismatch for {pilot['pilot_id']}")
        if _git_blob_sha(raw) != ref["git_blob"]:
            errors.append(f"Rookies cutoff reference blob mismatch for {pilot['pilot_id']}")
        payload = json.loads(raw)
        observed_cutoff = payload.get("landing_context", {}).get("context_cutoff")
        if observed_cutoff != pilot["context_cutoff"]:
            errors.append(f"Rookies cutoff reference value mismatch for {pilot['pilot_id']}")
    return errors


def validate_data_commit_pins(data_repo_root: Path) -> list[str]:
    """Replay every asserted Data commit:path, blob, and content hash."""

    errors: list[str] = []
    assertions = _load(builder.SOURCE_ASSERTIONS_PATH)
    identity = assertions["identity_dependency"]
    refs = [
        {
            "label": "#237 crosswalk",
            "git_commit": identity["git_commit"],
            "path": identity["crosswalk_path"],
            "git_blob": identity["crosswalk_git_blob"],
            "sha256": identity["crosswalk_sha256"],
        },
        {
            "label": "#237 manifest",
            "git_commit": identity["git_commit"],
            "path": identity["manifest_path"],
            "git_blob": identity["manifest_git_blob"],
            "sha256": identity["manifest_sha256"],
        },
        {
            "label": "promoted player-season coverage",
            **assertions["player_season_source"],
        },
        {
            "label": "player-season origin candidate",
            **assertions["player_season_origin_candidate"],
        },
        *[
            {"label": f"bounded inventory {item['path']}", **item}
            for item in assertions["bounded_repository_inventory"]
        ],
    ]
    for ref in refs:
        try:
            raw = _git_blob(data_repo_root, ref["git_commit"], ref["path"])
        except ValidationFailure as exc:
            errors.append(str(exc))
            continue
        if builder.sha256(raw) != ref["sha256"]:
            errors.append(f"Data commit content SHA mismatch for {ref['label']}")
        if _git_blob_sha(raw) != ref["git_blob"]:
            errors.append(f"Data commit Git blob mismatch for {ref['label']}")
    return errors


def validate_committed(
    *, rookies_repo_root: Path | None = None, data_repo_root: Path | None = None
) -> tuple[dict[str, Any], list[str]]:
    pilots = {team: _load(path) for team, path in builder.PILOT_OUTPUT_PATHS.items()}
    manifest = _load(builder.MANIFEST_PATH)
    source_report = _load(builder.SOURCE_REPORT_JSON_PATH)
    errors = validate_payloads(pilots, manifest, source_report)

    try:
        expected_outputs = builder.build_outputs()
    except (builder.BuildFailure, jsonschema.SchemaError) as exc:
        errors.append(f"deterministic rebuild failed: {exc}")
        expected_outputs = {}
    for path, expected in expected_outputs.items():
        target = ROOT / path
        if not target.exists():
            errors.append(f"deterministic output missing: {path}")
        elif target.read_bytes() != expected:
            errors.append(f"committed output differs from deterministic rebuild: {path}")

    source_assertions = _load(builder.SOURCE_ASSERTIONS_PATH)
    for path, expected, label in [
        (
            builder.CROSSWALK_PATH,
            source_assertions["identity_dependency"]["crosswalk_sha256"],
            "#237 crosswalk",
        ),
        (
            builder.CROSSWALK_MANIFEST_PATH,
            source_assertions["identity_dependency"]["manifest_sha256"],
            "#237 manifest",
        ),
        (
            builder.PLAYER_SEASON_PATH,
            source_assertions["player_season_source"]["sha256"],
            "player-season coverage",
        ),
        (
            builder.PLAYER_SEASON_ORIGIN_PATH,
            source_assertions["player_season_origin_candidate"]["sha256"],
            "player-season origin candidate",
        ),
    ]:
        actual = builder.sha256((ROOT / path).read_bytes())
        if actual != expected:
            errors.append(f"local source hash mismatch for {label}")

    if rookies_repo_root is not None:
        rookies_errors = validate_rookies_cutoff_refs(rookies_repo_root)
        errors.extend(rookies_errors)
        rookies_status = "passed" if not rookies_errors else "failed"
    else:
        rookies_status = "not_run"
    if data_repo_root is not None:
        data_errors = validate_data_commit_pins(data_repo_root)
        errors.extend(data_errors)
        data_status = "passed" if not data_errors else "failed"
    else:
        data_status = "not_run"

    report = {
        "artifact_id": "historical_landing_context_2023_pilot_bundle_validation",
        "validator_version": "0.1.0",
        "generated_at": builder.GENERATED_AT,
        "status": "valid" if not errors else "invalid",
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "external_rookies_cutoff_reference_verification": {
            "status": rookies_status,
            "rookies_repo_root_supplied": rookies_repo_root is not None,
        },
        "external_data_commit_pin_verification": {
            "status": data_status,
            "data_repo_root_supplied": data_repo_root is not None,
        },
        "validated_artifacts": [
            {
                "canonical_team": team,
                "path": path.as_posix(),
                "sha256": builder.sha256((ROOT / path).read_bytes()),
            }
            for team, path in sorted(builder.PILOT_OUTPUT_PATHS.items())
        ],
        "checks": [
            "draft_candidate_schema",
            "deterministic_rebuild",
            "exact_three_pilot_identity_and_cutoff_tuples",
            "issue_237_version_hash_and_exact_gsis_edge",
            "display_name_join_ban",
            "later_history_and_forecast_projection_ban",
            "raw_team_code_preservation_and_2022_lar_alias_block",
            "player_season_row_reproduction",
            "multi_team_full_season_exclusion",
            "known_by_cutoff_temporal_admission",
            "complete_team_total_and_vacancy_null_policy",
            "explicit_required_family_missingness",
            "observation_derivation_interpretation_separation",
            "candidate_no_promotion_no_ownership_no_terminal_boundary",
            "optional_pinned_rookies_cutoff_reference_replay",
            "optional_asserted_data_commit_path_blob_and_hash_replay",
        ],
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="write deterministic validation JSON")
    parser.add_argument(
        "--rookies-repo-root",
        type=Path,
        help="optionally replay pinned cutoff comparison refs from a TIBER-Rookies checkout",
    )
    parser.add_argument(
        "--data-repo-root",
        type=Path,
        help="optionally replay every asserted TIBER-Data commit:path/blob/content pin",
    )
    args = parser.parse_args()
    report, errors = validate_committed(
        rookies_repo_root=args.rookies_repo_root,
        data_repo_root=args.data_repo_root,
    )
    if args.report:
        target = ROOT / builder.VALIDATION_REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(builder.serialize(report))
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "VALIDATION PASSED: 3 pilot candidates; identity-only admission; "
        "2022 usage timing unresolved; complete team/vacancy values null"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
