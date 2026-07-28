"""Build deterministic #228 generic full-PPR scoring reconciliation evidence.

This script is deliberately read-only with respect to the promoted
``player_season_coverage_v0`` source. It verifies the exact promoted bytes and
promotion manifest, computes the issue-approved generic PPR profile only from
the eight explicitly governed component fields, and preserves the promoted
``season_ppr`` value as a comparator.

The promoted total is never rewritten or reverse-engineered. Rows with a
different source total remain visible in the discrepancy ledger.

Reproduce:
    python3 scripts/reconcile_player_season_coverage_ppr_v1.py

Verify committed outputs without writing:
    python3 scripts/reconcile_player_season_coverage_ppr_v1.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"
SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json"
)

CONTRACT_PATH = (
    REPO_ROOT / "docs/contracts/player-season-coverage-v0-generic-ppr-reconciliation-v1.json"
)
RECONCILIATION_PATH = (
    REPO_ROOT
    / "exports/candidates/scoring_reconciliation/"
    "player_season_coverage_v0_generic_ppr_reconciliation_v1.json"
)
DISCREPANCY_PATH = (
    REPO_ROOT
    / "exports/candidates/scoring_reconciliation/"
    "player_season_coverage_v0_generic_ppr_discrepancies_v1.json"
)
MISSINGNESS_PATH = (
    REPO_ROOT
    / "exports/candidates/scoring_reconciliation/"
    "player_season_coverage_v0_generic_ppr_missingness_v1.json"
)
REPORT_PATH = (
    REPO_ROOT / "docs/reports/player-season-coverage-v0-generic-ppr-reconciliation-v1.md"
)
EVIDENCE_MANIFEST_PATH = (
    REPO_ROOT
    / "data/manifests/player_season_coverage_v0_generic_ppr_reconciliation_v1.manifest.json"
)

SOURCE_SHA256 = "d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac"
SOURCE_MANIFEST_SHA256 = (
    "5e9a382db0681e7a808a1d5fdf4334653cf2f0b26314c45425b333aa2024d154"
)
SOURCE_REPOSITORY_COMMIT = "31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5"
SOURCE_CANDIDATE_SHA256 = (
    "c92404a1b519a62ee9f4b75f74662157fc8dd02b883648d4cdae694d0e021424"
)
SOURCE_RECORD_COUNT = 3016
SOURCE_SEASONS = (2021, 2022, 2023, 2024, 2025)
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
VALID_REGULAR_SEASON_WEEKS = tuple(range(1, 19))
GENERATED_AT = "2026-07-27T23:28:38Z"

NFLFASTR_SEMANTICS_COMMIT = "0489133d85c5f11682572d9436c4a7b371a789aa"
NFLFASTR_SEMANTICS_BLOB = "c54e875f9898ef9a4bbd5e7dd879c6e3c2abbc0a"
NFLFASTR_SEMANTICS_PATH = "R/aggregate_game_stats.R"
NFLFASTR_SEMANTICS_URL = (
    "https://github.com/nflverse/nflfastR/blob/"
    f"{NFLFASTR_SEMANTICS_COMMIT}/{NFLFASTR_SEMANTICS_PATH}"
)

MONEY_QUANTUM = Decimal("0.01")
TOLERANCE = Decimal("0.00")

SCORING_PROFILE: dict[str, Any] = {
    "profile_id": "tiber-generic-full-ppr-v1",
    "profile_version": "1.0.0",
    "league_specific": False,
    "regular_season_only": True,
    "supported_positions": list(SUPPORTED_POSITIONS),
    "bonuses": "none",
    "scoring": {
        "reception": "1",
        "receiving_yard": "0.1",
        "receiving_touchdown": "6",
        "rushing_yard": "0.1",
        "rushing_touchdown": "6",
        "passing_yard": "0.04",
        "passing_touchdown": "4",
        "interception": "-2",
    },
}

COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "name": "receptions",
        "profile_term": "reception",
        "path": ("usage_summary", "receptions"),
        "weight": Decimal("1"),
    },
    {
        "name": "receiving_yards",
        "profile_term": "receiving_yard",
        "path": ("production_summary", "receiving", "receiving_yards"),
        "weight": Decimal("0.1"),
    },
    {
        "name": "receiving_touchdowns",
        "profile_term": "receiving_touchdown",
        "path": ("production_summary", "receiving", "receiving_tds"),
        "weight": Decimal("6"),
    },
    {
        "name": "rushing_yards",
        "profile_term": "rushing_yard",
        "path": ("production_summary", "rushing", "rushing_yards"),
        "weight": Decimal("0.1"),
    },
    {
        "name": "rushing_touchdowns",
        "profile_term": "rushing_touchdown",
        "path": ("production_summary", "rushing", "rushing_tds"),
        "weight": Decimal("6"),
    },
    {
        "name": "passing_yards",
        "profile_term": "passing_yard",
        "path": ("production_summary", "passing", "passing_yards"),
        "weight": Decimal("0.04"),
    },
    {
        "name": "passing_touchdowns",
        "profile_term": "passing_touchdown",
        "path": ("production_summary", "passing", "passing_tds"),
        "weight": Decimal("4"),
    },
    {
        "name": "interceptions",
        "profile_term": "interception",
        "path": ("production_summary", "passing", "interceptions"),
        "weight": Decimal("-2"),
    },
)

RECONCILIATION_STATES = (
    "reconciled_exact",
    "reconciled_within_tolerance",
    "component_missing",
    "source_total_missing",
    "regular_season_scope_unresolved",
    "season_incomplete",
    "scoring_mismatch",
    "unsupported_position",
    "identity_unresolved",
)
COMPLETENESS_STATES = (
    "full_season",
    "partial_season",
    "single_week",
    "missing",
    "irreconcilable",
)
TERMINAL_DECISION = "scoring_reconciliation_evidence_ready"


class ReconciliationError(RuntimeError):
    """Fail-closed source or contract violation."""


def canonical_json_bytes(value: Any) -> bytes:
    """Canonical compact JSON bytes used only for immutable identity hashes."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    """Stable repository JSON serialization."""
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


PROFILE_SHA256 = sha256_bytes(canonical_json_bytes(SCORING_PROFILE))


def _load_pinned_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    if not path.is_file():
        raise ReconciliationError(f"required pinned source is missing: {path}")
    actual_sha256 = sha256_path(path)
    if actual_sha256 != expected_sha256:
        raise ReconciliationError(
            f"source drift for {path}: expected {expected_sha256}, got {actual_sha256}"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReconciliationError(f"expected JSON object at {path}")
    return value


def _path_text(path: Iterable[str]) -> str:
    return ".".join(path)


def _read_path(row: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    value: Any = row
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return False, None
        value = value[key]
    return value is not None, value


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReconciliationError(f"{field} must be a finite JSON number, got {value!r}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ReconciliationError(f"{field} is not numeric: {value!r}") from exc
    if not result.is_finite():
        raise ReconciliationError(f"{field} must be finite, got {value!r}")
    return result


def _integral_decimal(value: Any, field: str) -> Decimal:
    result = _decimal(value, field)
    if result != result.to_integral_value():
        raise ReconciliationError(
            f"{field} must be an integer-valued JSON number, got {value!r}"
        )
    return result


def _decimal_text(value: Decimal, places: int | None = None) -> str:
    if places is not None:
        value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = format(value, "f")
    if places is None and "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", "-0.00"}:
        return "0" if places is None else "0." + ("0" * places)
    return text


def _completeness(row: dict[str, Any]) -> tuple[str, list[str]]:
    weeks = row.get("weeks_observed")
    declared = row.get("coverage_status")

    if isinstance(weeks, bool) or not isinstance(weeks, int):
        return "irreconcilable", ["weeks_observed_not_integer"]
    if weeks < 0 or weeks > len(VALID_REGULAR_SEASON_WEEKS):
        return "irreconcilable", ["weeks_observed_outside_0_18"]

    if weeks == 0:
        computed = "missing"
        accepted_declared = {"none", "unknown"}
    elif weeks == 1:
        computed = "single_week"
        accepted_declared = {"single_week"}
    elif weeks < 15:
        computed = "partial_season"
        accepted_declared = {"partial_season"}
    else:
        computed = "full_season"
        accepted_declared = {"full_season"}

    if declared not in accepted_declared:
        return "irreconcilable", [
            "coverage_status_conflicts_with_weeks_observed",
            f"declared_{declared}",
            f"computed_{computed}",
        ]
    return computed, []


def evaluate_row(row: dict[str, Any], source_ordinal: int) -> dict[str, Any]:
    """Evaluate one promoted player-season row without dropping any failure."""
    player_id = row.get("player_id")
    player_name = row.get("player_name")
    identity_confidence = row.get("identity_confidence")
    season = row.get("season")
    season_type = row.get("season_type")
    position = row.get("position")

    completeness, completeness_reasons = _completeness(row)

    component_values: dict[str, str | None] = {}
    missing_components: list[str] = []
    observed_zero_components: list[str] = []
    derived_raw = Decimal("0")

    for component in COMPONENTS:
        path = component["path"]
        present, value = _read_path(row, path)
        path_text = _path_text(path)
        if not present:
            component_values[component["name"]] = None
            missing_components.append(path_text)
            continue
        numeric = _integral_decimal(value, path_text)
        component_values[component["name"]] = _decimal_text(numeric)
        if numeric == 0:
            observed_zero_components.append(component["name"])
        derived_raw += numeric * component["weight"]

    source_total_present, source_total_value = _read_path(
        row, ("production_summary", "season_ppr")
    )
    source_total: Decimal | None = None
    if source_total_present:
        source_total = _decimal(source_total_value, "production_summary.season_ppr")

    identity_resolved = (
        isinstance(player_id, str)
        and bool(player_id)
        and isinstance(player_name, str)
        and bool(player_name)
        and identity_confidence == "source_verified"
    )
    scope_resolved = (
        season in SOURCE_SEASONS
        and season_type == "REG"
        and completeness != "irreconcilable"
    )

    status: str
    reason_codes: list[str]
    signed_delta: Decimal | None = None
    absolute_delta: Decimal | None = None
    signed_delta_raw: Decimal | None = None
    absolute_delta_raw: Decimal | None = None
    derived_total: Decimal | None = None

    if position not in SUPPORTED_POSITIONS:
        status = "unsupported_position"
        reason_codes = ["position_outside_qb_rb_wr_te_scope"]
    elif not identity_resolved:
        status = "identity_unresolved"
        reason_codes = ["source_verified_identity_required"]
    elif not scope_resolved:
        status = "regular_season_scope_unresolved"
        reason_codes = completeness_reasons or ["season_or_season_type_outside_contract"]
    elif completeness == "missing":
        status = "season_incomplete"
        reason_codes = ["zero_regular_season_weeks_observed"]
    elif missing_components:
        status = "component_missing"
        reason_codes = ["required_profile_component_unavailable"]
    elif source_total is None:
        status = "source_total_missing"
        reason_codes = ["promoted_season_ppr_unavailable"]
    else:
        derived_total = derived_raw.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
        signed_delta_raw = derived_raw - source_total
        absolute_delta_raw = abs(signed_delta_raw)
        source_total_at_scale = source_total.quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_UP
        )
        signed_delta = derived_total - source_total_at_scale
        absolute_delta = abs(signed_delta)
        if signed_delta == 0:
            status = "reconciled_exact"
            reason_codes = ["candidate_profile_matches_source_total_at_cent_scale"]
        elif absolute_delta <= TOLERANCE:
            status = "reconciled_within_tolerance"
            reason_codes = ["candidate_profile_within_declared_numeric_tolerance"]
        else:
            status = "scoring_mismatch"
            reason_codes = [
                "source_total_not_equivalent_to_candidate_profile",
                "delta_not_attributable_from_promoted_component_set",
            ]

    if derived_total is None and not missing_components:
        derived_total = derived_raw.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)

    return {
        "source_row_ordinal": source_ordinal,
        "source_row_key": {
            "player_id": player_id,
            "season": season,
            "season_type": season_type,
        },
        "player_name": player_name,
        "position": position,
        "identity_status": (
            "source_verified" if identity_resolved else "identity_unresolved"
        ),
        "season_completeness": completeness,
        "week_scope": {
            "season_type": season_type,
            "weeks_observed": row.get("weeks_observed"),
            "valid_regular_season_week_numbers": "1-18_inclusive",
            "week_18_included": True,
            "per_week_numbers_present_in_promoted_row": False,
            "status": (
                "declared_regular_season_aggregate"
                if scope_resolved
                else "unresolved"
            ),
        },
        "component_values": component_values,
        "component_availability": (
            "complete" if not missing_components else "missing"
        ),
        "missing_components": missing_components,
        "observed_zero_components": sorted(observed_zero_components),
        "derived_generic_ppr": (
            _decimal_text(derived_total, places=2)
            if derived_total is not None
            else None
        ),
        "derived_generic_ppr_unrounded": (
            _decimal_text(derived_raw) if not missing_components else None
        ),
        "promoted_source_season_ppr": (
            _decimal_text(
                source_total.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP),
                places=2,
            )
            if source_total is not None
            else None
        ),
        "promoted_source_season_ppr_unrounded": (
            _decimal_text(source_total) if source_total is not None else None
        ),
        "signed_delta_derived_minus_source": (
            _decimal_text(signed_delta, places=2)
            if signed_delta is not None
            else None
        ),
        "signed_delta_derived_minus_source_unrounded": (
            _decimal_text(signed_delta_raw)
            if signed_delta_raw is not None
            else None
        ),
        "absolute_delta": (
            _decimal_text(absolute_delta, places=2)
            if absolute_delta is not None
            else None
        ),
        "absolute_delta_unrounded": (
            _decimal_text(absolute_delta_raw)
            if absolute_delta_raw is not None
            else None
        ),
        "reconciliation_status": status,
        "reason_codes": reason_codes,
    }


def _status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(row[field]) for row in rows)
    return dict(sorted(counter.items()))


def _rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00%"
    value = (Decimal(numerator) * Decimal(100) / Decimal(denominator)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{value}%"


def _group_summary(
    rows: list[dict[str, Any]], key: str
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if key == "season":
            value = str(row["source_row_key"]["season"])
        else:
            value = str(row[key])
        grouped.setdefault(value, []).append(row)

    result: dict[str, dict[str, Any]] = {}
    for value in sorted(grouped):
        group_rows = grouped[value]
        status_counts = _status_counts(group_rows, "reconciliation_status")
        conforming = status_counts.get("reconciled_exact", 0) + status_counts.get(
            "reconciled_within_tolerance", 0
        )
        result[value] = {
            "row_count": len(group_rows),
            "reconciliation_status_counts": status_counts,
            "season_completeness_counts": _status_counts(
                group_rows, "season_completeness"
            ),
            "source_total_conforming_rows": conforming,
            "source_total_mismatch_rows": status_counts.get("scoring_mismatch", 0),
            "source_total_conformance_rate": _rate(conforming, len(group_rows)),
        }
    return result


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = _status_counts(rows, "reconciliation_status")
    completeness = _status_counts(rows, "season_completeness")
    conforming = statuses.get("reconciled_exact", 0) + statuses.get(
        "reconciled_within_tolerance", 0
    )
    mismatch_rows = [
        row for row in rows if row["reconciliation_status"] == "scoring_mismatch"
    ]
    signed_deltas = [
        Decimal(row["signed_delta_derived_minus_source"]) for row in mismatch_rows
    ]

    component_missing_counts = {
        _path_text(component["path"]): sum(
            1
            for row in rows
            if _path_text(component["path"]) in row["missing_components"]
        )
        for component in COMPONENTS
    }
    observed_zero_counts = {
        component["name"]: sum(
            1
            for row in rows
            if component["name"] in row["observed_zero_components"]
        )
        for component in COMPONENTS
    }

    return {
        "row_count": len(rows),
        "reconciliation_status_counts": statuses,
        "season_completeness_counts": completeness,
        "source_total_conforming_rows": conforming,
        "source_total_mismatch_rows": statuses.get("scoring_mismatch", 0),
        "source_total_conformance_rate": _rate(conforming, len(rows)),
        "source_total_mismatch_rate": _rate(
            statuses.get("scoring_mismatch", 0), len(rows)
        ),
        "component_missing_counts": component_missing_counts,
        "source_total_missing_count": statuses.get("source_total_missing", 0),
        "observed_zero_component_counts": observed_zero_counts,
        "mismatch_delta": {
            "signed_min": (
                _decimal_text(min(signed_deltas), places=2)
                if signed_deltas
                else None
            ),
            "signed_max": (
                _decimal_text(max(signed_deltas), places=2)
                if signed_deltas
                else None
            ),
            "integer_multiple_of_two_count": sum(
                1 for delta in signed_deltas if delta % Decimal("2") == 0
            ),
            "evaluated_mismatch_count": len(signed_deltas),
        },
        "by_season": _group_summary(rows, "season"),
        "by_position": _group_summary(rows, "position"),
    }


def _source_semantics() -> dict[str, Any]:
    return {
        "promoted_field": "production_summary.season_ppr",
        "promoted_builder_declaration": (
            "nflreadpy.load_player_stats(summary_level='reg').fantasy_points_ppr "
            "is passed through directly from the nflverse season rollup"
        ),
        "candidate_profile_equivalence": "not_equivalent_for_all_rows",
        "semantic_corroboration": {
            "repository": "nflverse/nflfastR",
            "commit": NFLFASTR_SEMANTICS_COMMIT,
            "path": NFLFASTR_SEMANTICS_PATH,
            "blob_sha": NFLFASTR_SEMANTICS_BLOB,
            "url": NFLFASTR_SEMANTICS_URL,
            "observed_formula_families_outside_candidate_profile": [
                "special_teams_touchdowns",
                "passing_two_point_conversions",
                "rushing_two_point_conversions",
                "receiving_two_point_conversions",
                "sack_fumbles_lost",
                "rushing_fumbles_lost",
                "receiving_fumbles_lost",
            ],
            "provenance_limit": (
                "Current official producer code corroborates field semantics but is "
                "not claimed as the exact historical nflreadpy/nflverse release used "
                "to create the promoted source; that release was not pinned."
            ),
        },
        "interpretation_rule": (
            "A nonzero delta is preserved as scoring_mismatch. The promoted artifact "
            "does not expose the out-of-profile component families, so the net delta "
            "must not be reverse-engineered or attributed per row."
        ),
    }


def _contract() -> dict[str, Any]:
    return {
        "contract_id": "player-season-coverage-v0-generic-ppr-reconciliation-v1",
        "contract_version": "1.0.0",
        "tracking_issue": "TIBER-Data#228",
        "status": "candidate_evidence_contract_not_promoted",
        "profile": {
            "definition": SCORING_PROFILE,
            "canonical_json_rule": (
                "UTF-8 JSON; object keys sorted recursively; separators ',' and ':'; "
                "no insignificant whitespace; profile_sha256 is SHA-256 over the "
                "canonical JSON bytes of profile.definition only"
            ),
            "profile_sha256": PROFILE_SHA256,
        },
        "component_bindings": [
            {
                "component_name": component["name"],
                "profile_term": component["profile_term"],
                "source_path": _path_text(component["path"]),
                "weight": _decimal_text(component["weight"]),
                "input_type": "finite_integer_valued_json_number",
            }
            for component in COMPONENTS
        ],
        "source_scope": {
            "artifact_path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
            "artifact_sha256": SOURCE_SHA256,
            "repository_commit": SOURCE_REPOSITORY_COMMIT,
            "seasons": list(SOURCE_SEASONS),
            "season_type": "REG",
            "supported_positions": list(SUPPORTED_POSITIONS),
            "candidate_temporal_origins_covered_by_season_presence": [
                "2022_to_2023",
                "2023_to_2024",
                "2024_to_2025",
            ],
            "origin_boundary": (
                "Season presence and scoring identity only; this evidence does not "
                "define, execute, or accept any Forecast split."
            ),
        },
        "week_inclusion": {
            "valid_week_numbers": list(VALID_REGULAR_SEASON_WEEKS),
            "week_18": "included_as_regular_season",
            "malformed_or_out_of_scope_rule": (
                "A row whose season_type is not REG, whose season is outside "
                "2021-2025, or whose weeks_observed is outside 0-18 is "
                "regular_season_scope_unresolved and is not silently scored as valid."
            ),
            "source_limitation": (
                "Promoted rows expose weeks_observed counts, not individual week "
                "numbers. This evidence binds the declared REG aggregation and count "
                "range; it does not invent or independently reconstruct per-week rows."
            ),
        },
        "season_completeness": {
            "full_season": "15-18 distinct REG week numbers with a stat line",
            "partial_season": "2-14 distinct REG week numbers with a stat line",
            "single_week": "exactly 1 distinct REG week number with a stat line",
            "missing": "0 distinct REG week numbers",
            "irreconcilable": (
                "non-integer/out-of-range weeks_observed or declared coverage_status "
                "conflicting with the deterministic count rule"
            ),
            "non_inference": (
                "A missing stat-line week is not interpreted as a missed game, injury, "
                "inactive status, or roster absence."
            ),
        },
        "aggregation_precedence": {
            "candidate_profile_total": (
                "Compute from the eight governed season component fields; this is the "
                "only exact tiber-generic-full-ppr-v1 value."
            ),
            "promoted_source_total": (
                "Preserve production_summary.season_ppr as a comparator; never "
                "overwrite it or treat it as profile-equivalent when it mismatches."
            ),
            "weekly_total": (
                "No weekly scoring rows exist in the promoted source. Do not fabricate "
                "a weekly sum or use an unpinned weekly artifact as a substitute."
            ),
        },
        "numeric_rule": {
            "arithmetic": "base-10 Decimal constructed from JSON numeric text",
            "component_input_type": (
                "finite integer-valued JSON numbers; strings and booleans are rejected"
            ),
            "source_total_input_type": (
                "finite JSON number; strings and booleans are rejected"
            ),
            "published_scale": "0.01 points",
            "rounding": "ROUND_HALF_UP",
            "comparison": (
                "Quantize component-derived and source totals independently to 0.01, "
                "then compare the cent-scale values. Raw decimal values/deltas remain "
                "visible as diagnostics but never drive semantic status."
            ),
            "exact": "absolute cent-scale delta == 0.00",
            "within_tolerance": (
                "Reserved state; v1 tolerance is 0.00, so no nonzero cent-scale "
                "delta qualifies."
            ),
            "mismatch": "absolute cent-scale delta > 0.00",
            "tolerance": "0.00",
        },
        "missingness_and_zero": {
            "genuine_zero": (
                "A present numeric 0 is a governed observed zero and participates in "
                "the score; it is listed in observed_zero_components."
            ),
            "unavailable": (
                "A missing key or JSON null is unavailable, remains null, and yields "
                "component_missing; no unavailable component is zero-filled."
            ),
            "source_total_unavailable": (
                "A missing/null production_summary.season_ppr yields "
                "source_total_missing and is not reconstructed."
            ),
        },
        "reconciliation_states": list(RECONCILIATION_STATES),
        "reconciliation_status_contract": {
            "validation_precondition": (
                "Before status selection, governed component and source-total values "
                "must satisfy numeric_rule. A malformed numeric type, non-finite "
                "value, or non-integral component is a build-stopping contract "
                "violation; it is not converted into a row status."
            ),
            "selection_rule": (
                "Evaluate ordered_precedence from lowest order to highest and emit "
                "the first matching status. The final three delta states apply only "
                "after all eligibility, completeness, component, and source-total "
                "conditions pass."
            ),
            "ordered_precedence": [
                {
                    "order": 1,
                    "condition": "position is outside QB/RB/WR/TE",
                    "status": "unsupported_position",
                    "reason_codes": ["position_outside_qb_rb_wr_te_scope"],
                },
                {
                    "order": 2,
                    "condition": (
                        "player_id/player_name is missing or identity_confidence is "
                        "not source_verified"
                    ),
                    "status": "identity_unresolved",
                    "reason_codes": ["source_verified_identity_required"],
                },
                {
                    "order": 3,
                    "condition": (
                        "season is outside 2021-2025, season_type is not REG, or "
                        "season completeness is irreconcilable"
                    ),
                    "status": "regular_season_scope_unresolved",
                    "reason_codes": [
                        "weeks_observed_not_integer",
                        "weeks_observed_outside_0_18",
                        "coverage_status_conflicts_with_weeks_observed",
                        "declared_<coverage_status>",
                        "computed_<season_completeness>",
                        "season_or_season_type_outside_contract",
                    ],
                },
                {
                    "order": 4,
                    "condition": "weeks_observed is 0",
                    "status": "season_incomplete",
                    "reason_codes": ["zero_regular_season_weeks_observed"],
                },
                {
                    "order": 5,
                    "condition": "one or more governed component paths is null or absent",
                    "status": "component_missing",
                    "reason_codes": ["required_profile_component_unavailable"],
                },
                {
                    "order": 6,
                    "condition": "production_summary.season_ppr is null or absent",
                    "status": "source_total_missing",
                    "reason_codes": ["promoted_season_ppr_unavailable"],
                },
                {
                    "order": 7,
                    "condition": "signed cent-scale derived-minus-source delta is 0.00",
                    "status": "reconciled_exact",
                    "reason_codes": [
                        "candidate_profile_matches_source_total_at_cent_scale"
                    ],
                },
                {
                    "order": 8,
                    "condition": (
                        "signed cent-scale delta is nonzero and absolute delta is at "
                        "most tolerance; reserved and unreachable while tolerance is 0.00"
                    ),
                    "status": "reconciled_within_tolerance",
                    "reason_codes": [
                        "candidate_profile_within_declared_numeric_tolerance"
                    ],
                },
                {
                    "order": 9,
                    "condition": "absolute cent-scale delta exceeds tolerance",
                    "status": "scoring_mismatch",
                    "reason_codes": [
                        "source_total_not_equivalent_to_candidate_profile",
                        "delta_not_attributable_from_promoted_component_set",
                    ],
                },
            ],
            "status_definitions": {
                "reconciled_exact": (
                    "All higher-precedence gates pass and candidate/source totals "
                    "match after independent cent-scale normalization."
                ),
                "reconciled_within_tolerance": (
                    "All higher-precedence gates pass and a nonzero normalized delta "
                    "is within tolerance; reserved in v1 because tolerance is 0.00."
                ),
                "component_missing": (
                    "At least one governed component path is absent or null; no "
                    "component is inferred or zero-filled."
                ),
                "source_total_missing": (
                    "The promoted comparator total is absent or null."
                ),
                "regular_season_scope_unresolved": (
                    "Season/season_type or deterministic completeness evidence does "
                    "not satisfy the governed regular-season scope."
                ),
                "season_incomplete": (
                    "The row declares zero observed regular-season weeks."
                ),
                "scoring_mismatch": (
                    "All higher-precedence gates pass and the normalized delta is "
                    "nonzero and outside tolerance."
                ),
                "unsupported_position": (
                    "The producer-native position is outside QB/RB/WR/TE."
                ),
                "identity_unresolved": (
                    "Source-verified player identity is not established."
                ),
            },
            "reason_code_vocabulary": {
                "fixed": {
                    "position_outside_qb_rb_wr_te_scope": (
                        "Producer-native position is outside the approved profile."
                    ),
                    "source_verified_identity_required": (
                        "A nonempty player ID/name and source_verified confidence are required."
                    ),
                    "weeks_observed_not_integer": (
                        "weeks_observed is not a non-boolean JSON integer."
                    ),
                    "weeks_observed_outside_0_18": (
                        "weeks_observed is outside the inclusive range 0-18."
                    ),
                    "coverage_status_conflicts_with_weeks_observed": (
                        "Declared coverage_status disagrees with deterministic classification."
                    ),
                    "season_or_season_type_outside_contract": (
                        "season is outside 2021-2025 or season_type is not REG."
                    ),
                    "zero_regular_season_weeks_observed": (
                        "No regular-season stat-line week is represented."
                    ),
                    "required_profile_component_unavailable": (
                        "One or more exact source paths in component_bindings is absent or null."
                    ),
                    "promoted_season_ppr_unavailable": (
                        "production_summary.season_ppr is absent or null."
                    ),
                    "candidate_profile_matches_source_total_at_cent_scale": (
                        "Independently normalized candidate and source totals match exactly."
                    ),
                    "candidate_profile_within_declared_numeric_tolerance": (
                        "A nonzero normalized delta is no greater than tolerance."
                    ),
                    "source_total_not_equivalent_to_candidate_profile": (
                        "The normalized source total differs from the candidate profile total."
                    ),
                    "delta_not_attributable_from_promoted_component_set": (
                        "Promoted rows omit the out-of-profile fields needed for "
                        "per-row attribution."
                    ),
                },
                "patterns": {
                    "declared_<coverage_status>": (
                        "Carries the producer-declared coverage_status value on a conflict."
                    ),
                    "computed_<season_completeness>": (
                        "Carries the deterministic completeness class on a conflict."
                    ),
                },
            },
        },
        "season_completeness_states": list(COMPLETENESS_STATES),
        "source_total_semantics": _source_semantics(),
        "consumer_boundary": {
            "allowed": [
                "inspect generic full-PPR component identity",
                "use derived_generic_ppr as candidate evidence after downstream admission",
                "inspect source-total discrepancies and explicit completeness",
            ],
            "not_allowed": [
                "rewrite promoted source bytes or totals",
                "infer omitted source-total components per row",
                "claim every source season_ppr conforms to the candidate profile",
                "authorize Forecast model admission, cutoff selection, or run execution",
                "promote, deploy, rank, advise, or produce league-specific scoring",
            ],
        },
    }


def _source_pins(
    source: dict[str, Any], source_manifest: dict[str, Any]
) -> dict[str, Any]:
    return {
        "repository": "Prometheus-Frameworks/TIBER-Data",
        "repository_commit": SOURCE_REPOSITORY_COMMIT,
        "artifact": {
            "path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
            "sha256": SOURCE_SHA256,
            "artifact_id": source.get("artifact_id"),
            "spec_version": source.get("spec_version"),
            "status": source.get("status"),
            "promotion_review": source.get("promotion_review"),
            "promotion_decision": source.get("promotion_decision"),
            "row_count": len(source.get("records", [])),
            "seasons": source.get("seasons"),
            "season_type_scope": source.get("season_type_scope"),
        },
        "promotion_manifest": {
            "path": str(SOURCE_MANIFEST_PATH.relative_to(REPO_ROOT)),
            "sha256": SOURCE_MANIFEST_SHA256,
            "declared_promoted_artifact_sha256": source_manifest.get(
                "promoted_artifact_sha256"
            ),
        },
        "source_candidate": {
            "path": source.get("source_candidate", {}).get("path"),
            "sha256": source.get("source_candidate", {}).get("sha256"),
        },
    }


def _validate_source(
    source: dict[str, Any], source_manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    expected = {
        "artifact_id": "player_season_coverage_v0",
        "spec_version": "player_season_coverage_v0_promoted_v1",
        "status": "promoted_governed_artifact",
        "seasons": list(SOURCE_SEASONS),
        "season_type_scope": ["REG"],
        "included_positions": ["QB", "RB", "TE", "WR"],
        "row_grain": "player_id + season + season_type",
    }
    for key, value in expected.items():
        if source.get(key) != value:
            raise ReconciliationError(
                f"source contract drift for {key}: expected {value!r}, "
                f"got {source.get(key)!r}"
            )

    records = source.get("records")
    if not isinstance(records, list) or len(records) != SOURCE_RECORD_COUNT:
        raise ReconciliationError(
            f"expected {SOURCE_RECORD_COUNT} source records, got "
            f"{len(records) if isinstance(records, list) else type(records).__name__}"
        )
    if source.get("source_candidate", {}).get("sha256") != SOURCE_CANDIDATE_SHA256:
        raise ReconciliationError("promoted source_candidate sha256 drift")
    if source_manifest.get("promoted_artifact_sha256") != SOURCE_SHA256:
        raise ReconciliationError(
            "promotion manifest no longer binds the exact promoted artifact bytes"
        )

    seen: set[tuple[Any, Any, Any]] = set()
    for row in records:
        key = (row.get("player_id"), row.get("season"), row.get("season_type"))
        if key in seen:
            raise ReconciliationError(f"duplicate promoted source row grain: {key!r}")
        seen.add(key)
    return records


def _report_markdown(
    summary: dict[str, Any],
    source_pins: dict[str, Any],
) -> str:
    lines = [
        "# `player_season_coverage_v0` generic PPR reconciliation v1",
        "",
        f"- **Generated at:** {GENERATED_AT}",
        "- **Tracking:** TIBER-Data #228",
        f"- **Terminal decision:** `{TERMINAL_DECISION}`",
        "- **Status:** candidate reconciliation evidence; not promoted and not a "
        "Forecast admission/run decision.",
        f"- **Profile:** `tiber-generic-full-ppr-v1` (`sha256:{PROFILE_SHA256}`)",
        f"- **Pinned source:** `{source_pins['artifact']['path']}` at "
        f"`sha256:{SOURCE_SHA256}` from TIBER-Data `{SOURCE_REPOSITORY_COMMIT}`.",
        "",
        "## Decision",
        "",
        "The exact issue-approved generic PPR total is computable from governed "
        "components for every one of the 3,016 promoted rows. That component-derived "
        "value is usable as candidate scoring-identity evidence, subject to a separate "
        "Forecast admission decision.",
        "",
        "The promoted `production_summary.season_ppr` field is **not equivalent** to "
        "that profile for all rows: after independent cent-scale `ROUND_HALF_UP` "
        "normalization, 2,186 rows match exactly and 830 have a nonzero cent-scale "
        "difference. Raw serialization residue remains visible for diagnostics but "
        "does not create a semantic mismatch or tolerance pass. Differences are "
        "preserved, source totals are never overwritten, and omitted source-total "
        "component families are never inferred from the delta.",
        "",
        "## Overall reconciliation",
        "",
        "| Measure | Count / rate |",
        "| --- | ---: |",
        f"| Source rows | {summary['row_count']} |",
        f"| Exact matches | "
        f"{summary['reconciliation_status_counts'].get('reconciled_exact', 0)} |",
        f"| Within tolerance | "
        f"{summary['reconciliation_status_counts'].get('reconciled_within_tolerance', 0)} |",
        f"| Scoring mismatches | {summary['source_total_mismatch_rows']} |",
        f"| Source-total conformance | {summary['source_total_conformance_rate']} |",
        f"| Source-total mismatch | {summary['source_total_mismatch_rate']} |",
        f"| Missing profile components | "
        f"{sum(summary['component_missing_counts'].values())} |",
        f"| Missing source totals | {summary['source_total_missing_count']} |",
        "",
        "## By season",
        "",
        "| Season | Rows | Exact | Mismatch | Conformance |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for season, values in summary["by_season"].items():
        exact = values["reconciliation_status_counts"].get("reconciled_exact", 0)
        lines.append(
            f"| {season} | {values['row_count']} | {exact} | "
            f"{values['source_total_mismatch_rows']} | "
            f"{values['source_total_conformance_rate']} |"
        )

    lines.extend(
        [
            "",
            "## By position",
            "",
            "| Position | Rows | Exact | Mismatch | Conformance |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for position, values in summary["by_position"].items():
        exact = values["reconciliation_status_counts"].get("reconciled_exact", 0)
        lines.append(
            f"| {position} | {values['row_count']} | {exact} | "
            f"{values['source_total_mismatch_rows']} | "
            f"{values['source_total_conformance_rate']} |"
        )

    lines.extend(
        [
            "",
        "## Completeness and week scope",
        "",
        "The pinned 2021–2025 population covers the season pairs needed to inspect "
        "2022→2023, 2023→2024, and 2024→2025 candidate temporal origins. This is "
        "season-presence/scoring evidence only; it does not define or accept a "
        "Forecast split.",
        "",
        "Every row carries one explicit completeness state. The source methodology "
            "defines `full_season` as 15–18 observed REG week numbers, "
            "`partial_season` as 2–14, and `single_week` as 1. Week 18 is included. "
            "A count of zero is `missing`; an invalid count or count/status conflict "
            "is `irreconcilable`.",
            "",
            "The promoted rows expose only `weeks_observed`, not individual week "
            "numbers. This evidence therefore binds the promoted REG declaration and "
            "valid 0–18 count range without pretending to reconstruct weekly rows. "
            "Absence of a stat-line week is not interpreted as injury, inactivity, or "
            "a missed game.",
            "",
            "| Completeness | Rows |",
            "| --- | ---: |",
        ]
    )
    for state in COMPLETENESS_STATES:
        lines.append(
            f"| `{state}` | {summary['season_completeness_counts'].get(state, 0)} |"
        )

    lines.extend(
        [
            "",
            "## Source-total semantics",
            "",
            "The promoted builder declares `season_ppr` to be a direct passthrough of "
            "`nflreadpy.load_player_stats(summary_level='reg').fantasy_points_ppr`. "
            "Current official nflfastR producer code corroborates that its PPR total "
            "includes the candidate profile plus special-teams touchdowns, passing/"
            "rushing/receiving two-point conversions, and sack/rushing/receiving "
            "fumbles lost. The producer code is pinned here only as semantic "
            f"corroboration: [`{NFLFASTR_SEMANTICS_PATH}` at "
            f"`{NFLFASTR_SEMANTICS_COMMIT}`]({NFLFASTR_SEMANTICS_URL}), blob "
            f"`{NFLFASTR_SEMANTICS_BLOB}`.",
            "",
            "The promoted artifact did not pin the exact historical nflreadpy/nflverse "
            "release used for retrieval, so this report does not claim that the current "
            "producer commit is that historical release. The promoted source bytes, "
            "their promotion manifest, and their original source-candidate hash are "
            "the authoritative inputs to this reconciliation.",
            "",
            "All 830 nonzero differences are integer multiples of two, with signed "
            f"`derived - source` range "
            f"`{summary['mismatch_delta']['signed_min']}` to "
            f"`{summary['mismatch_delta']['signed_max']}`. This is consistent with the "
            "corroborated out-of-profile families, but the promoted rows omit those "
            "families, so no per-row attribution is made.",
            "",
            "## Aggregation, missingness, and numeric rules",
            "",
            "- Component-derived season scoring has precedence for identifying the "
            "exact candidate profile.",
            "- Promoted `season_ppr` remains a source comparator and is never rewritten.",
            "- No weekly scoring rows are present in the promoted source; no weekly sum "
            "is fabricated or substituted.",
            "- Decimal arithmetic is exact from JSON numeric text. Published values use "
        "two decimals and `ROUND_HALF_UP`; independently normalized totals must have "
        "a zero-cent delta to reconcile. The v1 tolerance is 0.00.",
            "- Present numeric zero is genuine zero. Missing/null is unavailable and "
            "never zero-filled.",
            "",
            "## Output packet",
            "",
            f"- Contract: `{CONTRACT_PATH.relative_to(REPO_ROOT)}`",
            f"- Per-row evidence: `{RECONCILIATION_PATH.relative_to(REPO_ROOT)}`",
            f"- Discrepancy ledger: `{DISCREPANCY_PATH.relative_to(REPO_ROOT)}`",
            f"- Missingness ledger: `{MISSINGNESS_PATH.relative_to(REPO_ROOT)}`",
            f"- Evidence manifest: `{EVIDENCE_MANIFEST_PATH.relative_to(REPO_ROOT)}`",
            "",
            "## Authority boundary",
            "",
            "This packet does not promote any artifact, change the promoted source, "
            "authorize a Forecast target, select a cutoff, train/freeze a model, execute "
            "a forward run, or emit rankings/advice. Forecast admission and all "
            "downstream policy remain operator decisions.",
            "",
        ]
    )
    return "\n".join(lines)


def build_outputs() -> dict[Path, bytes]:
    source = _load_pinned_json(SOURCE_PATH, SOURCE_SHA256)
    source_manifest = _load_pinned_json(
        SOURCE_MANIFEST_PATH, SOURCE_MANIFEST_SHA256
    )
    source_records = _validate_source(source, source_manifest)

    rows = [
        evaluate_row(row, source_ordinal)
        for source_ordinal, row in enumerate(source_records)
    ]
    rows.sort(
        key=lambda row: (
            row["source_row_key"]["season"],
            row["source_row_key"]["player_id"],
            row["source_row_key"]["season_type"],
        )
    )
    if len(rows) != len(source_records):
        raise ReconciliationError("not every source row received reconciliation evidence")

    summary = _build_summary(rows)
    source_pins = _source_pins(source, source_manifest)

    invalid_or_missing = sum(
        count
        for status, count in summary["reconciliation_status_counts"].items()
        if status
        not in {
            "reconciled_exact",
            "reconciled_within_tolerance",
            "scoring_mismatch",
        }
    )
    if invalid_or_missing:
        raise ReconciliationError(
            f"{invalid_or_missing} rows cannot evaluate the approved profile; "
            "mandatory stop condition reached"
        )
    if summary["row_count"] != SOURCE_RECORD_COUNT:
        raise ReconciliationError("summary row count does not reconcile to source")
    if sum(summary["reconciliation_status_counts"].values()) != SOURCE_RECORD_COUNT:
        raise ReconciliationError("reconciliation status counts do not sum to source")
    if sum(summary["season_completeness_counts"].values()) != SOURCE_RECORD_COUNT:
        raise ReconciliationError("completeness status counts do not sum to source")

    contract = _contract()
    reconciliation = {
        "artifact_id": "player_season_coverage_v0_generic_ppr_reconciliation_v1",
        "spec_version": "1.0.0",
        "status": "candidate_evidence_not_promoted",
        "generated_at": GENERATED_AT,
        "tracking_issue": "TIBER-Data#228",
        "terminal_decision": TERMINAL_DECISION,
        "profile": contract["profile"],
        "source": source_pins,
        "historical_scope": {
            "seasons": list(SOURCE_SEASONS),
            "candidate_temporal_origins_covered_by_season_presence": [
                "2022_to_2023",
                "2023_to_2024",
                "2024_to_2025",
            ],
            "forecast_split_authorized": False,
        },
        "source_total_semantics": _source_semantics(),
        "contract_decisions": {
            key: contract[key]
            for key in (
                "week_inclusion",
                "season_completeness",
                "aggregation_precedence",
                "numeric_rule",
                "missingness_and_zero",
                "component_bindings",
                "reconciliation_status_contract",
            )
        },
        "usability": {
            "candidate_generic_ppr_component_evidence": "usable",
            "promoted_source_total_profile_identity": "partially_supported_not_equivalent",
            "required_downstream_action": (
                "Forecast/operator must separately decide whether to admit the "
                "component-derived target; this evidence grants no admission."
            ),
        },
        "summaries": summary,
        "records": rows,
    }

    discrepancies = {
        "artifact_id": "player_season_coverage_v0_generic_ppr_discrepancies_v1",
        "spec_version": "1.0.0",
        "status": "candidate_evidence_not_promoted",
        "generated_at": GENERATED_AT,
        "tracking_issue": "TIBER-Data#228",
        "profile_sha256": PROFILE_SHA256,
        "source_artifact_sha256": SOURCE_SHA256,
        "row_count": summary["source_total_mismatch_rows"],
        "reason": (
            "Rows whose promoted source season_ppr differs from the exact "
            "issue-approved component-derived profile after independent cent-scale "
            "ROUND_HALF_UP normalization."
        ),
        "records": [
            {
                "source_row_key": row["source_row_key"],
                "player_name": row["player_name"],
                "position": row["position"],
                "season_completeness": row["season_completeness"],
                "derived_generic_ppr": row["derived_generic_ppr"],
                "derived_generic_ppr_unrounded": row[
                    "derived_generic_ppr_unrounded"
                ],
                "promoted_source_season_ppr": row[
                    "promoted_source_season_ppr"
                ],
                "promoted_source_season_ppr_unrounded": row[
                    "promoted_source_season_ppr_unrounded"
                ],
                "signed_delta_derived_minus_source": row[
                    "signed_delta_derived_minus_source"
                ],
                "signed_delta_derived_minus_source_unrounded": row[
                    "signed_delta_derived_minus_source_unrounded"
                ],
                "absolute_delta": row["absolute_delta"],
                "absolute_delta_unrounded": row["absolute_delta_unrounded"],
                "reconciliation_status": row["reconciliation_status"],
                "reason_codes": row["reason_codes"],
            }
            for row in rows
            if row["reconciliation_status"] == "scoring_mismatch"
        ],
    }
    missingness_records = [
        {
            "source_row_key": row["source_row_key"],
            "player_name": row["player_name"],
            "position": row["position"],
            "season_completeness": row["season_completeness"],
            "component_availability": row["component_availability"],
            "missing_components": row["missing_components"],
            "promoted_source_season_ppr": row["promoted_source_season_ppr"],
            "reconciliation_status": row["reconciliation_status"],
            "reason_codes": row["reason_codes"],
        }
        for row in rows
        if row["reconciliation_status"]
        in {
            "component_missing",
            "source_total_missing",
            "regular_season_scope_unresolved",
            "season_incomplete",
            "unsupported_position",
            "identity_unresolved",
        }
    ]
    missingness = {
        "artifact_id": "player_season_coverage_v0_generic_ppr_missingness_v1",
        "spec_version": "1.0.0",
        "status": "candidate_evidence_not_promoted",
        "generated_at": GENERATED_AT,
        "tracking_issue": "TIBER-Data#228",
        "profile_sha256": PROFILE_SHA256,
        "source_artifact_sha256": SOURCE_SHA256,
        "row_count": len(missingness_records),
        "summary": {
            "component_missing_counts": summary["component_missing_counts"],
            "source_total_missing_count": summary["source_total_missing_count"],
            "non_evaluable_status_counts": {
                state: summary["reconciliation_status_counts"].get(state, 0)
                for state in (
                    "component_missing",
                    "source_total_missing",
                    "regular_season_scope_unresolved",
                    "season_incomplete",
                    "unsupported_position",
                    "identity_unresolved",
                )
            },
            "genuine_zero_rule": (
                "Present numeric zero is observed, scored, and never listed as missing."
            ),
        },
        "records": missingness_records,
    }

    report = _report_markdown(summary, source_pins).encode("utf-8")
    preliminary: dict[Path, bytes] = {
        CONTRACT_PATH: pretty_json_bytes(contract),
        RECONCILIATION_PATH: pretty_json_bytes(reconciliation),
        DISCREPANCY_PATH: pretty_json_bytes(discrepancies),
        MISSINGNESS_PATH: pretty_json_bytes(missingness),
        REPORT_PATH: report,
    }
    evidence_manifest = {
        "artifact_id": "player_season_coverage_v0_generic_ppr_reconciliation_v1_manifest",
        "spec_version": "1.0.0",
        "status": "candidate_evidence_manifest_not_promoted",
        "generated_at": GENERATED_AT,
        "tracking_issue": "TIBER-Data#228",
        "terminal_decision": TERMINAL_DECISION,
        "source": source_pins,
        "profile_sha256": PROFILE_SHA256,
        "generator": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
        "outputs": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256_bytes(content),
                "bytes": len(content),
            }
            for path, content in sorted(
                preliminary.items(), key=lambda item: str(item[0])
            )
        ],
        "invariants": {
            "source_rows": SOURCE_RECORD_COUNT,
            "reconciliation_rows": summary["row_count"],
            "status_count_sum": sum(
                summary["reconciliation_status_counts"].values()
            ),
            "completeness_count_sum": sum(
                summary["season_completeness_counts"].values()
            ),
            "discrepancy_rows": discrepancies["row_count"],
            "missingness_rows": missingness["row_count"],
            "source_bytes_modified": False,
            "forecast_authorized": False,
            "promotion_attempted": False,
        },
        "reproduce": [
            "python3 scripts/reconcile_player_season_coverage_ppr_v1.py",
            "python3 scripts/reconcile_player_season_coverage_ppr_v1.py --check",
        ],
        "authority_boundary": (
            "TIBER-Data candidate evidence only. No source mutation, promotion, "
            "Forecast admission, cutoff selection, model/run execution, or advice."
        ),
    }
    preliminary[EVIDENCE_MANIFEST_PATH] = pretty_json_bytes(evidence_manifest)
    return preliminary


def _check_outputs(outputs: dict[Path, bytes]) -> list[str]:
    errors: list[str] = []
    for path, expected in outputs.items():
        if not path.is_file():
            errors.append(f"missing generated output: {path.relative_to(REPO_ROOT)}")
            continue
        actual = path.read_bytes()
        if actual != expected:
            errors.append(f"stale generated output: {path.relative_to(REPO_ROOT)}")
    return errors


def _write_outputs(outputs: dict[Path, bytes]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed generated outputs without writing",
    )
    args = parser.parse_args(argv)

    try:
        outputs = build_outputs()
        if args.check:
            errors = _check_outputs(outputs)
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print(
                f"verified {len(outputs)} deterministic outputs; "
                f"profile sha256={PROFILE_SHA256}"
            )
            return 0
        _write_outputs(outputs)
    except (OSError, json.JSONDecodeError, ReconciliationError) as exc:
        print(f"reconciliation failed closed: {exc}", file=sys.stderr)
        return 1

    print(
        f"wrote {len(outputs)} deterministic outputs; "
        f"terminal decision={TERMINAL_DECISION}; profile sha256={PROFILE_SHA256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
