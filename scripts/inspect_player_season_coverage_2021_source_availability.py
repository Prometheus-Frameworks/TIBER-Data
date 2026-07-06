"""Inspect 2021 REG source availability for the player_season_coverage_v0 family.

TIBER-Data #198: source-feasibility check only. Forecast PR #134 (TIBER-Forecast)
designed additional validation for the player-history feature contract and found it
blocked on whether TIBER-Data can source, verify, and govern 2021 REG player-season
coverage from the SAME approved source family used by the promoted 2022-2025
`player_season_coverage_v0` artifact (nflreadpy.load_player_stats + load_players).

This script is a NON-PROMOTIONAL inspection/reporting tool. It:

- calls nflreadpy.load_player_stats(seasons=[2021], summary_level='week' and 'reg')
  and nflreadpy.load_players() — the exact approved source allowlist recorded in
  exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json;
- measures 2021 REG row/player counts for QB/RB/WR/TE, schema compatibility with
  scripts/build_player_season_coverage_2022_2025.py (same column-candidate lists),
  identity/age/draft join coverage from load_players(), week-span compatibility with
  the existing 17-game / 18-week coverage_status methodology, and null/missing-field
  behavior;
- writes an evidence report to docs/reports/ (markdown + json) and emits exactly one
  narrow decision from the allowed set in #198.

It must NOT and does not:
- write anything under data/processed/, data/gold/, or exports/;
- build or modify a candidate or promoted artifact (no per-player records are emitted);
- touch Forecast mirrors or Forecast behavior;
- authorize promotion, threshold acceptance, or production/product use.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2021-source-availability.md"
REPORT_JSON_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2021-source-availability.json"
PROMOTED_ARTIFACT_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"

SEASON = 2021
SEASON_TYPE = "REG"
INCLUDED_POSITIONS = ("QB", "RB", "WR", "TE")

# Column-candidate lists copied from scripts/build_player_season_coverage_2022_2025.py
# (the promoted builder). "required" mirrors which resolutions that builder treats as
# hard requirements (_resolve_column(..., required=True)).
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
    "espn_id",
]

# 2021+ season shape assumed by the promoted builder's coverage_status rule:
# 17 games per team across REG week numbers 1-18 (see COVERAGE_STATUS_RULE in
# scripts/build_player_season_coverage_2022_2025.py).
EXPECTED_MAX_REG_WEEK = 18
FULL_SEASON_WEEKS_THRESHOLD = 15

ALLOWED_DECISIONS = (
    "may_open_player_season_coverage_2021_candidate_build_issue",
    "player_season_coverage_2021_source_unavailable_blocks_additional_validation",
    "player_season_coverage_2021_requires_source_boundary_redesign",
    "player_season_coverage_2021_source_feasibility_inconclusive_requires_followup",
)

# Minimum identity-join rate for load_players() to be considered compatible with the
# 2022-2025 build (which observed 100% source_verified identity joins).
IDENTITY_JOIN_RATE_FLOOR = 0.95


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


def assess_2021_source_availability(week_df, reg_df, players_df, promoted_meta: dict) -> dict:
    """Pure assessment: takes already-loaded source frames, returns the report payload.

    Emits evidence + exactly one decision from ALLOWED_DECISIONS. Never emits
    per-player artifact records.
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    week_columns = set(week_df.columns)
    reg_columns = set(reg_df.columns)
    players_columns = set(players_df.columns)

    week_resolved = _resolve_columns(week_columns, WEEK_LEVEL_COLUMNS)
    reg_resolved = _resolve_columns(reg_columns, REG_LEVEL_COLUMNS)
    players_identity_present = {c: (c in players_columns) for c in PLAYERS_IDENTITY_COLUMNS}

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
    wk_position_col = "position" if "position" in week_columns else None

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
        pid = str(r.get(reg_player_id_col) or "").strip()
        if not pid:
            continue
        row_counts_by_position[pos] += 1
        players_by_position[pos].add(pid)
        key = (pid, SEASON, SEASON_TYPE)
        if key in grain_seen:
            duplicate_grain_pairs += 1
        grain_seen.add(key)

    week_row_counts_by_position: dict[str, int] = {p: 0 for p in INCLUDED_POSITIONS}
    if wk_position_col:
        for r in week_reg_rows:
            pos = str(r.get(wk_position_col) or "").strip().upper()
            if pos in week_row_counts_by_position:
                week_row_counts_by_position[pos] += 1

    reg_week_numbers = sorted(
        {int(r[wk_week_col]) for r in week_reg_rows if not _is_null(r.get(wk_week_col))}
    ) if wk_week_col else []

    weeks_by_player: dict[str, set[int]] = defaultdict(set)
    if wk_player_id_col and wk_week_col:
        for r in week_reg_rows:
            pid = str(r.get(wk_player_id_col) or "").strip()
            if pid and not _is_null(r.get(wk_week_col)):
                weeks_by_player[pid].add(int(r[wk_week_col]))
    max_weeks_observed_any_player = max((len(w) for w in weeks_by_player.values()), default=0)

    games_col = _col(reg_resolved, "games")
    games_values = [r.get(games_col) for r in reg_position_rows if not _is_null(r.get(games_col))]
    max_games = max((int(g) for g in games_values), default=None) if games_values else None
    games_null = sum(1 for r in reg_position_rows if _is_null(r.get(games_col)))

    # Identity join against load_players(), keyed by gsis_id exactly like the builder.
    players_records = _records_from_dataframe(players_df)
    players_index: dict[str, dict] = {}
    if players_identity_present.get("gsis_id"):
        for row in players_records:
            gsis_id = row.get("gsis_id")
            if gsis_id is None or str(gsis_id).strip() == "":
                continue
            players_index[str(gsis_id).strip()] = row

    all_2021_player_ids = set().union(*players_by_position.values()) if any(players_by_position.values()) else set()
    joined = [pid for pid in all_2021_player_ids if pid in players_index]
    identity_join_rate = round(len(joined) / len(all_2021_player_ids), 4) if all_2021_player_ids else None

    def _identity_field_rate(field: str) -> dict:
        if not players_identity_present.get(field):
            return {"available": None, "total": len(joined), "rate": None, "note": "column not present in load_players()"}
        available = sum(1 for pid in joined if not _is_null(players_index[pid].get(field)))
        return {
            "available": available,
            "total": len(joined),
            "rate": round(available / len(joined), 4) if joined else None,
        }

    identity_field_rates = {
        field: _identity_field_rate(field)
        for field in ("birth_date", "rookie_season", "draft_year", "draft_round", "draft_pick", "draft_team")
    }

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

    # --- checks --------------------------------------------------------------
    positions_all_present = all(row_counts_by_position[p] > 0 for p in INCLUDED_POSITIONS)
    week_span_compatible = (
        bool(reg_week_numbers)
        and set(reg_week_numbers) == set(range(1, EXPECTED_MAX_REG_WEEK + 1))
        and max_weeks_observed_any_player <= EXPECTED_MAX_REG_WEEK
    )
    games_cap_compatible = max_games is not None and max_games <= EXPECTED_MAX_REG_WEEK
    identity_join_compatible = identity_join_rate is not None and identity_join_rate >= IDENTITY_JOIN_RATE_FLOOR

    checks = {
        "week_level_2021_rows_exist": len(week_records_all) > 0,
        "reg_level_2021_rows_exist": len(reg_records_all) > 0,
        "week_level_reg_season_type_rows_exist": len(week_reg_rows) > 0,
        "required_week_level_columns_present": not missing_required_week,
        "required_reg_level_columns_present": not missing_required_reg,
        "season_type_reg_emitted_by_source": SEASON_TYPE in week_season_types or SEASON_TYPE in reg_season_types,
        "all_four_positions_present": positions_all_present,
        "reg_week_span_1_to_18": week_span_compatible,
        "games_within_17_game_season_cap_plus_trade_allowance": games_cap_compatible,
        "grain_unique_player_season_season_type": duplicate_grain_pairs == 0,
        "load_players_gsis_join_available": players_identity_present.get("gsis_id", False),
        "identity_join_rate_at_or_above_floor": identity_join_compatible,
    }

    blocking_failures = [
        name
        for name in (
            "week_level_2021_rows_exist",
            "reg_level_2021_rows_exist",
            "week_level_reg_season_type_rows_exist",
            "season_type_reg_emitted_by_source",
            "all_four_positions_present",
        )
        if not checks[name]
    ]
    redesign_failures = [
        name
        for name in (
            "required_week_level_columns_present",
            "required_reg_level_columns_present",
            "reg_week_span_1_to_18",
            "games_within_17_game_season_cap_plus_trade_allowance",
            "grain_unique_player_season_season_type",
            "load_players_gsis_join_available",
            "identity_join_rate_at_or_above_floor",
        )
        if not checks[name]
    ]

    if blocking_failures:
        decision = "player_season_coverage_2021_source_unavailable_blocks_additional_validation"
        decision_basis = f"blocking source-availability checks failed: {blocking_failures}"
    elif redesign_failures:
        decision = "player_season_coverage_2021_requires_source_boundary_redesign"
        decision_basis = f"2021 rows exist but compatibility checks failed: {redesign_failures}"
    else:
        decision = "may_open_player_season_coverage_2021_candidate_build_issue"
        decision_basis = "all source-availability and builder-compatibility checks passed"
    assert decision in ALLOWED_DECISIONS

    promoted_counts = promoted_meta.get("counts", {})

    return {
        "report_id": "player_season_coverage_v0_2021_source_availability",
        "status": "source_availability_evidence_report_not_an_artifact",
        "tracking_issue": "TIBER-Data#198",
        "forecast_context": [
            "Prometheus-Frameworks/TIBER-Forecast#133",
            "Prometheus-Frameworks/TIBER-Forecast#134 (merged 2517270)",
        ],
        "generated_at": generated_at,
        "season_inspected": SEASON,
        "season_type_inspected": SEASON_TYPE,
        "positions_inspected": list(INCLUDED_POSITIONS),
        "sources_inspected": [
            "nflreadpy.load_player_stats(seasons=[2021], summary_level='week')",
            "nflreadpy.load_player_stats(seasons=[2021], summary_level='reg')",
            "nflreadpy.load_players()",
        ],
        "approved_source_allowlist_reference": "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json",
        "non_goals": [
            "no candidate artifact is built or emitted",
            "no promoted artifact is modified",
            "no Forecast mirror/rerun/validation is performed or authorized",
            "no promotion, threshold acceptance, production binding, or product behavior is authorized",
        ],
        "availability": {
            "week_level_rows_total": len(week_records_all),
            "week_level_rows_reg": len(week_reg_rows),
            "reg_level_rows_total": len(reg_records_all),
            "reg_level_rows_reg_qb_rb_wr_te": len(reg_position_rows),
            "season_type_values_week_level": week_season_types,
            "season_type_values_reg_level": reg_season_types,
            "row_counts_by_position_reg_level": row_counts_by_position,
            "player_counts_by_position": {p: len(players_by_position[p]) for p in INCLUDED_POSITIONS},
            "unique_players_all_positions": len(all_2021_player_ids),
            "week_level_reg_row_counts_by_position": week_row_counts_by_position if wk_position_col else None,
            "reg_week_numbers_observed": reg_week_numbers,
            "max_weeks_observed_any_player": max_weeks_observed_any_player,
            "max_games_reg_level": max_games,
            "games_null_count": games_null,
            "duplicate_grain_pairs": duplicate_grain_pairs,
        },
        "schema_compatibility": {
            "week_level_columns": week_resolved,
            "reg_level_columns": reg_resolved,
            "missing_required_week_level": missing_required_week,
            "missing_required_reg_level": missing_required_reg,
            "missing_optional_reg_level": missing_optional_reg,
            "load_players_identity_columns_present": players_identity_present,
        },
        "identity_age_draft": {
            "identity_join_rate_gsis_id": identity_join_rate,
            "identity_join_rate_floor": IDENTITY_JOIN_RATE_FLOOR,
            "players_joined": len(joined),
            "players_total": len(all_2021_player_ids),
            "field_availability_for_joined_players": identity_field_rates,
        },
        "null_observations_reg_level": null_observations,
        "methodology_compatibility": {
            "expected_max_reg_week": EXPECTED_MAX_REG_WEEK,
            "full_season_weeks_threshold": FULL_SEASON_WEEKS_THRESHOLD,
            "hypothesis_from_forecast_pr_134": (
                "2021 is likely methodology-compatible because it is a 17-game / 18-week season, "
                "unlike pre-2021 seasons."
            ),
            "hypothesis_verified": week_span_compatible and games_cap_compatible,
        },
        "checks": checks,
        "blocking_failures": blocking_failures,
        "redesign_failures": redesign_failures,
        "comparison_to_promoted_2022_2025": {
            "promoted_artifact": PROMOTED_ARTIFACT_PATH.relative_to(REPO_ROOT).as_posix(),
            "promoted_counts": promoted_counts,
            "promoted_seasons": promoted_meta.get("seasons"),
        },
        "decision": decision,
        "decision_basis": decision_basis,
        "decisions_not_emitted_and_not_authorized": [
            "promotion of any artifact",
            "Forecast mirror refresh",
            "Forecast controlled rerun",
            "player-history threshold acceptance",
            "leakage audit",
            "model wiring / seasonalPprModel.ts changes",
        ],
    }


def render_markdown(payload: dict) -> str:
    a = payload["availability"]
    sc = payload["schema_compatibility"]
    idn = payload["identity_age_draft"]
    checks = payload["checks"]
    promoted = payload["comparison_to_promoted_2022_2025"]
    promoted_by_season = (promoted.get("promoted_counts") or {}).get("by_season", {})

    def _yn(v: bool) -> str:
        return "PASS" if v else "FAIL"

    lines: list[str] = []
    lines.append("# Source-Availability Report: `player_season_coverage_v0` — 2021 REG")
    lines.append("")
    lines.append(f"- **Generated at:** {payload['generated_at']}")
    lines.append(f"- **Tracking issue:** {payload['tracking_issue']}")
    lines.append(
        "- **Forecast context (not source authority):** "
        + ", ".join(payload["forecast_context"])
    )
    lines.append(f"- **Status:** `{payload['status']}`")
    lines.append(
        "- **Scope:** season 2021, season_type REG, positions QB/RB/WR/TE, approved source "
        "family only (`nflreadpy.load_player_stats`, `nflreadpy.load_players`). "
        "This report is evidence only: it is **not** a candidate artifact, **not** a promoted "
        "artifact, and authorizes **no** Forecast behavior."
    )
    lines.append("")
    lines.append("## Sources inspected")
    lines.append("")
    for s in payload["sources_inspected"]:
        lines.append(f"- `{s}`")
    lines.append("")
    lines.append("## 2021 REG availability")
    lines.append("")
    lines.append(f"- Week-level rows (all season types): {a['week_level_rows_total']}")
    lines.append(f"- Week-level rows (REG): {a['week_level_rows_reg']}")
    lines.append(f"- REG-summary rows (all positions): {a['reg_level_rows_total']}")
    lines.append(f"- REG-summary rows (QB/RB/WR/TE): {a['reg_level_rows_reg_qb_rb_wr_te']}")
    lines.append(f"- `season_type` values seen (week level): {a['season_type_values_week_level']}")
    lines.append(f"- `season_type` values seen (reg level): {a['season_type_values_reg_level']}")
    lines.append("")
    lines.append("### Row and player counts by position (REG summary level)")
    lines.append("")
    lines.append("| position | 2021 rows | 2021 unique players | promoted 2022 rows | promoted 2023 rows | promoted 2024 rows | promoted 2025 rows |")
    lines.append("|---|---|---|---|---|---|---|")
    promoted_by_pos_note = "row counts by season+position are not stored in manifest counts; see per-season totals below"
    by_pos = a["row_counts_by_position_reg_level"]
    players_by_pos = a["player_counts_by_position"]
    for p in payload["positions_inspected"]:
        lines.append(f"| {p} | {by_pos[p]} | {players_by_pos[p]} | — | — | — | — |")
    lines.append("")
    lines.append(
        f"- Unique 2021 players across all four positions: {a['unique_players_all_positions']}"
    )
    lines.append(
        "- Promoted 2022-2025 per-season row totals for comparison: "
        + ", ".join(f"{k}: {v}" for k, v in sorted(promoted_by_season.items()))
        + f" ({promoted_by_pos_note})."
    )
    lines.append("")
    lines.append("## Schema compatibility with the 2022-2025 builder")
    lines.append("")
    lines.append(f"- Missing REQUIRED week-level columns: {sc['missing_required_week_level'] or 'none'}")
    lines.append(f"- Missing REQUIRED reg-level columns: {sc['missing_required_reg_level'] or 'none'}")
    lines.append(f"- Missing OPTIONAL reg-level columns: {sc['missing_optional_reg_level'] or 'none'}")
    lines.append("")
    lines.append("| builder field | resolved 2021 column | required | present |")
    lines.append("|---|---|---|---|")
    for field, meta in {**sc["week_level_columns"], **sc["reg_level_columns"]}.items():
        lines.append(
            f"| `{field}` | `{meta['resolved_column']}` | {'yes' if meta['required'] else 'no'} | {'yes' if meta['present'] else 'NO'} |"
        )
    lines.append("")
    lines.append("## Identity / age / draft availability (`load_players()`)")
    lines.append("")
    lines.append(
        f"- gsis_id join rate for 2021 QB/RB/WR/TE players: {idn['identity_join_rate_gsis_id']} "
        f"({idn['players_joined']}/{idn['players_total']}; floor {idn['identity_join_rate_floor']})"
    )
    lines.append("")
    lines.append("| field | available | of joined | rate |")
    lines.append("|---|---|---|---|")
    for field, rate in idn["field_availability_for_joined_players"].items():
        lines.append(f"| `{field}` | {rate.get('available')} | {rate.get('total')} | {rate.get('rate')} |")
    lines.append("")
    lines.append("## Null / missing-field observations (2021 REG, QB/RB/WR/TE)")
    lines.append("")
    lines.append("| reg-level field | nulls | total | rate |")
    lines.append("|---|---|---|---|")
    for field, obs in payload["null_observations_reg_level"].items():
        lines.append(f"| `{field}` | {obs.get('nulls')} | {obs.get('total')} | {obs.get('rate')} |")
    lines.append("")
    lines.append("## Coverage-status methodology compatibility")
    lines.append("")
    mc = payload["methodology_compatibility"]
    lines.append(f"- REG week numbers observed in 2021: {a['reg_week_numbers_observed']}")
    lines.append(f"- Max distinct REG weeks observed by any single player: {a['max_weeks_observed_any_player']}")
    lines.append(f"- Max `games` at reg level: {a['max_games_reg_level']} (null `games`: {a['games_null_count']})")
    lines.append(f"- Duplicate `(player_id, season, season_type)` pairs: {a['duplicate_grain_pairs']}")
    lines.append(f"- Forecast PR #134 hypothesis: \"{mc['hypothesis_from_forecast_pr_134']}\"")
    lines.append(f"- Hypothesis verified from TIBER-Data evidence: **{mc['hypothesis_verified']}**")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| check | result |")
    lines.append("|---|---|")
    for name, ok in checks.items():
        lines.append(f"| `{name}` | {_yn(ok)} |")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("```text")
    lines.append(payload["decision"])
    lines.append("```")
    lines.append("")
    lines.append(f"- Basis: {payload['decision_basis']}")
    lines.append("")
    lines.append("### Explicitly NOT emitted / NOT authorized by this report")
    lines.append("")
    for item in payload["decisions_not_emitted_and_not_authorized"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(
        "This report is evidence under `docs/reports/`. It is not a candidate artifact, not a "
        "promoted dataset, and does not authorize a 2021 build; a follow-up TIBER-Data issue "
        "must explicitly authorize any candidate build."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    import nflreadpy as nfl

    promoted_meta = json.loads(PROMOTED_ARTIFACT_PATH.read_text(encoding="utf-8"))
    promoted_meta.pop("records", None)

    week_df = nfl.load_player_stats(seasons=[SEASON], summary_level="week")
    reg_df = nfl.load_player_stats(seasons=[SEASON], summary_level="reg")
    players_df = nfl.load_players()

    payload = assess_2021_source_availability(week_df, reg_df, players_df, promoted_meta)

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(f"{json.dumps(payload, indent=2, allow_nan=False)}\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(payload), encoding="utf-8")

    print(f"Wrote {REPORT_JSON_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_MD_PATH.relative_to(REPO_ROOT)}")
    print(f"Decision: {payload['decision']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
