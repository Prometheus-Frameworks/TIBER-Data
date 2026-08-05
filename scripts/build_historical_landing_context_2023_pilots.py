#!/usr/bin/env python3
"""Build the candidate-only TIBER-Data#236 historical landing-context pilots.

The builder is intentionally conservative. It projects only the manifest-bound
identity spine from #237, preserves 2022 player-season evidence as unadmitted
candidate rows when source timing is unproven, and emits explicit nulls for
source families that TIBER-Data cannot currently reproduce at the cutoff.
"""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from hashlib import sha1 as _sha1
from hashlib import sha256 as _sha256
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
GENERATED_AT = "2026-08-05T00:00:00Z"
SCHEMA_VERSION = "historical_landing_context_candidate_v0.1.0"
SOURCE_ASSERTIONS_PATH = Path(
    "data/candidate/historical_landing_context/2023_pilot_source_assertions_v0.json"
)
SCHEMA_PATH = Path(
    "data/candidate/historical_landing_context/"
    "historical_landing_context_candidate_v0.1.0.schema.json"
)
CROSSWALK_PATH = Path(
    "exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.json"
)
CROSSWALK_MANIFEST_PATH = Path(
    "exports/candidates/identity_crosswalk/rookie_2023_identity_crosswalk_v0.1.0.manifest.json"
)
PLAYER_SEASON_PATH = Path("exports/promoted/nfl/player_season_coverage_v0.json")
PLAYER_SEASON_ORIGIN_PATH = Path(
    "data/processed/evidence/player_season_coverage_2022_2025.source_backed.json"
)
OUTPUT_DIR = Path("exports/candidates/historical_landing_context")
PILOT_OUTPUT_PATHS = {
    "BAL": OUTPUT_DIR / "2023_bal_historical_landing_context_v0.1.0.json",
    "IND": OUTPUT_DIR / "2023_ind_historical_landing_context_v0.1.0.json",
    "LAR": OUTPUT_DIR / "2023_lar_historical_landing_context_v0.1.0.json",
}
MANIFEST_PATH = OUTPUT_DIR / "2023_historical_landing_context_pilot_bundle_v0.1.0.manifest.json"
VALIDATION_REPORT_PATH = (
    OUTPUT_DIR / "2023_historical_landing_context_pilot_bundle_v0.1.0.validation.json"
)
SOURCE_REPORT_JSON_PATH = Path(
    "docs/reports/historical-landing-context-2023-source-availability-2026-08-05.json"
)
SOURCE_REPORT_MD_PATH = Path(
    "docs/reports/historical-landing-context-2023-source-availability-2026-08-05.md"
)


class BuildFailure(RuntimeError):
    """Raised when a pinned input or fail-closed build invariant is violated."""


def sha256(raw: bytes) -> str:
    return _sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    return _sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def serialize(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def load_json(path: Path) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def require_sha(
    path: Path, expected: str, label: str, *, expected_git_blob: str | None = None
) -> bytes:
    raw = (ROOT / path).read_bytes()
    actual = sha256(raw)
    if actual != expected:
        raise BuildFailure(f"{label} SHA-256 mismatch: expected {expected}, found {actual}")
    if expected_git_blob is not None and git_blob_sha(raw) != expected_git_blob:
        raise BuildFailure(
            f"{label} Git blob mismatch: expected {expected_git_blob}, "
            f"found {git_blob_sha(raw)}"
        )
    return raw


def _source_ref(
    *,
    source_ref_id: str,
    ref: dict[str, Any],
    role: str,
    authority: str,
    observed_at: str | None = None,
    source_updated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "source_ref_id": source_ref_id,
        "repository": ref["repository"],
        "git_commit": ref["git_commit"],
        "path": ref.get("path") or ref.get("crosswalk_path") or ref.get("manifest_path"),
        "git_blob": ref.get("git_blob")
        or ref.get("crosswalk_git_blob")
        or ref.get("manifest_git_blob"),
        "sha256": ref.get("sha256")
        or ref.get("crosswalk_sha256")
        or ref.get("manifest_sha256"),
        "role": role,
        "authority": authority,
        "observed_at": observed_at,
        "source_updated_at": source_updated_at,
    }


def verify_local_inputs(assertions: dict[str, Any]) -> None:
    identity = assertions["identity_dependency"]
    require_sha(
        CROSSWALK_PATH,
        identity["crosswalk_sha256"],
        "#237 crosswalk",
        expected_git_blob=identity["crosswalk_git_blob"],
    )
    require_sha(
        CROSSWALK_MANIFEST_PATH,
        identity["manifest_sha256"],
        "#237 manifest",
        expected_git_blob=identity["manifest_git_blob"],
    )

    player_source = assertions["player_season_source"]
    require_sha(
        PLAYER_SEASON_PATH,
        player_source["sha256"],
        "promoted player-season source",
        expected_git_blob=player_source["git_blob"],
    )
    origin = assertions["player_season_origin_candidate"]
    require_sha(
        PLAYER_SEASON_ORIGIN_PATH,
        origin["sha256"],
        "player-season origin candidate",
        expected_git_blob=origin["git_blob"],
    )

    for item in assertions["bounded_repository_inventory"]:
        require_sha(
            Path(item["path"]),
            item["sha256"],
            f"bounded inventory {item['path']}",
            expected_git_blob=item["git_blob"],
        )

    manifest = load_json(CROSSWALK_MANIFEST_PATH)
    binding = manifest.get("downstream_binding", {})
    expected_binding = {
        "required_version": identity["version"],
        "required_crosswalk_sha256": identity["crosswalk_sha256"],
        "fail_on_mismatch": True,
        "allowed_identity_edge": identity["allowed_edge"],
        "tiber_canonical_player_id_edge_authorized": False,
    }
    if binding != expected_binding:
        raise BuildFailure(f"#237 downstream binding drifted: {binding}")

    if assertions.get("status") != "candidate_input_fixture_not_governed_authority":
        raise BuildFailure("source assertions were upgraded beyond candidate authority")
    if assertions.get("scope", {}).get("promotion_authorized") is not False:
        raise BuildFailure("source assertions unexpectedly authorize promotion")


def _usage_temporal() -> dict[str, Any]:
    return {
        "effective_at": None,
        "effective_period": {"season": 2022, "season_type": "REG"},
        "source_available_at": None,
        "source_updated_at": None,
        "known_by_cutoff": None,
        "knowledge_basis": "source_timing_unavailable",
    }


def _missing_temporal() -> dict[str, Any]:
    return {
        "effective_at": None,
        "effective_period": None,
        "source_available_at": None,
        "source_updated_at": None,
        "known_by_cutoff": None,
        "knowledge_basis": "not_applicable_missing_group",
    }


def _draft_temporal() -> dict[str, Any]:
    return {
        "effective_at": None,
        "effective_period": None,
        "source_available_at": None,
        "source_updated_at": None,
        "known_by_cutoff": True,
        "knowledge_basis": "draft_selection_ordinal_at_configured_cutoff",
    }


def _unavailable_group(reason: str) -> dict[str, Any]:
    return {
        "row_kind": "observation",
        "support_status": "unavailable",
        "needs_verification": True,
        "value": None,
        "records": [],
        "temporal": _missing_temporal(),
        "source_ref_ids": [],
        "missing_reason": reason,
    }


def _vacated_opportunity() -> dict[str, Any]:
    return {
        "row_kind": "deterministic_derivation",
        "support_status": "blocked_missing_cutoff_transaction_and_team_split_sources",
        "needs_verification": True,
        "vacated_targets": None,
        "vacated_target_share": None,
        "vacated_receiving_air_yards": None,
        "vacated_routes": None,
        "vacated_snaps": None,
        "calculation_method": (
            "sum exact team-split prior-season opportunity only for source-verified "
            "departures with effective_at on or before context_cutoff"
        ),
        "components": [],
        "temporal": _missing_temporal(),
        "source_ref_ids": [],
        "missing_reason": (
            "No cutoff-bounded transaction feed exists, and full-season multi-team usage "
            "cannot be allocated to a team. Routes and snaps are null in the governed source."
        ),
    }


def _source_registry(
    assertions: dict[str, Any], pilot: dict[str, Any]
) -> list[dict[str, Any]]:
    identity = assertions["identity_dependency"]
    crosswalk_ref = {
        **identity,
        "path": identity["crosswalk_path"],
        "git_blob": identity["crosswalk_git_blob"],
        "sha256": identity["crosswalk_sha256"],
    }
    manifest_ref = {
        **identity,
        "path": identity["manifest_path"],
        "git_blob": identity["manifest_git_blob"],
        "sha256": identity["manifest_sha256"],
    }
    player = assertions["player_season_source"]
    origin = assertions["player_season_origin_candidate"]
    cutoff = pilot["cutoff_reference"]
    return [
        _source_ref(
            source_ref_id="issue-237-crosswalk-candidate",
            ref=crosswalk_ref,
            role="exact GSIS identity spine and 2023 draft assignment",
            authority="candidate_dependency_not_promoted",
        ),
        _source_ref(
            source_ref_id="issue-237-crosswalk-manifest",
            ref=manifest_ref,
            role="version and content-hash consumer binding",
            authority="candidate_dependency_not_promoted",
        ),
        _source_ref(
            source_ref_id=player["source_id"],
            ref=player,
            role="2022 REG player-season production and usage observations",
            authority=player["consumer_boundary"],
            observed_at=origin["observed_at"],
            source_updated_at=player["source_updated_at"],
        ),
        _source_ref(
            source_ref_id=origin["source_id"],
            ref=origin,
            role="source-method and team-context semantics",
            authority=origin["team_context_semantics"],
            observed_at=origin["observed_at"],
            source_updated_at=origin["source_updated_at"],
        ),
        _source_ref(
            source_ref_id=f"rookies-pilot-cutoff-reference-{pilot['canonical_team'].lower()}",
            ref=cutoff,
            role="configured pilot cutoff comparison reference only",
            authority=cutoff["authority"],
        ),
    ]


def _decimal_sum(rows: list[dict[str, Any]], field: str) -> float:
    total = sum((Decimal(str(row[field])) for row in rows), start=Decimal("0"))
    return float(total.quantize(Decimal("0.0001")))


def _candidate_usage_rows(
    records: list[dict[str, Any]], raw_team: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matching = [
        row
        for row in records
        if row.get("season") == 2022
        and row.get("season_type") == "REG"
        and raw_team in row.get("teams", [])
        and isinstance(row.get("usage_summary", {}).get("targets"), int)
        and row["usage_summary"]["targets"] > 0
    ]
    known_single_team = [row for row in matching if row.get("teams") == [raw_team]]
    multi_team = [row for row in matching if row.get("teams") != [raw_team]]

    projected: list[dict[str, Any]] = []
    for row in sorted(
        known_single_team,
        key=lambda item: (-item["usage_summary"]["targets"], item["player_id"]),
    ):
        usage = row["usage_summary"]
        receiving = row["production_summary"]["receiving"]
        required_values = {
            "receptions": usage.get("receptions"),
            "receiving_yards": receiving.get("receiving_yards"),
            "receiving_tds": receiving.get("receiving_tds"),
            "receiving_air_yards": usage.get("receiving_air_yards"),
            "target_share": usage.get("target_share"),
            "air_yards_share": usage.get("air_yards_share"),
        }
        if any(value is None for value in required_values.values()):
            raise BuildFailure(f"2022 usage row {row['player_id']} lacks required candidate values")
        projected.append(
            {
                "row_kind": "observation",
                "support_status": "source_backed_candidate_timing_unproven",
                "needs_verification": True,
                "admitted_to_reconstruction": False,
                "roster_or_depth_inference_allowed": False,
                "source_record_key": {
                    "player_id": row["player_id"],
                    "season": 2022,
                    "season_type": "REG",
                },
                "player_id": row["player_id"],
                "player_name_audit_only": row["player_name"],
                "position": row["position"],
                "raw_teams": row["teams"],
                "targets": usage["targets"],
                **required_values,
                "temporal": _usage_temporal(),
                "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
            }
        )

    excluded = [
        {
            "player_id": row["player_id"],
            "player_name_audit_only": row["player_name"],
            "raw_teams": row["teams"],
            "full_season_targets": row["usage_summary"]["targets"],
            "exclusion_reason": "full_season_usage_not_split_across_teams",
            "admitted_to_team_values": False,
            "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
        }
        for row in sorted(multi_team, key=lambda item: item["player_id"])
    ]
    return projected, excluded


def _identity_projection(
    crosswalk_row: dict[str, Any], pilot: dict[str, Any]
) -> dict[str, Any]:
    core = crosswalk_row["core_identity"]
    if crosswalk_row["crosswalk_row_id"] != pilot["crosswalk_row_id"]:
        raise BuildFailure(f"crosswalk row mismatch for {pilot['pilot_id']}")
    if core["gsis_id"] != pilot["gsis_id"] or core["rookies_slug"] != pilot["rookies_slug"]:
        raise BuildFailure(f"identity assertion mismatch for {pilot['pilot_id']}")
    if core["tiber_data_source_player_id"] != core["gsis_id"]:
        raise BuildFailure(f"pilot lacks exact-GSIS Data source-player edge: {pilot['pilot_id']}")
    if core["tiber_canonical_player_id"] is not None:
        raise BuildFailure(f"pilot unexpectedly has a governed TIBER canonical ID: {pilot['pilot_id']}")
    if crosswalk_row["draft_team"]["canonical_code"] != pilot["canonical_team"]:
        raise BuildFailure(f"pilot draft team mismatches #237: {pilot['pilot_id']}")
    return {
        "crosswalk_row_id": crosswalk_row["crosswalk_row_id"],
        "gsis_id": core["gsis_id"],
        "rookies_slug": core["rookies_slug"],
        "rookies_slug_status": core["rookies_slug_status"],
        "tiber_data_source_player_id": core["tiber_data_source_player_id"],
        "tiber_canonical_player_id": None,
        "display_name_join_used": False,
    }


def _missingness(pilot: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [
        (
            "observations.returning_inventory.value",
            "no_cutoff_bounded_roster_or_transaction_source",
        ),
        (
            "observations.vacated_opportunity.vacated_targets",
            "no_complete_departure_and_team_split_inputs",
        ),
        ("observations.offseason_chronology.value", "no_immutable_dated_transaction_feed"),
        ("observations.roster_at_cutoff.value", "no_april_2023_roster_snapshot"),
        ("observations.quarterback_state.value", "no_cutoff_bounded_qb_state_source"),
        (
            "observations.coaching_play_caller_state.value",
            "no_cutoff_bounded_coaching_source",
        ),
        (
            "observations.prior_season_offense_quality.value",
            "no_2022_team_environment_source",
        ),
        ("observations.injury_availability.value", "no_cutoff_bounded_availability_source"),
        (
            "observations.prior_season_usage.complete_team_totals",
            "player_season_rows_are_not_complete_team_or_team_split_aggregates",
        ),
        ("observations.prior_season_usage.routes_run", "source_field_unavailable"),
        ("observations.prior_season_usage.snap_share", "source_field_unavailable"),
        ("observations.prior_season_usage.route_participation", "source_field_unavailable"),
        ("observations.prior_season_usage.red_zone_targets", "source_field_unavailable"),
        ("observations.prior_season_usage.red_zone_carries", "source_field_unavailable"),
        (
            "observations.prior_season_usage.temporal.known_by_cutoff",
            "source_release_and_revision_timestamp_unavailable",
        ),
    ]
    if pilot["prior_season_team_binding_status"].startswith("blocked"):
        entries.append(
            (
                "context.team.prior_season_bound_canonical_code",
                "2022_LA_to_LAR_alias_not_authorized_by_issue_237",
            )
        )
    return [
        {
            "field_path": field_path,
            "reason_code": reason,
            "value_state": "null_or_empty_never_zero_filled",
            "source_ref_ids": [],
        }
        for field_path, reason in entries
    ]


def build_pilot(
    *,
    assertions: dict[str, Any],
    pilot: dict[str, Any],
    crosswalk_row: dict[str, Any],
    player_records: list[dict[str, Any]],
    source_assertions_sha: str,
    schema_sha: str,
) -> dict[str, Any]:
    identity = assertions["identity_dependency"]
    subject = _identity_projection(crosswalk_row, pilot)
    known_rows, excluded_rows = _candidate_usage_rows(
        player_records, pilot["prior_season_source_team_raw"]
    )
    binding_blocked = pilot["prior_season_team_binding_status"].startswith("blocked")
    usage_status = (
        "blocked_team_alias_and_source_timing_unproven"
        if binding_blocked
        else "candidate_partial_rows_source_timing_unproven"
    )
    source_refs = _source_registry(assertions, pilot)

    draft_team = crosswalk_row["draft_team"]
    payload = {
        "artifact": f"historical_landing_context_2023_{pilot['canonical_team'].lower()}_candidate",
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_partial_evidence_not_promoted",
        "issue": "Prometheus-Frameworks/TIBER-Data#236",
        "generated_at": GENERATED_AT,
        "promotion_authorized": False,
        "context": {
            "season": 2023,
            "prior_season": 2022,
            "effective_at": pilot["context_cutoff"],
            "context_cutoff": pilot["context_cutoff"],
            "cutoff_precision": pilot["cutoff_precision"],
            "same_day_admission_policy": (
                "draft_selection_ordinal_only_no_external_same_day_fact_without_sequence_evidence"
            ),
            "historical_mode": "as_known_at_cutoff",
            "known_by_cutoff": True,
            "team": {
                "canonical_code": pilot["canonical_team"],
                "draft_source_raw_code": draft_team["raw_code"],
                "prior_season_source_raw_code": pilot["prior_season_source_team_raw"],
                "prior_season_team_binding_status": pilot[
                    "prior_season_team_binding_status"
                ],
                "prior_season_bound_canonical_code": (
                    None if binding_blocked else pilot["canonical_team"]
                ),
                "prior_season_normalization_applied": False,
            },
            "subject": subject,
        },
        "identity_binding": {
            "crosswalk_version": identity["version"],
            "crosswalk_path": identity["crosswalk_path"],
            "crosswalk_sha256": identity["crosswalk_sha256"],
            "manifest_path": identity["manifest_path"],
            "manifest_sha256": identity["manifest_sha256"],
            "allowed_edge": identity["allowed_edge"],
            "tiber_canonical_player_id_edge_authorized": False,
            "projection_policy": (
                "identity_spine_and_2023_draft_fields_only_no_history_or_forecast_context"
            ),
        },
        "source_registry": source_refs,
        "observations": {
            "draft_assignment": {
                "row_kind": "observation",
                "support_status": "candidate_source_asserted",
                "needs_verification": False,
                "overall_pick": crosswalk_row["overall_pick"],
                "canonical_team": draft_team["canonical_code"],
                "raw_team_code": draft_team["raw_code"],
                "temporal": _draft_temporal(),
                "source_ref_ids": [
                    "issue-237-crosswalk-candidate",
                    f"rookies-pilot-cutoff-reference-{pilot['canonical_team'].lower()}",
                ],
            },
            "prior_season_usage": {
                "row_kind": "observation",
                "support_status": usage_status,
                "needs_verification": True,
                "source_team_raw_code": pilot["prior_season_source_team_raw"],
                "team_binding_status": pilot["prior_season_team_binding_status"],
                "normalization_applied": False,
                "complete_team_distribution": False,
                "complete_team_totals": {
                    "targets": None,
                    "target_share": None,
                    "receiving_air_yards": None,
                    "air_yards_share": None,
                    "receiving_yards": None,
                    "receiving_tds": None,
                },
                "routes_run": None,
                "snap_share": None,
                "route_participation": None,
                "red_zone_targets": None,
                "red_zone_carries": None,
                "known_single_team_rows": known_rows,
                "excluded_multi_team_rows": excluded_rows,
                "temporal": _usage_temporal(),
                "source_ref_ids": [
                    "tiber-data-player-season-coverage-v0-promoted",
                    "tiber-data-player-season-coverage-2022-2025-origin-candidate",
                ],
            },
            "returning_inventory": _unavailable_group(
                "Prior-season production is not roster membership or a depth chart, and no "
                "cutoff-bounded April 2023 roster/transaction source is held."
            ),
            "vacated_opportunity": _vacated_opportunity(),
            "offseason_chronology": _unavailable_group(
                "No admissible April 2023 cutoff-bounded transaction feed is held; "
                "wrong-year and fixture-only lanes are inventory evidence only."
            ),
            "roster_at_cutoff": _unavailable_group(
                "The repository has a roster contract but no April 2023 as-of roster artifact."
            ),
            "quarterback_state": _unavailable_group(
                "Player-season production cannot establish starter hierarchy, contract state, or health."
            ),
            "coaching_play_caller_state": _unavailable_group(
                "No cutoff-bounded coaching or play-caller source is held."
            ),
            "prior_season_offense_quality": _unavailable_group(
                "No governed 2022 team offense, pace, personnel, or scoring artifact is held."
            ),
            "injury_availability": _unavailable_group(
                "No cutoff-bounded injury/availability feed is held; games played is not a health state."
            ),
        },
        "deterministic_derivations": {
            "known_single_team_rows_subtotal": {
                "row_kind": "deterministic_derivation",
                "status": "candidate_diagnostic_only",
                "row_count": len(known_rows),
                "targets": sum(row["targets"] for row in known_rows),
                "target_share_sum": _decimal_sum(known_rows, "target_share"),
                "air_yards_share_sum": _decimal_sum(known_rows, "air_yards_share"),
                "admitted_to_reconstruction": False,
                "completeness": "partial_single_team_player_season_rows_not_a_team_total",
                "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
            }
        },
        "interpretations": {
            "status": "not_in_scope_design_and_evidence_only",
            "records": [],
        },
        "missingness": _missingness(pilot),
        "reproducibility": {
            "deterministic": True,
            "builder_command": "python3 scripts/build_historical_landing_context_2023_pilots.py",
            "validator_command": (
                "python3 scripts/validate_historical_landing_context_2023_pilots.py --report "
                "--data-repo-root . --rookies-repo-root ../TIBER-Rookies"
            ),
            "source_assertions_path": SOURCE_ASSERTIONS_PATH.as_posix(),
            "source_assertions_sha256": source_assertions_sha,
            "schema_path": SCHEMA_PATH.as_posix(),
            "schema_sha256": schema_sha,
        },
        "open_questions": assertions["open_questions"],
    }
    return payload


def source_family_assessments() -> list[dict[str, Any]]:
    return [
        {
            "family": "prior_season_targets_shares_air_yards_and_receiving",
            "status": "player_rows_available_but_cutoff_timing_and_team_completeness_unproven",
            "admitted_value_scope": "none_in_this_design_evidence_candidate",
            "candidate_evidence_scope": (
                "verbatim single-team 2022 REG player-season rows with nonzero targets"
            ),
            "source_ref_ids": [
                "tiber-data-player-season-coverage-v0-promoted",
                "tiber-data-player-season-coverage-2022-2025-origin-candidate",
            ],
        },
        {
            "family": "vacated_targets_and_receiving_opportunity",
            "status": "blocked_no_cutoff_transaction_feed_or_team_split_usage",
            "admitted_value_scope": "none_all_totals_null",
            "candidate_evidence_scope": "individual usage components only; no departure state",
            "source_ref_ids": ["tiber-data-player-season-coverage-v0-promoted"],
        },
        {
            "family": "draft_day_roster_or_depth_chart",
            "status": "unavailable_no_april_2023_cutoff_historical_roster_artifact",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": (
                "wrong-year fixture, source-backed 2025, and provisional current-state "
                "lanes are inventoried but inadmissible; prior-season usage is not a roster substitute"
            ),
            "source_ref_ids": [],
        },
        {
            "family": "offseason_arrivals_and_departures",
            "status": "unavailable_no_admissible_april_2023_cutoff_bounded_transaction_feed",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": (
                "the immutable 2026 fixture lane and event contract are inventoried but "
                "inadmissible; frozen Rookies URLs remain comparison-only"
            ),
            "source_ref_ids": [],
        },
        {
            "family": "quarterback_state",
            "status": "unavailable_production_does_not_establish_cutoff_state",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": "none",
            "source_ref_ids": [],
        },
        {
            "family": "coaching_and_play_caller_state",
            "status": "unavailable_no_cutoff_bounded_source",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": "none",
            "source_ref_ids": [],
        },
        {
            "family": "prior_season_offense_quality_volume_personnel_and_scoring",
            "status": "unavailable_no_2022_team_environment_artifact",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": "player rows cannot be promoted to team totals",
            "source_ref_ids": [],
        },
        {
            "family": "injury_and_availability",
            "status": "unavailable_no_cutoff_bounded_availability_source",
            "admitted_value_scope": "none",
            "candidate_evidence_scope": "games played cannot be used as injury state",
            "source_ref_ids": [],
        },
        {
            "family": "draft_results_and_team_assignment",
            "status": "bounded_candidate_available_via_issue_237_exact_gsis_projection",
            "admitted_value_scope": "three pilot identities, overall picks, and draft teams",
            "candidate_evidence_scope": "TIBER canonical IDs remain null",
            "source_ref_ids": [
                "issue-237-crosswalk-candidate",
                "issue-237-crosswalk-manifest",
            ],
        },
    ]


def build_source_report(
    assertions: dict[str, Any], pilots: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    findings = []
    for team in sorted(pilots):
        artifact = pilots[team]
        usage = artifact["observations"]["prior_season_usage"]
        subtotal = artifact["deterministic_derivations"]["known_single_team_rows_subtotal"]
        findings.append(
            {
                "canonical_team": team,
                "context_cutoff": artifact["context"]["context_cutoff"],
                "prior_season_source_raw_code": usage["source_team_raw_code"],
                "team_binding_status": usage["team_binding_status"],
                "known_single_team_row_count": subtotal["row_count"],
                "known_single_team_target_subtotal": subtotal["targets"],
                "known_single_team_target_share_sum": subtotal["target_share_sum"],
                "known_single_team_air_yards_share_sum": subtotal["air_yards_share_sum"],
                "excluded_multi_team_row_count": len(usage["excluded_multi_team_rows"]),
                "complete_team_distribution": False,
                "prior_usage_known_by_cutoff": None,
                "admitted_to_reconstruction": False,
                "artifact_path": PILOT_OUTPUT_PATHS[team].as_posix(),
                "source_ref_ids": [
                    "issue-237-crosswalk-candidate",
                    "tiber-data-player-season-coverage-v0-promoted",
                    "tiber-data-player-season-coverage-2022-2025-origin-candidate",
                ],
            }
        )

    return {
        "artifact_id": "historical_landing_context_2023_source_availability_gap_report",
        "report_version": "0.1.0",
        "status": "design_and_evidence_gap_report_not_a_terminal_decision",
        "issue": "Prometheus-Frameworks/TIBER-Data#236",
        "generated_at": GENERATED_AT,
        "scope": {
            "pilot_teams": ["BAL", "IND", "LAR"],
            "context_season": 2023,
            "prior_season": 2022,
            "cutoff_mode": "configured_end_of_selection_day_proxy_with_same_day_ordinal_firewall",
            "ownership_decision_reserved_for_operator": True,
            "promotion_authorized": False,
        },
        "bounded_discovery_method": {
            "repository": "Prometheus-Frameworks/TIBER-Data",
            "method": (
                "inspect tracked candidate/promoted artifacts and contracts whose paths or metadata "
                "claim roster, opportunity, team context, usage, offense, personnel, availability, "
                "or draft-result semantics; compare their explicit season/source scope to April 2023"
            ),
            "not_a_claim": "not a full external-source census or transitive cross-repo ownership decision",
        },
        "source_registry": [
            ref
            for ref in pilots["BAL"]["source_registry"]
            if not ref["source_ref_id"].startswith("rookies-pilot-cutoff-reference-")
        ],
        "source_families": source_family_assessments(),
        "pilot_findings": findings,
        "bounded_repository_inventory": assertions["bounded_repository_inventory"],
        "pinned_frozen_rookies_comparison_references": [
            {
                "canonical_team": pilot["canonical_team"],
                "context_cutoff": pilot["context_cutoff"],
                **pilot["cutoff_reference"],
            }
            for pilot in assertions["pilots"]
        ],
        "frozen_rookies_reference_audit": assertions["frozen_reference_audit"],
        "hindsight_firewall": {
            "later_crosswalk_history_projected": False,
            "forecast_metadata_projected": False,
            "post_cutoff_puka_kupp_source_admitted": False,
            "same_day_external_fact_without_sequence_evidence_admitted": False,
            "modern_source_observation_timestamp_treated_as_fact_effective_at": False,
        },
        "open_questions": assertions["open_questions"],
    }


def render_source_report(report: dict[str, Any]) -> str:
    lines = [
        "# Historical landing-context 2023 source availability and gap report",
        "",
        "Status: design/evidence report only. It makes no ownership or terminal decision and "
        "authorizes no promotion.",
        "",
        "## Answer first",
        "",
        "The bounded repository audit found only two usable evidence lanes: the #237 exact-GSIS "
        "identity/draft projection and individual 2022 REG player-season usage rows. The latter "
        "remain unadmitted because their immutable lineage has no contemporaneous release or "
        "revision timestamp. Complete team distributions, returning/depth inventory, vacated "
        "opportunity, transactions, quarterback/coaching state, 2022 team environment, and "
        "injury/availability remain explicit gaps.",
        "",
        "## Required source families",
        "",
        "| Family | Bounded status | Admitted scope |",
        "| --- | --- | --- |",
    ]
    for item in report["source_families"]:
        lines.append(
            f"| `{item['family']}` | `{item['status']}` | {item['admitted_value_scope']} |"
        )
    lines.extend(
        [
            "",
            "## Pilot evidence",
            "",
            "The subtotals below are diagnostics over source rows whose full-season `teams` value "
            "contains exactly one team. They are not complete team totals and are not admitted to "
            "the reconstructed layer.",
            "",
            "| Team | Raw 2022 code | Binding | Rows | Target subtotal | Target-share sum | "
            "Air-yards-share sum | Multi-team exclusions |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in report["pilot_findings"]:
        lines.append(
            f"| {item['canonical_team']} | `{item['prior_season_source_raw_code']}` | "
            f"`{item['team_binding_status']}` | {item['known_single_team_row_count']} | "
            f"{item['known_single_team_target_subtotal']} | "
            f"{item['known_single_team_target_share_sum']:.4f} | "
            f"{item['known_single_team_air_yards_share_sum']:.4f} | "
            f"{item['excluded_multi_team_row_count']} |"
        )
    lines.extend(
        [
            "",
            "`LA` is preserved for the 2022 Rams source rows. #237 authorizes its directed "
            "`LA → LAR` candidate rule only for source seasons 2023–2025, so the LAR prior-season "
            "team binding remains blocked here.",
            "",
            "## Hindsight and aggregation firewall",
            "",
            "- No #237 later-season team history or Forecast metadata is projected.",
            "- No 2022 player-season row is treated as a returning roster/depth fact.",
            "- Multi-team full-season rows are excluded from the diagnostic team subtotals.",
            "- Complete team totals and vacated opportunity remain null; rows are never renormalized.",
            "- The frozen Puka comparison reference's June 2023 Kupp source is explicitly excluded.",
            "- End-of-day cutoffs are configured proxies; same-day external facts require sequence "
            "evidence and none are admitted by these pilots.",
            "",
            "## Bounded negative inventory",
            "",
            "| Claimed family | Path | Observed scope | April 2023 use | SHA-256 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["bounded_repository_inventory"]:
        lines.append(
            f"| `{item['source_family']}` | `{item['path']}` | {item['observed_scope']} | "
            f"`{item['april_2023_admissibility']}` | `{item['sha256']}` |"
        )
    lines.extend(["", "## Open operator questions", ""])
    for question in report["open_questions"]:
        lines.append(f"- {question}")
    lines.extend(
        [
            "",
            "The cross-repo ownership split and all terminal decisions are intentionally reserved "
            "for the operator.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    assertions_raw = (ROOT / SOURCE_ASSERTIONS_PATH).read_bytes()
    assertions = json.loads(assertions_raw)
    verify_local_inputs(assertions)

    schema_raw = (ROOT / SCHEMA_PATH).read_bytes()
    schema = json.loads(schema_raw)
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )

    crosswalk = load_json(CROSSWALK_PATH)
    player_source = load_json(PLAYER_SEASON_PATH)
    if player_source.get("season_type_scope") != ["REG"]:
        raise BuildFailure("player-season source scope is not REG-only")
    records = player_source.get("records")
    if not isinstance(records, list):
        raise BuildFailure("player-season source records are missing")

    by_gsis = {
        row["core_identity"]["gsis_id"]: row
        for row in crosswalk.get("records", [])
        if isinstance(row, dict) and isinstance(row.get("core_identity"), dict)
    }
    pilots: dict[str, dict[str, Any]] = {}
    for pilot in assertions["pilots"]:
        row = by_gsis.get(pilot["gsis_id"])
        if row is None:
            raise BuildFailure(f"#237 row missing for {pilot['gsis_id']}")
        payload = build_pilot(
            assertions=assertions,
            pilot=pilot,
            crosswalk_row=row,
            player_records=records,
            source_assertions_sha=sha256(assertions_raw),
            schema_sha=sha256(schema_raw),
        )
        schema_errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if schema_errors:
            first = schema_errors[0]
            path = "/".join(str(part) for part in first.absolute_path) or "<root>"
            raise BuildFailure(f"generated {pilot['pilot_id']} fails schema at {path}: {first.message}")
        pilots[pilot["canonical_team"]] = payload

    if set(pilots) != {"BAL", "IND", "LAR"}:
        raise BuildFailure(f"pilot teams drifted: {sorted(pilots)}")

    report = build_source_report(assertions, pilots)
    report_json_raw = serialize(report)
    report_md_raw = render_source_report(report).encode("utf-8")

    outputs: dict[Path, bytes] = {
        PILOT_OUTPUT_PATHS[team]: serialize(payload) for team, payload in pilots.items()
    }
    outputs[SOURCE_REPORT_JSON_PATH] = report_json_raw
    outputs[SOURCE_REPORT_MD_PATH] = report_md_raw

    manifest = {
        "artifact_id": "historical_landing_context_2023_pilot_bundle_v0.1.0",
        "status": "candidate_bundle_not_promoted",
        "issue": "Prometheus-Frameworks/TIBER-Data#236",
        "generated_at": GENERATED_AT,
        "promotion_authorized": False,
        "schema": {
            "version": SCHEMA_VERSION,
            "path": SCHEMA_PATH.as_posix(),
            "sha256": sha256(schema_raw),
            "governed_contract": False,
        },
        "source_assertions": {
            "path": SOURCE_ASSERTIONS_PATH.as_posix(),
            "sha256": sha256(assertions_raw),
            "authority": "candidate_input_fixture_not_governed_authority",
        },
        "identity_dependency": {
            "version": assertions["identity_dependency"]["version"],
            "crosswalk_path": assertions["identity_dependency"]["crosswalk_path"],
            "crosswalk_sha256": assertions["identity_dependency"]["crosswalk_sha256"],
            "manifest_path": assertions["identity_dependency"]["manifest_path"],
            "manifest_sha256": assertions["identity_dependency"]["manifest_sha256"],
            "allowed_edge": assertions["identity_dependency"]["allowed_edge"],
            "tiber_canonical_player_id_edge_authorized": False,
        },
        "pilot_artifacts": [
            {
                "canonical_team": team,
                "path": PILOT_OUTPUT_PATHS[team].as_posix(),
                "sha256": sha256(outputs[PILOT_OUTPUT_PATHS[team]]),
                "context_cutoff": pilots[team]["context"]["context_cutoff"],
                "status": pilots[team]["status"],
            }
            for team in sorted(pilots)
        ],
        "source_availability_report": {
            "json_path": SOURCE_REPORT_JSON_PATH.as_posix(),
            "json_sha256": sha256(report_json_raw),
            "markdown_path": SOURCE_REPORT_MD_PATH.as_posix(),
            "markdown_sha256": sha256(report_md_raw),
        },
        "consumer_boundary": {
            "design_and_evidence_only": True,
            "interpretations_authorized": False,
            "ownership_decision_made": False,
            "identity_edge": "gsis_to_tiber_data_source_player_id",
            "full_team_totals_ready": False,
            "returning_inventory_ready": False,
            "vacated_opportunity_ready": False,
        },
        "open_questions": assertions["open_questions"],
    }
    outputs[MANIFEST_PATH] = serialize(manifest)
    return outputs


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for path in sorted(outputs, key=lambda item: item.as_posix()):
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(outputs[path])
        print(f"wrote {path}")


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    counts = Counter(path.parent.as_posix() for path in outputs)
    print(f"built {len(PILOT_OUTPUT_PATHS)} pilots and {len(outputs)} outputs: {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
