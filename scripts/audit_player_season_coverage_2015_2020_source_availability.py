"""Audit 2015-2020 REG source availability for the player_season_coverage_v0 family.

TIBER-Data #216: bounded, read-only source-availability audit. For each REG season
2015-2020 it asks whether the approved source family
(nflreadpy.load_player_stats + nflreadpy.load_players — the exact allowlist in
exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json) exposes
enough source-backed, contract-compatible evidence to justify a LATER, separately
authorized player_season_coverage_v0 candidate-build issue.

This script is a NON-PROMOTIONAL inspection/reporting tool. It:

- inspects each season independently via
  nflreadpy.load_player_stats(seasons=[year], summary_level='week'),
  nflreadpy.load_player_stats(seasons=[year], summary_level='reg'),
  and nflreadpy.load_players() (identity/birth-date/rookie/draft metadata only);
- reports per-season aggregate counts, exact REG week values observed, required and
  optional column resolution, null rates, duplicate grain pairs, and identity join
  rates — never player names or player-level rows;
- does NOT assume the 2021+ schedule shape (EXPECTED_REG_WEEKS = 1-18). It first
  reports what each season's source actually contains and then states the narrowest
  schedule-span rule supported by that evidence;
- keeps each season's result separate and preserves source exceptions honestly:
  a season whose source calls fail is reported as NOT OBSERVED, never as pass or
  as "source lacks the data";
- writes an aggregate evidence report to docs/reports/ (markdown + json) and emits
  exactly one terminal decision from the enum fixed in #216.

The audit may establish only: source_rows_exist, builder_compatible,
candidate_build_may_be_proposed. It must NOT and does not:
- write anything under data/, exports/, or schemas/;
- build, modify, or emit any candidate or promoted artifact rows;
- widen any README/contract support-window claim (2021-2025 REG remains the only
  promoted window);
- modify the 2021 or 2022-2025 builders;
- ingest or evaluate ADP, rankings, or market data;
- authorize any Forecast behavior.

Exit codes: 0 = every season fully observed and cleared (decision may_open_...);
2 = requires_followup (including any source-call failure — fail closed, the audit
is not a pass); 3 = do_not_pursue under the current source contract.
"""

from __future__ import annotations

import json
import platform
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2015-2020-source-availability.md"
REPORT_JSON_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2015-2020-source-availability.json"
PROMOTED_MANIFEST_PATH = REPO_ROOT / "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json"

SEASONS = (2015, 2016, 2017, 2018, 2019, 2020)
SEASON_TYPE = "REG"
INCLUDED_POSITIONS = ("QB", "RB", "WR", "TE")

# Column-candidate lists copied from scripts/build_player_season_coverage_2022_2025.py
# and scripts/build_player_season_coverage_2021_candidate.py (the promoted builders).
# "required" mirrors which resolutions those builders treat as hard requirements.
WEEK_LEVEL_COLUMNS = {
    "season": {"candidates": ["season"], "required": True},
    "week": {"candidates": ["week"], "required": True},
    "player_id": {"candidates": ["player_id", "gsis_id"], "required": True},
    "team": {"candidates": ["team", "recent_team"], "required": True},
    "season_type": {"candidates": ["season_type"], "required": True},
}
REG_LEVEL_COLUMNS = {
    "player_id": {"candidates": ["player_id", "gsis_id"], "required": True},
    "player_name": {"candidates": ["player_display_name", "player_name"], "required": True},
    "position": {"candidates": ["position"], "required": True},
    "games": {"candidates": ["games"], "required": True},
    "season_type": {"candidates": ["season_type"], "required": False},
    "completions": {"candidates": ["completions"], "required": False},
    "attempts": {"candidates": ["attempts"], "required": False},
    "passing_yards": {"candidates": ["passing_yards"], "required": False},
    "passing_tds": {"candidates": ["passing_tds"], "required": False},
    "passing_interceptions": {"candidates": ["passing_interceptions"], "required": False},
    "carries": {"candidates": ["carries"], "required": False},
    "rushing_yards": {"candidates": ["rushing_yards"], "required": False},
    "rushing_tds": {"candidates": ["rushing_tds"], "required": False},
    "receptions": {"candidates": ["receptions"], "required": False},
    "targets": {"candidates": ["targets"], "required": False},
    "receiving_yards": {"candidates": ["receiving_yards"], "required": False},
    "receiving_tds": {"candidates": ["receiving_tds"], "required": False},
    "receiving_air_yards": {"candidates": ["receiving_air_yards"], "required": False},
    "target_share": {"candidates": ["target_share"], "required": False},
    "air_yards_share": {"candidates": ["air_yards_share"], "required": False},
    "wopr": {"candidates": ["wopr"], "required": False},
    "racr": {"candidates": ["racr"], "required": False},
    "fantasy_points_ppr": {"candidates": ["fantasy_points_ppr"], "required": False},
}
PLAYERS_IDENTITY_COLUMNS = [
    "gsis_id",
    "birth_date",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_team",
    "rookie_season",
]
IDENTITY_FIELDS_REPORTED = (
    "birth_date",
    "rookie_season",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_team",
)

# Minimum identity-join rate for load_players() to be considered compatible with the
# promoted 2021-2025 builds (which observed 100% source_verified identity joins and
# enforce this same floor, see IDENTITY_JOIN_RATE_FLOOR in the 2021 builder / #198).
IDENTITY_JOIN_RATE_FLOOR = 0.95

# Schedule-methodology rule (#216): the 2021+ assumption EXPECTED_REG_WEEKS =
# set(range(1, 19)) is deliberately NOT reused here. Weeks are observed per season;
# the only hard cap applied is that no REG week may exceed the widest span the
# current schema/validator semantics have ever governed (18), and no week may be
# below 1. Anything else is reported as observed evidence, not assumed.
ABSOLUTE_MAX_REG_WEEK = 18
ABSOLUTE_MIN_REG_WEEK = 1

ALLOWED_DECISIONS = (
    "may_open_player_season_coverage_2015_2020_candidate_build_issue",
    "player_season_coverage_2015_2020_source_audit_requires_followup",
    "do_not_pursue_player_season_coverage_2015_2020_under_current_source_contract",
)

BUILDER_COMPATIBLE_VALUES = (
    "compatible_as_is",
    "compatible_with_explicit_week_span_parameter",
    "incompatible",
    "not_observed",
)

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_NOT_OBSERVED = "not_observed"


def _records_from_dataframe(df) -> list[dict]:
    if hasattr(df, "to_dicts"):
        return df.to_dicts()
    return df.to_dict("records")


def _is_null(value) -> bool:
    if value is None:
        return True
    try:
        import math

        if isinstance(value, float) and math.isnan(value):
            return True
    except TypeError:
        pass
    return False


def _resolve_columns(columns: set[str], spec: dict[str, dict]) -> dict[str, dict]:
    resolved: dict[str, dict] = {}
    for field, meta in spec.items():
        found = next((c for c in meta["candidates"] if c in columns), None)
        resolved[field] = {
            "candidates": meta["candidates"],
            "required": meta["required"],
            "resolved_column": found,
            "present": found is not None,
        }
    return resolved


def _null_rate(rows: list[dict], column: str | None) -> dict:
    if column is None:
        return {"nulls": None, "total": len(rows), "rate": None, "note": "column not present in source"}
    nulls = sum(1 for r in rows if _is_null(r.get(column)))
    total = len(rows)
    return {"nulls": nulls, "total": total, "rate": round(nulls / total, 4) if total else None}


def build_players_index(players_df) -> tuple[dict[str, dict], dict[str, bool]]:
    """Index load_players() rows by gsis_id for identity joins; report column presence."""
    players_columns = set(players_df.columns)
    identity_present = {c: (c in players_columns) for c in PLAYERS_IDENTITY_COLUMNS}
    index: dict[str, dict] = {}
    if identity_present.get("gsis_id"):
        for row in _records_from_dataframe(players_df):
            gsis_id = row.get("gsis_id")
            if gsis_id is None or str(gsis_id).strip() == "":
                continue
            index[str(gsis_id).strip()] = row
    return index, identity_present


def inspect_season(
    season: int,
    week_df,
    reg_df,
    players_index: dict[str, dict] | None,
    players_identity_present: dict[str, bool] | None,
) -> dict:
    """Inspect one season's already-loaded source frames. Aggregates only.

    Never returns player names, player IDs, or player-level rows. players_index may
    be None when load_players() itself failed; identity checks then stay not_observed.
    """
    week_columns = set(week_df.columns)
    reg_columns = set(reg_df.columns)

    week_resolved = _resolve_columns(week_columns, WEEK_LEVEL_COLUMNS)
    reg_resolved = _resolve_columns(reg_columns, REG_LEVEL_COLUMNS)

    missing_required_week = [f for f, m in week_resolved.items() if m["required"] and not m["present"]]
    missing_required_reg = [f for f, m in reg_resolved.items() if m["required"] and not m["present"]]
    missing_optional_reg = [f for f, m in reg_resolved.items() if not m["required"] and not m["present"]]

    week_records_all = _records_from_dataframe(week_df)
    reg_records_all = _records_from_dataframe(reg_df)

    def _col(resolved: dict, field: str) -> str | None:
        return resolved[field]["resolved_column"]

    wk_season_type_col = _col(week_resolved, "season_type")
    reg_season_type_col = _col(reg_resolved, "season_type")

    week_season_types = sorted(
        {str(r.get(wk_season_type_col, "")).strip().upper() for r in week_records_all}
    ) if wk_season_type_col else []
    reg_season_types = sorted(
        {str(r.get(reg_season_type_col, "")).strip().upper() for r in reg_records_all}
    ) if reg_season_type_col else []

    week_reg_rows = [
        r
        for r in week_records_all
        if wk_season_type_col and str(r.get(wk_season_type_col, "")).strip().upper() == SEASON_TYPE
    ]
    reg_rows = [
        r
        for r in reg_records_all
        if (reg_season_type_col is None)
        or str(r.get(reg_season_type_col, "")).strip().upper() == SEASON_TYPE
    ]

    position_col = _col(reg_resolved, "position")
    reg_player_id_col = _col(reg_resolved, "player_id")
    wk_player_id_col = _col(week_resolved, "player_id")
    wk_week_col = _col(week_resolved, "week")
    wk_team_col = _col(week_resolved, "team")

    reg_position_rows = [
        r
        for r in reg_rows
        if position_col and str(r.get(position_col) or "").strip().upper() in INCLUDED_POSITIONS
    ]

    row_counts_by_position: dict[str, int] = {p: 0 for p in INCLUDED_POSITIONS}
    players_by_position: dict[str, set] = {p: set() for p in INCLUDED_POSITIONS}
    grain_seen: set = set()
    duplicate_grain_pairs = 0
    for r in reg_position_rows:
        pos = str(r.get(position_col) or "").strip().upper()
        pid = str(r.get(reg_player_id_col) or "").strip() if reg_player_id_col else ""
        if not pid:
            continue
        row_counts_by_position[pos] += 1
        players_by_position[pos].add(pid)
        key = (pid, season, SEASON_TYPE)
        if key in grain_seen:
            duplicate_grain_pairs += 1
        grain_seen.add(key)

    reg_week_numbers = sorted(
        {int(r[wk_week_col]) for r in week_reg_rows if not _is_null(r.get(wk_week_col))}
    ) if wk_week_col else []
    min_reg_week = reg_week_numbers[0] if reg_week_numbers else None
    max_reg_week = reg_week_numbers[-1] if reg_week_numbers else None
    week_gaps = (
        sorted(set(range(ABSOLUTE_MIN_REG_WEEK, max_reg_week + 1)) - set(reg_week_numbers))
        if max_reg_week is not None
        else []
    )
    unexpected_weeks = sorted(
        w for w in reg_week_numbers if w < ABSOLUTE_MIN_REG_WEEK or w > ABSOLUTE_MAX_REG_WEEK
    )

    weeks_by_player: dict[str, set[int]] = defaultdict(set)
    if wk_player_id_col and wk_week_col:
        for r in week_reg_rows:
            pid = str(r.get(wk_player_id_col) or "").strip()
            if pid and not _is_null(r.get(wk_week_col)):
                weeks_by_player[pid].add(int(r[wk_week_col]))
    max_weeks_observed_any_player = max((len(w) for w in weeks_by_player.values()), default=0)

    games_col = _col(reg_resolved, "games")
    games_values = [
        r.get(games_col) for r in reg_position_rows if games_col and not _is_null(r.get(games_col))
    ]
    max_games = max((int(g) for g in games_values), default=None) if games_values else None

    null_observations = {
        field: _null_rate(reg_position_rows, _col(reg_resolved, field))
        for field in (
            "games",
            "fantasy_points_ppr",
            "targets",
            "receptions",
            "carries",
            "receiving_air_yards",
            "target_share",
            "air_yards_share",
            "wopr",
            "racr",
        )
    }
    team_context_null = _null_rate(week_reg_rows, wk_team_col)
    team_context_null["level"] = "week_level_reg_rows"
    null_observations["team_context"] = team_context_null

    all_player_ids = (
        set().union(*players_by_position.values()) if any(players_by_position.values()) else set()
    )

    if players_index is None or players_identity_present is None:
        identity_join_rate = None
        joined_count = None
        identity_field_rates = {
            f: {"available": None, "total": None, "rate": None, "note": "load_players() not observed"}
            for f in IDENTITY_FIELDS_REPORTED
        }
        gsis_join_available = None
    else:
        gsis_join_available = players_identity_present.get("gsis_id", False)
        joined = [pid for pid in sorted(all_player_ids) if pid in players_index]
        joined_count = len(joined)
        identity_join_rate = (
            round(joined_count / len(all_player_ids), 4) if all_player_ids else None
        )

        def _identity_field_rate(field: str) -> dict:
            if not players_identity_present.get(field):
                return {
                    "available": None,
                    "total": joined_count,
                    "rate": None,
                    "note": "column not present in load_players()",
                }
            available = sum(1 for pid in joined if not _is_null(players_index[pid].get(field)))
            return {
                "available": available,
                "total": joined_count,
                "rate": round(available / joined_count, 4) if joined_count else None,
            }

        identity_field_rates = {f: _identity_field_rate(f) for f in IDENTITY_FIELDS_REPORTED}

    # --- per-season statuses (kept separate per #216, never collapsed) -----------
    positions_all_present = all(row_counts_by_position[p] > 0 for p in INCLUDED_POSITIONS)
    rows_exist = (
        len(week_records_all) > 0
        and len(reg_records_all) > 0
        and len(week_reg_rows) > 0
        and len(reg_position_rows) > 0
        and (SEASON_TYPE in week_season_types or SEASON_TYPE in reg_season_types)
        and positions_all_present
    )
    required_columns_present = not missing_required_week and not missing_required_reg

    # schedule_method_observed: the week span is taken from evidence, not assumed.
    # It passes only when REG weeks were observed, form a contiguous span starting
    # at week 1, and stay within the absolute 1-18 bound.
    schedule_observed = (
        bool(reg_week_numbers)
        and min_reg_week == ABSOLUTE_MIN_REG_WEEK
        and not week_gaps
        and not unexpected_weeks
        and max_weeks_observed_any_player <= (max_reg_week or 0)
    )
    observed_week_span_rule = (
        f"REG weeks {min_reg_week}-{max_reg_week}, contiguous, source-observed"
        if schedule_observed
        else None
    )

    identity_join_sufficient_status = (
        STATUS_NOT_OBSERVED
        if identity_join_rate is None and not all_player_ids
        else STATUS_NOT_OBSERVED
        if players_index is None
        else STATUS_PASS
        if (gsis_join_available and identity_join_rate is not None and identity_join_rate >= IDENTITY_JOIN_RATE_FLOOR)
        else STATUS_FAIL
    )

    # existing_schema_compatible: schemas/player_season_coverage_v0.schema.json is
    # season-agnostic (season >= 1900, weeks_observed >= 0, no week-span constant),
    # so compatibility is determined by observed shape: unique grain, resolvable
    # required identity fields, and games within the observed week span.
    schema_compatible = (
        rows_exist
        and required_columns_present
        and duplicate_grain_pairs == 0
        and max_games is not None
        and max_reg_week is not None
        and max_games <= max_reg_week
    )

    # existing_validator_semantics_compatible: the validator enforces grain
    # uniqueness, explicit REG season_type, approved-source-prefix refs, and
    # null-vs-zero honesty. Nothing in it hard-codes a season shape. From source
    # evidence the load-bearing observations are unique grain and an explicit REG
    # season_type emitted by the source.
    validator_compatible = (
        rows_exist
        and duplicate_grain_pairs == 0
        and (SEASON_TYPE in week_season_types or SEASON_TYPE in reg_season_types)
    )

    # builder_compatible: the current builders hard-code EXPECTED_REG_WEEKS =
    # set(range(1, 19)) and fail closed on any other span, so a season whose
    # observed span differs can never be built "as is" — only via a later builder
    # that takes an explicit, evidence-backed week-span parameter.
    if not (rows_exist and required_columns_present and schedule_observed):
        builder_compatible = "incompatible"
    elif set(reg_week_numbers) == set(range(1, 19)):
        builder_compatible = "compatible_as_is"
    else:
        builder_compatible = "compatible_with_explicit_week_span_parameter"

    statuses = {
        "source_rows_exist": STATUS_PASS if rows_exist else STATUS_FAIL,
        "required_columns_present": STATUS_PASS if required_columns_present else STATUS_FAIL,
        "identity_join_sufficient": identity_join_sufficient_status,
        "schedule_method_observed": STATUS_PASS if schedule_observed else STATUS_FAIL,
        "existing_schema_compatible": STATUS_PASS if schema_compatible else STATUS_FAIL,
        "existing_validator_semantics_compatible": STATUS_PASS if validator_compatible else STATUS_FAIL,
        "builder_compatible": builder_compatible,
    }

    definitive_failures: list[str] = []
    followup_items: list[str] = []
    if not rows_exist:
        definitive_failures.append("source_rows_exist")
    if not required_columns_present:
        definitive_failures.append(
            "required_columns_present: week-level missing "
            f"{missing_required_week or 'none'}, reg-level missing {missing_required_reg or 'none'}"
        )
    if identity_join_sufficient_status == STATUS_FAIL:
        followup_items.append(
            f"identity_join_sufficient: gsis join rate {identity_join_rate} below floor {IDENTITY_JOIN_RATE_FLOOR}"
        )
    elif identity_join_sufficient_status == STATUS_NOT_OBSERVED:
        followup_items.append("identity_join_sufficient: load_players() not observed")
    if not schedule_observed:
        followup_items.append(
            f"schedule_method_observed: weeks={reg_week_numbers} gaps={week_gaps} unexpected={unexpected_weeks}"
        )
    if duplicate_grain_pairs > 0:
        followup_items.append(
            f"duplicate_grain_pairs: {duplicate_grain_pairs} duplicate (player_id, season, season_type) pairs"
        )
    if rows_exist and required_columns_present and not schema_compatible:
        followup_items.append(
            f"existing_schema_compatible: max_games={max_games} vs max observed REG week {max_reg_week}"
        )

    return {
        "season": season,
        "season_type": SEASON_TYPE,
        "source_calls": [
            {
                "call": f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')",
                "status": "ok",
            },
            {
                "call": f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='reg')",
                "status": "ok",
            },
        ],
        "columns_observed": {
            "week_level": sorted(week_columns),
            "reg_level": sorted(reg_columns),
        },
        "availability": {
            "week_level_rows_total": len(week_records_all),
            "week_level_rows_reg": len(week_reg_rows),
            "reg_level_rows_total": len(reg_records_all),
            "reg_level_rows_reg_qb_rb_wr_te": len(reg_position_rows),
            "season_type_values_week_level": week_season_types,
            "season_type_values_reg_level": reg_season_types,
            "row_counts_by_position_reg_level": row_counts_by_position,
            "player_counts_by_position": {p: len(players_by_position[p]) for p in INCLUDED_POSITIONS},
            "unique_players_all_positions": len(all_player_ids),
            "reg_week_numbers_observed": reg_week_numbers,
            "min_reg_week": min_reg_week,
            "max_reg_week": max_reg_week,
            "week_gaps": week_gaps,
            "unexpected_week_values": unexpected_weeks,
            "max_weeks_observed_any_player": max_weeks_observed_any_player,
            "max_games_reg_level": max_games,
            "duplicate_grain_pairs": duplicate_grain_pairs,
        },
        "schema_compatibility": {
            "week_level_columns": week_resolved,
            "reg_level_columns": reg_resolved,
            "missing_required_week_level": missing_required_week,
            "missing_required_reg_level": missing_required_reg,
            "missing_optional_reg_level": missing_optional_reg,
        },
        "identity_age_draft": {
            "load_players_gsis_join_available": gsis_join_available,
            "identity_join_rate_gsis_id": identity_join_rate,
            "identity_join_rate_floor": IDENTITY_JOIN_RATE_FLOOR,
            "players_joined": joined_count,
            "players_total": len(all_player_ids),
            "field_availability_for_joined_players": identity_field_rates,
        },
        "null_observations": null_observations,
        "observed_week_span_rule": observed_week_span_rule,
        "statuses": statuses,
        "definitive_failures": definitive_failures,
        "followup_items": followup_items,
    }


def _season_error_result(season: int, failed_calls: list[dict]) -> dict:
    """Honest placeholder for a season whose source calls failed: nothing observed."""
    statuses = {
        "source_rows_exist": STATUS_NOT_OBSERVED,
        "required_columns_present": STATUS_NOT_OBSERVED,
        "identity_join_sufficient": STATUS_NOT_OBSERVED,
        "schedule_method_observed": STATUS_NOT_OBSERVED,
        "existing_schema_compatible": STATUS_NOT_OBSERVED,
        "existing_validator_semantics_compatible": STATUS_NOT_OBSERVED,
        "builder_compatible": "not_observed",
    }
    return {
        "season": season,
        "season_type": SEASON_TYPE,
        "source_calls": failed_calls,
        "columns_observed": None,
        "availability": None,
        "schema_compatibility": None,
        "identity_age_draft": None,
        "null_observations": None,
        "observed_week_span_rule": None,
        "statuses": statuses,
        "definitive_failures": [],
        "followup_items": [
            "source_call_failed: season not observed; availability is UNKNOWN, not absent. "
            "This is an inspection-environment/source-access failure, not evidence that the "
            "upstream source lacks this season."
        ],
    }


def run_audit(load_week, load_reg, load_players, promoted_manifest: dict) -> dict:
    """Run the full 2015-2020 audit with injected loaders (network or fixtures).

    load_week(year) / load_reg(year) return dataframes for one season; load_players()
    returns the identity frame. Each season is inspected independently: one season's
    source failure never blocks or contaminates another season's evidence, and a
    failed season is recorded as not_observed (fail closed — never counted as pass).
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        import nflreadpy

        nflreadpy_version = getattr(nflreadpy, "__version__", "unknown")
    except Exception:  # offline tests without nflreadpy installed
        nflreadpy_version = None

    players_error: str | None = None
    players_index: dict[str, dict] | None = None
    players_identity_present: dict[str, bool] | None = None
    try:
        players_df = load_players()
        players_index, players_identity_present = build_players_index(players_df)
    except Exception as exc:
        players_error = f"{type(exc).__name__}: {exc}"

    season_results: list[dict] = []
    for season in SEASONS:  # ascending, deterministic report ordering
        week_call = f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='week')"
        reg_call = f"nflreadpy.load_player_stats(seasons=[{season}], summary_level='reg')"
        failed_calls: list[dict] = []
        week_df = reg_df = None
        try:
            week_df = load_week(season)
            failed_calls.append({"call": week_call, "status": "ok"})
        except Exception as exc:
            failed_calls.append({"call": week_call, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
        try:
            reg_df = load_reg(season)
            failed_calls.append({"call": reg_call, "status": "ok"})
        except Exception as exc:
            failed_calls.append({"call": reg_call, "status": "error", "error": f"{type(exc).__name__}: {exc}"})

        if week_df is None or reg_df is None:
            season_results.append(_season_error_result(season, failed_calls))
            continue

        result = inspect_season(season, week_df, reg_df, players_index, players_identity_present)
        season_results.append(result)

    # --- overall decision --------------------------------------------------------
    seasons_with_definitive_failures = sorted(
        r["season"] for r in season_results if r["definitive_failures"]
    )
    seasons_with_followup_items = sorted(
        r["season"] for r in season_results if r["followup_items"]
    )
    seasons_not_observed = sorted(
        r["season"] for r in season_results if r["statuses"]["source_rows_exist"] == STATUS_NOT_OBSERVED
    )
    seasons_fully_cleared = sorted(
        r["season"]
        for r in season_results
        if not r["definitive_failures"]
        and not r["followup_items"]
        and r["statuses"]["source_rows_exist"] == STATUS_PASS
        and r["statuses"]["required_columns_present"] == STATUS_PASS
        and r["statuses"]["identity_join_sufficient"] == STATUS_PASS
        and r["statuses"]["schedule_method_observed"] == STATUS_PASS
        and r["statuses"]["existing_schema_compatible"] == STATUS_PASS
        and r["statuses"]["existing_validator_semantics_compatible"] == STATUS_PASS
        and r["statuses"]["builder_compatible"]
        in ("compatible_as_is", "compatible_with_explicit_week_span_parameter")
    )

    if seasons_with_definitive_failures:
        decision = "do_not_pursue_player_season_coverage_2015_2020_under_current_source_contract"
        decision_basis = (
            "observed source evidence definitively fails required checks for season(s) "
            f"{seasons_with_definitive_failures}: "
            + "; ".join(
                f"{r['season']}: {r['definitive_failures']}"
                for r in season_results
                if r["definitive_failures"]
            )
        )
    elif len(seasons_fully_cleared) == len(SEASONS):
        decision = "may_open_player_season_coverage_2015_2020_candidate_build_issue"
        decision_basis = (
            "every season 2015-2020 cleared source_rows_exist, required_columns_present, "
            "identity_join_sufficient, schedule_method_observed, existing_schema_compatible, "
            "existing_validator_semantics_compatible, and a builder_compatible path"
        )
    else:
        decision = "player_season_coverage_2015_2020_source_audit_requires_followup"
        unresolved = sorted(set(seasons_with_followup_items) | set(seasons_not_observed))
        decision_basis = (
            f"season(s) {unresolved} have unresolved followup items or were not observed: "
            + "; ".join(
                f"{r['season']}: {r['followup_items']}"
                for r in season_results
                if r["followup_items"]
            )
        )
    assert decision in ALLOWED_DECISIONS

    # Narrowest schedule-span rule supported by evidence (never assumed from 2021+).
    observed_rules = {
        r["season"]: r["observed_week_span_rule"] for r in season_results
    }
    spans = {
        (r["availability"]["min_reg_week"], r["availability"]["max_reg_week"])
        for r in season_results
        if r["availability"] and r["observed_week_span_rule"]
    }
    if not spans:
        narrowest_rule = (
            "no schedule-span rule can be stated: no season's REG week span was observed "
            "from source in this run"
        )
    elif len(spans) == 1:
        lo, hi = next(iter(spans))
        narrowest_rule = (
            f"every observed season 2015-2020 exposes exactly REG weeks {lo}-{hi}; the "
            f"narrowest supported rule is EXPECTED_REG_WEEKS = set(range({lo}, {hi + 1})) "
            "for these seasons only (NOT the 2021+ range(1, 19) rule)"
        )
    else:
        narrowest_rule = (
            "observed seasons expose DIFFERENT REG week spans "
            f"({sorted(spans)}); a single shared week-span constant is NOT supported — a "
            "later build must parameterize the expected span per season"
        )

    payload = {
        "report_id": "player_season_coverage_v0_2015_2020_source_availability",
        "status": "source_availability_evidence_report_not_an_artifact",
        "tracking_issue": "TIBER-Data#216",
        "strategy_context_not_authority": (
            "TIBER-Strategy#3 (research/proven-production-discount-field-note-v0, "
            "commit 9992648, docs/design/proven-production-discount-research-note-v0.md) "
            "motivates why deeper player history may later matter; it carries NO authority "
            "over TIBER-Data behavior and did not influence this audit's verdict."
        ),
        "generated_at": generated_at,
        "environment": {
            "python_version": platform.python_version(),
            "nflreadpy_version": nflreadpy_version,
        },
        "seasons_inspected": list(SEASONS),
        "season_type_inspected": SEASON_TYPE,
        "positions_inspected": list(INCLUDED_POSITIONS),
        "sources_authorized": [
            "nflreadpy.load_player_stats(seasons=[year], summary_level='week')",
            "nflreadpy.load_player_stats(seasons=[year], summary_level='reg')",
            "nflreadpy.load_players()",
        ],
        "approved_source_allowlist_reference": "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json",
        "load_players_call": {
            "call": "nflreadpy.load_players()",
            "status": "error" if players_error else "ok",
            **({"error": players_error} if players_error else {}),
        },
        "non_goals": [
            "no candidate artifact is built or emitted (no player-season rows exist in this report)",
            "no promoted artifact or manifest is modified",
            "no README/contract support window is widened; 2021-2025 REG remains the only promoted window",
            "no ADP, market, ranking, or advice data is ingested or evaluated",
            "no Forecast mirror refresh, rerun, validation, or feature change is performed or authorized",
            "no bust/rebound cohort is computed and no operator-supplied player examples are evaluated",
        ],
        "audit_may_establish_only": [
            "source_rows_exist",
            "builder_compatible",
            "candidate_build_may_be_proposed",
        ],
        "audit_may_not_establish": [
            "candidate_built",
            "promoted",
            "Forecast_ready",
            "2015-2025_available_to_consumers",
        ],
        "schedule_methodology": {
            "rule_not_reused": "EXPECTED_REG_WEEKS = set(range(1, 19)) (2021+ assumption) was NOT applied",
            "absolute_bounds_applied": f"weeks must fall within {ABSOLUTE_MIN_REG_WEEK}-{ABSOLUTE_MAX_REG_WEEK}; span itself is taken from evidence",
            "observed_week_span_rules_by_season": observed_rules,
            "narrowest_supported_rule": narrowest_rule,
        },
        "seasons": season_results,
        "summary": {
            "seasons_fully_cleared": seasons_fully_cleared,
            "seasons_with_definitive_failures": seasons_with_definitive_failures,
            "seasons_with_followup_items": seasons_with_followup_items,
            "seasons_not_observed": seasons_not_observed,
        },
        "builder_reuse_assessment": {
            "reusable_unchanged": [
                "schemas/player_season_coverage_v0.schema.json is season-agnostic (season >= 1900; "
                "no week-span constant) and needs no change for 2015-2020 rows",
                "scripts/validate_player_season_coverage_v0.py semantics (unique "
                "player_id+season+season_type grain, explicit REG season_type, approved-source-prefix "
                "refs, null-vs-zero honesty, no availability assertions) contain no season-shape "
                "assumption and need no change",
                "the approved source allowlist (nflreadpy.load_player_stats(, nflreadpy.load_players() "
                "call family) is unchanged for these seasons",
            ],
            "not_reusable_as_is": [
                "EXPECTED_REG_WEEKS = set(range(1, 19)) in "
                "scripts/build_player_season_coverage_2021_candidate.py fails closed on any season "
                "whose observed REG span is not exactly weeks 1-18; a 2015-2020 build must take an "
                "explicit per-season expected-week-span constant justified by this audit's observations",
                "COVERAGE_STATUS_RULE (full_season: weeks_observed >= 15) is calibrated to a 17-game/"
                "18-week season; for a shorter observed span the threshold's meaning changes "
                "(15 of 17 vs 15 of 18 weeks) and must be explicitly restated and re-justified, not "
                "silently reused",
                "the 17-game games cap and bye/trade allowances assumed by the 2021+ builders must be "
                "re-derived from the observed max games and week span for each older season",
            ],
            "must_not_change": [
                "the 2021 and 2022-2025 builders themselves (out of scope for this audit and for any "
                "follow-up 2015-2020 build)",
                "the promoted artifact, its manifest, the schema, the validator, and the source allowlist",
            ],
        },
        "decision": decision,
        "decision_basis": decision_basis,
        "decisions_not_emitted_and_not_authorized": [
            "candidate build (a later issue must separately authorize it)",
            "promotion of any artifact",
            "support-window widening to 2015-2025 anywhere",
            "Forecast mirror refresh, rerun, or validation",
            "ADP or market-data ingestion",
            "rankings, projections, advice, or product behavior",
        ],
        "comparison_to_promoted_2021_2025": {
            "promoted_artifact": "exports/promoted/nfl/player_season_coverage_v0.json",
            "promoted_manifest": PROMOTED_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(),
            "promoted_seasons": promoted_manifest.get("seasons"),
            "promoted_counts": promoted_manifest.get("counts"),
        },
    }
    return payload


def render_markdown(payload: dict) -> str:
    lines: list[str] = []
    lines.append("# Source-Availability Report: `player_season_coverage_v0` — 2015-2020 REG")
    lines.append("")
    lines.append(f"- **Generated at:** {payload['generated_at']}")
    lines.append(f"- **Tracking issue:** {payload['tracking_issue']}")
    lines.append(f"- **Status:** `{payload['status']}`")
    env = payload["environment"]
    lines.append(
        f"- **Environment:** Python {env['python_version']}, nflreadpy {env['nflreadpy_version']}"
    )
    lines.append(
        "- **Scope:** seasons 2015-2020, season_type REG, positions QB/RB/WR/TE, approved "
        "source family only (`nflreadpy.load_player_stats`, `nflreadpy.load_players`). "
        "This report is aggregate evidence only: it is **not** a candidate artifact, **not** "
        "a promoted artifact, carries **no** player-level rows, and authorizes **no** "
        "candidate build, promotion, Forecast behavior, or product behavior."
    )
    lines.append(
        "- **Strategy context (not authority):** " + payload["strategy_context_not_authority"]
    )
    lines.append("")
    lines.append("## What this audit may and may not establish")
    lines.append("")
    lines.append("May establish: " + ", ".join(f"`{x}`" for x in payload["audit_may_establish_only"]))
    lines.append("")
    lines.append("May NOT establish: " + ", ".join(f"`{x}`" for x in payload["audit_may_not_establish"]))
    lines.append("")
    lines.append("## Sources authorized and called")
    lines.append("")
    for s in payload["sources_authorized"]:
        lines.append(f"- `{s}`")
    lp = payload["load_players_call"]
    lines.append(f"- `nflreadpy.load_players()` status: **{lp['status']}**" + (f" — `{lp.get('error')}`" if lp.get("error") else ""))
    lines.append("")
    lines.append("## Schedule methodology")
    lines.append("")
    sm = payload["schedule_methodology"]
    lines.append(f"- Rule deliberately not reused: `{sm['rule_not_reused']}`")
    lines.append(f"- Bounds applied: {sm['absolute_bounds_applied']}")
    lines.append(f"- **Narrowest supported rule from evidence:** {sm['narrowest_supported_rule']}")
    lines.append("")
    lines.append("## Per-season results")
    lines.append("")
    lines.append(
        "| season | source calls | week rows (all/REG) | REG-summary rows (all/QB+RB+WR+TE) | "
        "unique players | REG weeks observed | gaps | dup grain | identity join |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in payload["seasons"]:
        a = r["availability"]
        calls = "ok" if all(c["status"] == "ok" for c in r["source_calls"]) else "ERROR"
        if a is None:
            lines.append(
                f"| {r['season']} | {calls} | not observed | not observed | not observed | "
                "not observed | — | — | not observed |"
            )
            continue
        weeks = (
            f"{a['min_reg_week']}-{a['max_reg_week']}"
            if a["min_reg_week"] is not None
            else "none"
        )
        idn = r["identity_age_draft"]
        lines.append(
            f"| {r['season']} | {calls} | {a['week_level_rows_total']}/{a['week_level_rows_reg']} | "
            f"{a['reg_level_rows_total']}/{a['reg_level_rows_reg_qb_rb_wr_te']} | "
            f"{a['unique_players_all_positions']} | {weeks} | {a['week_gaps'] or 'none'} | "
            f"{a['duplicate_grain_pairs']} | {idn['identity_join_rate_gsis_id']} |"
        )
    lines.append("")
    lines.append("### Per-season statuses (kept separate per #216)")
    lines.append("")
    status_keys = [
        "source_rows_exist",
        "required_columns_present",
        "identity_join_sufficient",
        "schedule_method_observed",
        "existing_schema_compatible",
        "existing_validator_semantics_compatible",
        "builder_compatible",
    ]
    lines.append("| season | " + " | ".join(status_keys) + " |")
    lines.append("|---|" + "---|" * len(status_keys))
    for r in payload["seasons"]:
        lines.append(
            f"| {r['season']} | " + " | ".join(str(r["statuses"][k]) for k in status_keys) + " |"
        )
    lines.append("")
    for r in payload["seasons"]:
        lines.append(f"### Season {r['season']}")
        lines.append("")
        for c in r["source_calls"]:
            suffix = f" — `{c.get('error')}`" if c.get("error") else ""
            lines.append(f"- `{c['call']}`: **{c['status']}**{suffix}")
        if r["availability"] is None:
            lines.append(
                "- Not observed: source calls failed, so availability for this season is "
                "**unknown** (this is an access failure, not evidence the source lacks the season)."
            )
            lines.append("")
            continue
        a = r["availability"]
        lines.append(f"- Week-level rows: {a['week_level_rows_total']} total, {a['week_level_rows_reg']} REG")
        lines.append(
            f"- REG-summary rows: {a['reg_level_rows_total']} total, "
            f"{a['reg_level_rows_reg_qb_rb_wr_te']} QB/RB/WR/TE"
        )
        by_pos = a["row_counts_by_position_reg_level"]
        by_pl = a["player_counts_by_position"]
        lines.append(
            "- Rows by position: "
            + ", ".join(f"{p}: {by_pos[p]} rows / {by_pl[p]} players" for p in payload["positions_inspected"])
            + f"; unique players total: {a['unique_players_all_positions']}"
        )
        lines.append(
            f"- REG weeks observed: {a['reg_week_numbers_observed']} "
            f"(min {a['min_reg_week']}, max {a['max_reg_week']}, gaps {a['week_gaps'] or 'none'}, "
            f"unexpected {a['unexpected_week_values'] or 'none'})"
        )
        lines.append(
            f"- Max games (REG summary): {a['max_games_reg_level']}; max distinct weeks any player: "
            f"{a['max_weeks_observed_any_player']}; duplicate grain pairs: {a['duplicate_grain_pairs']}"
        )
        sc = r["schema_compatibility"]
        lines.append(
            f"- Missing required columns: week-level {sc['missing_required_week_level'] or 'none'}, "
            f"reg-level {sc['missing_required_reg_level'] or 'none'}; missing optional reg-level: "
            f"{sc['missing_optional_reg_level'] or 'none'}"
        )
        idn = r["identity_age_draft"]
        lines.append(
            f"- Identity join (gsis_id): {idn['identity_join_rate_gsis_id']} "
            f"({idn['players_joined']}/{idn['players_total']}; floor {idn['identity_join_rate_floor']})"
        )
        field_rates = idn["field_availability_for_joined_players"]
        lines.append(
            "- Identity field availability: "
            + ", ".join(f"{f}: {field_rates[f].get('rate')}" for f in IDENTITY_FIELDS_REPORTED)
        )
        lines.append("- Null observations (REG summary, QB/RB/WR/TE):")
        for field, obs in r["null_observations"].items():
            lines.append(
                f"  - `{field}`: {obs.get('nulls')}/{obs.get('total')} null (rate {obs.get('rate')})"
                + (f" — {obs['note']}" if obs.get("note") else "")
            )
        if r["followup_items"]:
            lines.append("- Follow-up items: " + "; ".join(r["followup_items"]))
        if r["definitive_failures"]:
            lines.append("- Definitive failures: " + "; ".join(r["definitive_failures"]))
        lines.append("")
    lines.append("## Builder / validator / schema reuse assessment")
    lines.append("")
    bra = payload["builder_reuse_assessment"]
    lines.append("Reusable unchanged:")
    lines.append("")
    for item in bra["reusable_unchanged"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("NOT reusable as-is:")
    lines.append("")
    for item in bra["not_reusable_as_is"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Must not change:")
    lines.append("")
    for item in bra["must_not_change"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("```text")
    lines.append(payload["decision"])
    lines.append("```")
    lines.append("")
    lines.append(f"- Basis: {payload['decision_basis']}")
    lines.append("")
    summary = payload["summary"]
    lines.append(f"- Seasons fully cleared: {summary['seasons_fully_cleared'] or 'none'}")
    lines.append(
        f"- Seasons with definitive failures: {summary['seasons_with_definitive_failures'] or 'none'}"
    )
    lines.append(f"- Seasons with follow-up items: {summary['seasons_with_followup_items'] or 'none'}")
    lines.append(f"- Seasons not observed: {summary['seasons_not_observed'] or 'none'}")
    lines.append("")
    lines.append("### Explicitly NOT emitted / NOT authorized by this report")
    lines.append("")
    for item in payload["decisions_not_emitted_and_not_authorized"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(
        "This report is aggregate evidence under `docs/reports/`. It is not a candidate "
        "artifact and not a promoted dataset. The decision above may authorize only a later "
        "issue **proposal**; the phrase \"2015-2025 is available\" remains prohibited until a "
        "later candidate build, independent review, and explicit promotion are complete."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    import nflreadpy as nfl

    promoted_manifest = json.loads(PROMOTED_MANIFEST_PATH.read_text(encoding="utf-8"))

    payload = run_audit(
        load_week=lambda season: nfl.load_player_stats(seasons=[season], summary_level="week"),
        load_reg=lambda season: nfl.load_player_stats(seasons=[season], summary_level="reg"),
        load_players=nfl.load_players,
        promoted_manifest=promoted_manifest,
    )

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(f"{json.dumps(payload, indent=2, allow_nan=False)}\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(payload), encoding="utf-8")

    print(f"Wrote {REPORT_JSON_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_MD_PATH.relative_to(REPO_ROOT)}")
    print(f"Decision: {payload['decision']}")

    if payload["decision"] == "may_open_player_season_coverage_2015_2020_candidate_build_issue":
        return 0
    if payload["decision"] == "player_season_coverage_2015_2020_source_audit_requires_followup":
        return 2
    return 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
