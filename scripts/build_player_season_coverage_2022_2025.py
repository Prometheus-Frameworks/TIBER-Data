"""Build the bounded player_season_coverage_v0 candidate artifact for 2022-2025.

Follows the source boundary defined in docs/specs/player-season-coverage-v0-source-boundary.md
(TIBER-Data #188 / PR #189). This script touches real source/data paths under the
approved, bounded scope for TIBER-Data #190:

- seasons: 2022, 2023, 2024, 2025
- season_type: REG only (POST is explicitly out of scope for this slice)
- positions: QB, RB, WR, TE (consistent with existing 2025 source-backed evidence
  builders: build_player_weekly_ppr_outcomes_source_backed_2025.py,
  build_player_weekly_usage_source_backed_2025.py,
  build_roster_player_team_map_source_backed_2025.py)
- sources: nflreadpy.load_player_stats (week + reg summary levels) and
  nflreadpy.load_players(). nflreadpy.load_rosters_weekly is NOT called; team/roster
  context is instead derived from the team-of-record on each week-level production
  row already pulled from load_player_stats, which keeps the source surface to one
  approved family and avoids a second, much larger weekly pull. This is documented
  per-row in coverage_notes and in the coverage report.

This artifact is a CANDIDATE / evidence artifact, not a promoted dataset. It does not
authorize Forecast consumption. Active/inactive/IR/practice-squad gameday status is
never asserted in this output.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import nflreadpy as nfl

SEASONS = [2022, 2023, 2024, 2025]
SEASON_TYPE = "REG"
INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}

OUTPUT_PATH = Path("data/processed/evidence/player_season_coverage_2022_2025.source_backed.json")
REPORT_MD_PATH = Path("docs/reports/player-season-coverage-v0-2022-2025.md")
REPORT_JSON_PATH = Path("docs/reports/player-season-coverage-v0-2022-2025.json")

PRIMARY_TEAM_RULE = (
    "most weeks_observed in REG week-level production rows for the season; "
    "ties broken by earliest week of first appearance, then alphabetical team code"
)
TEAM_CONTEXT_SOURCE_NOTE = (
    "Team context (teams[], primary_team, team_weeks) is derived from the team-of-record "
    "on each week-level row in nflreadpy.load_player_stats (game appearances with a "
    "recorded stat line), not from a separate roster-membership pull "
    "(nflreadpy.load_rosters_weekly was not called for this build). This reflects teams "
    "the player recorded production for in a given week, not full roster-membership weeks "
    "(e.g. it excludes weeks rostered but inactive/practice-squad with no recorded stat line)."
)
COVERAGE_STATUS_RULE = (
    "full_season: weeks_observed >= 15; partial_season: 1 < weeks_observed < 15; "
    "single_week: weeks_observed == 1. weeks_observed counts distinct REG week NUMBERS "
    "(1-18, the full week span of a 2021+ season) with a recorded stat line, not games-against-the-"
    "17-per-team-game-cap; a traded player whose two teams' bye weeks differ can validly reach 18."
)
AGE_REFERENCE_NOTE = "season_age computed against a fixed reference date of September 1 of `season`."


def _records_from_dataframe(df) -> list[dict]:
    if hasattr(df, "to_dicts"):
        return df.to_dicts()
    return df.to_dict("records")


def _json_safe_value(value):
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, float) and not math.isfinite(value):
            return None
    except TypeError:
        pass
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _resolve_column(columns: set[str], candidates: list[str], field_name: str, required: bool = True) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    if required:
        raise ValueError(
            f"Missing required column for '{field_name}'. Expected one of {candidates}, found columns={sorted(columns)}"
        )
    return None


def _round_or_none(value, ndigits: int = 4):
    if value is None:
        return None
    try:
        if isinstance(value, float) and (math.isnan(value) or not math.isfinite(value)):
            return None
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None


def _season_age(birth_date_value, season: int) -> float | None:
    if birth_date_value is None:
        return None
    if isinstance(birth_date_value, datetime):
        birth_date_value = birth_date_value.date()
    elif isinstance(birth_date_value, str):
        try:
            birth_date_value = date.fromisoformat(birth_date_value.strip()[:10])
        except ValueError:
            return None
    if not isinstance(birth_date_value, date):
        return None
    reference_date = date(season, 9, 1)
    days = (reference_date - birth_date_value).days
    if days < 0:
        return None
    return round(days / 365.25, 2)


def _load_players_index() -> dict[str, dict]:
    players_df = nfl.load_players()
    columns = set(players_df.columns)
    gsis_col = _resolve_column(columns, ["gsis_id"], "gsis_id")
    index: dict[str, dict] = {}
    for row in _records_from_dataframe(players_df):
        gsis_id = row.get(gsis_col)
        if gsis_id is None or str(gsis_id).strip() == "":
            continue
        index[str(gsis_id).strip()] = row
    return index


def _build_team_context(week_records: list[dict], season_col: str, week_col: str, team_col: str) -> dict[tuple[int, str], dict]:
    """Group week-level REG production rows by (season, player_id) into team context."""
    grouped: dict[tuple[int, str], list[tuple[int, str]]] = defaultdict(list)
    for row in week_records:
        player_id = row["_player_id"]
        season = int(row[season_col])
        week = int(row[week_col])
        team = str(row[team_col]).strip()
        if not team:
            continue
        grouped[(season, player_id)].append((week, team))

    context: dict[tuple[int, str], dict] = {}
    for key, entries in grouped.items():
        entries.sort(key=lambda e: e[0])
        first_seen_week: dict[str, int] = {}
        weeks_by_team: dict[str, set[int]] = defaultdict(set)
        for week, team in entries:
            weeks_by_team[team].add(week)
            if team not in first_seen_week:
                first_seen_week[team] = week

        teams_chronological = sorted(weeks_by_team.keys(), key=lambda t: first_seen_week[t])
        team_weeks = [
            {"team": team, "weeks_observed": len(weeks_by_team[team])} for team in teams_chronological
        ]
        team_weeks.sort(key=lambda tw: (-tw["weeks_observed"], first_seen_week[tw["team"]], tw["team"]))
        primary_team = team_weeks[0]["team"] if team_weeks else None
        weeks_observed = len({w for w, _t in entries})

        context[key] = {
            "teams": teams_chronological,
            "primary_team": primary_team,
            "team_weeks": team_weeks,
            "team_unknown": primary_team is None,
            "weeks_observed": weeks_observed,
        }
    return context


def _coverage_status(weeks_observed: int) -> str:
    if weeks_observed >= 15:
        return "full_season"
    if weeks_observed > 1:
        return "partial_season"
    if weeks_observed == 1:
        return "single_week"
    return "unknown"


def build_source_backed_payload() -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()

    players_index = _load_players_index()
    print(f"Loaded load_players() identity index: {len(players_index)} players")

    records: list[dict] = []
    seen_grain: set[tuple[str, int, str]] = set()

    for season in SEASONS:
        week_df = nfl.load_player_stats(seasons=[season], summary_level="week")
        week_columns = set(week_df.columns)
        wk_season_col = _resolve_column(week_columns, ["season"], "season")
        wk_week_col = _resolve_column(week_columns, ["week"], "week")
        wk_player_id_col = _resolve_column(week_columns, ["player_id", "gsis_id"], "player_id")
        wk_team_col = _resolve_column(week_columns, ["team", "recent_team"], "team")
        wk_season_type_col = _resolve_column(week_columns, ["season_type"], "season_type")

        week_records_raw = _records_from_dataframe(week_df)
        week_records: list[dict] = []
        for row in week_records_raw:
            if str(row.get(wk_season_type_col, "")).strip().upper() != SEASON_TYPE:
                continue
            player_id = row.get(wk_player_id_col)
            if player_id is None or str(player_id).strip() == "":
                continue
            row["_player_id"] = str(player_id).strip()
            week_records.append(row)

        team_context = _build_team_context(week_records, wk_season_col, wk_week_col, wk_team_col)

        reg_df = nfl.load_player_stats(seasons=[season], summary_level="reg")
        reg_columns = set(reg_df.columns)
        player_id_col = _resolve_column(reg_columns, ["player_id", "gsis_id"], "player_id")
        player_name_col = _resolve_column(reg_columns, ["player_display_name", "player_name"], "player_name")
        position_col = _resolve_column(reg_columns, ["position"], "position")
        games_col = _resolve_column(reg_columns, ["games"], "games")
        season_type_col = _resolve_column(reg_columns, ["season_type"], "season_type", required=False)

        completions_col = _resolve_column(reg_columns, ["completions"], "completions", required=False)
        attempts_col = _resolve_column(reg_columns, ["attempts"], "attempts", required=False)
        passing_yards_col = _resolve_column(reg_columns, ["passing_yards"], "passing_yards", required=False)
        passing_tds_col = _resolve_column(reg_columns, ["passing_tds"], "passing_tds", required=False)
        passing_int_col = _resolve_column(reg_columns, ["passing_interceptions"], "passing_interceptions", required=False)
        carries_col = _resolve_column(reg_columns, ["carries"], "carries", required=False)
        rushing_yards_col = _resolve_column(reg_columns, ["rushing_yards"], "rushing_yards", required=False)
        rushing_tds_col = _resolve_column(reg_columns, ["rushing_tds"], "rushing_tds", required=False)
        receptions_col = _resolve_column(reg_columns, ["receptions"], "receptions", required=False)
        targets_col = _resolve_column(reg_columns, ["targets"], "targets", required=False)
        receiving_yards_col = _resolve_column(reg_columns, ["receiving_yards"], "receiving_yards", required=False)
        receiving_tds_col = _resolve_column(reg_columns, ["receiving_tds"], "receiving_tds", required=False)
        receiving_air_yards_col = _resolve_column(reg_columns, ["receiving_air_yards"], "receiving_air_yards", required=False)
        target_share_col = _resolve_column(reg_columns, ["target_share"], "target_share", required=False)
        air_yards_share_col = _resolve_column(reg_columns, ["air_yards_share"], "air_yards_share", required=False)
        wopr_col = _resolve_column(reg_columns, ["wopr"], "wopr", required=False)
        racr_col = _resolve_column(reg_columns, ["racr"], "racr", required=False)
        fantasy_ppr_col = _resolve_column(reg_columns, ["fantasy_points_ppr"], "fantasy_points_ppr", required=False)

        def _v(row: dict, col: str | None):
            return None if col is None else _json_safe_value(row.get(col))

        for row in _records_from_dataframe(reg_df):
            player_id = row.get(player_id_col)
            if player_id is None or str(player_id).strip() == "":
                continue
            player_id_str = str(player_id).strip()

            position = str(_v(row, position_col) or "").strip().upper()
            if position not in INCLUDED_POSITIONS:
                continue

            season_type_value = str(row.get(season_type_col, SEASON_TYPE)).strip().upper() if season_type_col else SEASON_TYPE
            if season_type_value != SEASON_TYPE:
                continue

            grain_key = (player_id_str, season, SEASON_TYPE)
            if grain_key in seen_grain:
                raise ValueError(f"Duplicate player-season-season_type grain detected ({grain_key}). Build fails closed.")
            seen_grain.add(grain_key)

            ctx = team_context.get((season, player_id_str))
            missing_fields: list[str] = [
                "games_missed",
                "snap_share",
                "routes_run",
                "route_participation",
                "red_zone_targets",
                "red_zone_carries",
            ]

            if ctx is None:
                teams_list: list[str] = []
                primary_team = None
                primary_team_rule_value = None
                team_weeks_value: list[dict] = []
                team_unknown = True
                weeks_observed = 0
                missing_fields.append("team_context")
            else:
                teams_list = ctx["teams"]
                primary_team = ctx["primary_team"]
                primary_team_rule_value = PRIMARY_TEAM_RULE if len(teams_list) > 1 else None
                team_weeks_value = ctx["team_weeks"]
                team_unknown = ctx["team_unknown"]
                weeks_observed = ctx["weeks_observed"]

            games_played = _v(row, games_col)
            games_observed = weeks_observed

            identity_row = players_index.get(player_id_str)
            source_refs = [
                {
                    "source_name": "nflreadpy.load_player_stats(summary_level='reg')",
                    "source_url": None,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "confidence": "source_verified",
                    "notes": "Season REG production/usage rollup (nflverse). See artifact methodology.production_summary_source_note.",
                },
                {
                    "source_name": "nflreadpy.load_player_stats(summary_level='week')",
                    "source_url": None,
                    "observed_at": generated_at,
                    "source_updated_at": None,
                    "confidence": "source_verified",
                    "notes": "Week-level team-of-record (nflverse). See artifact methodology.team_context_source_note.",
                },
            ]

            if identity_row is not None:
                identity_confidence = "source_verified"
                birth_date_value = identity_row.get("birth_date")
                draft_year_value = _json_safe_value(identity_row.get("draft_year"))
                rookie_year_value = _json_safe_value(identity_row.get("rookie_season"))
                draft_round_value = _json_safe_value(identity_row.get("draft_round"))
                draft_pick_value = _json_safe_value(identity_row.get("draft_pick"))
                draft_team_value = _json_safe_value(identity_row.get("draft_team"))
                espn_id_value = _json_safe_value(identity_row.get("espn_id"))
                sleeper_id_value = None  # not exposed by nflreadpy.load_players in this environment
                source_refs.append(
                    {
                        "source_name": "nflreadpy.load_players()",
                        "source_url": None,
                        "observed_at": generated_at,
                        "source_updated_at": None,
                        "confidence": "source_verified",
                        "notes": "Player master identity/age/draft index (nflverse), keyed by gsis_id.",
                    }
                )
            else:
                identity_confidence = "provisional"
                birth_date_value = None
                draft_year_value = None
                rookie_year_value = None
                draft_round_value = None
                draft_pick_value = None
                draft_team_value = None
                espn_id_value = None
                sleeper_id_value = None
                missing_fields.extend(["birth_date", "season_age", "draft_year", "rookie_year", "career_year"])

            birth_date_json = _json_safe_value(birth_date_value)
            season_age_value = _season_age(birth_date_value, season)
            if birth_date_json is None and "birth_date" not in missing_fields:
                missing_fields.append("birth_date")
            if season_age_value is None and "season_age" not in missing_fields:
                missing_fields.append("season_age")
            if draft_year_value is None and "draft_year" not in missing_fields:
                missing_fields.append("draft_year")

            career_year_value = None
            if rookie_year_value is not None:
                try:
                    career_year_value = int(season) - int(rookie_year_value) + 1
                except (TypeError, ValueError):
                    career_year_value = None
            if rookie_year_value is None and "rookie_year" not in missing_fields:
                missing_fields.append("rookie_year")
            if career_year_value is None and "career_year" not in missing_fields:
                missing_fields.append("career_year")

            provider_ids = None
            if espn_id_value or sleeper_id_value:
                provider_ids = {
                    "espn_id": espn_id_value,
                    "sleeper_id": sleeper_id_value,
                }

            production_summary = {
                "season_ppr": _v(row, fantasy_ppr_col),
                "games_for_ppg": games_played,
                "season_ppg": (
                    _round_or_none(_v(row, fantasy_ppr_col) / games_played, 2)
                    if (_v(row, fantasy_ppr_col) is not None and games_played not in (None, 0))
                    else None
                ),
                "passing": {
                    "completions": _v(row, completions_col),
                    "attempts": _v(row, attempts_col),
                    "passing_yards": _v(row, passing_yards_col),
                    "passing_tds": _v(row, passing_tds_col),
                    "interceptions": _v(row, passing_int_col),
                },
                "rushing": {
                    "rushing_attempts": _v(row, carries_col),
                    "rushing_yards": _v(row, rushing_yards_col),
                    "rushing_tds": _v(row, rushing_tds_col),
                },
                "receiving": {
                    "receiving_yards": _v(row, receiving_yards_col),
                    "receiving_tds": _v(row, receiving_tds_col),
                },
                "source_note": "nflverse season rollup, passthrough (see methodology.production_summary_source_note).",
            }

            usage_summary = {
                "targets": _v(row, targets_col),
                "receptions": _v(row, receptions_col),
                "rushing_attempts": _v(row, carries_col),
                "receiving_air_yards": _v(row, receiving_air_yards_col),
                "target_share": _round_or_none(_v(row, target_share_col)),
                "air_yards_share": _round_or_none(_v(row, air_yards_share_col)),
                "wopr": _round_or_none(_v(row, wopr_col)),
                "racr": _round_or_none(_v(row, racr_col)),
                "snap_share": None,
                "routes_run": None,
                "route_participation": None,
                "red_zone_targets": None,
                "red_zone_carries": None,
                "source_note": "unavailable fields are not exposed by source (see methodology.usage_summary_source_note); null, never zero.",
            }

            record = {
                "player_id": player_id_str,
                "player_name": str(_v(row, player_name_col) or "").strip() or player_id_str,
                "position": position,
                "provider_ids": provider_ids,
                "identity_confidence": identity_confidence,
                "season": season,
                "season_type": SEASON_TYPE,
                "generated_at": generated_at,
                "observed_at": generated_at,
                "source_updated_at": None,
                "source_refs": source_refs,
                "teams": teams_list,
                "primary_team": primary_team,
                "primary_team_rule": primary_team_rule_value,
                "team_weeks": team_weeks_value,
                "team_unknown": team_unknown,
                "weeks_observed": weeks_observed,
                "games_observed": games_observed,
                "games_played": games_played,
                "games_missed": None,
                "coverage_status": _coverage_status(weeks_observed),
                "coverage_notes": (
                    f"{weeks_observed} of up to 18 REG week numbers observed"
                    + (f"; multi-team ({len(teams_list)}), see primary_team_rule" if len(teams_list) > 1 else "")
                    + " (see artifact methodology for thresholds and team-context source)."
                ),
                "missing_fields": sorted(set(missing_fields)),
                "production_summary": production_summary,
                "usage_summary": usage_summary,
                "birth_date": birth_date_json,
                "season_age": season_age_value,
                "draft_year": draft_year_value,
                "draft_round": draft_round_value,
                "draft_pick": draft_pick_value,
                "draft_team": draft_team_value,
                "rookie_year": rookie_year_value,
                "career_year": career_year_value,
            }

            records.append(record)

    if not records:
        raise ValueError("No valid source-backed player-season coverage records were produced. Build fails closed.")

    records.sort(key=lambda r: (r["season"], r["player_id"]))

    return {
        "artifact_id": "player_season_coverage_2022_2025.source_backed",
        "spec_version": "player_season_coverage_v0_candidate",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": generated_at,
        "seasons": SEASONS,
        "season_type_scope": [SEASON_TYPE],
        "included_positions": sorted(INCLUDED_POSITIONS),
        "row_grain": "player_id + season + season_type",
        "provenance": "nflreadpy.load_player_stats + nflreadpy.load_players",
        "source_path": "nflverse player stats (week + reg summary levels) and player master index via nflreadpy",
        "generated_from": [
            "scripts/build_player_season_coverage_2022_2025.py",
            "nflreadpy.load_player_stats(seasons, summary_level='reg')",
            "nflreadpy.load_player_stats(seasons, summary_level='week')",
            "nflreadpy.load_players()",
        ],
        "non_goals": [
            "not promoted/governed Forecast-ready data",
            "not a Forecast input today",
            "no active/inactive/IR/practice-squad availability status is asserted",
            "POST season_type out of scope for this build slice",
        ],
        "methodology": {
            "primary_team_rule": PRIMARY_TEAM_RULE,
            "team_context_source_note": TEAM_CONTEXT_SOURCE_NOTE,
            "coverage_status_rule": COVERAGE_STATUS_RULE,
            "age_reference_note": AGE_REFERENCE_NOTE,
            "production_summary_source_note": (
                "nflreadpy.load_player_stats(summary_level='reg').fantasy_points_ppr and yardage/TD fields are "
                "passed through directly (nflverse's own season rollup), not recomputed by this build."
            ),
            "usage_summary_source_note": (
                "snap_share/routes_run/route_participation/red_zone_* are not exposed by "
                "nflreadpy.load_player_stats and remain unavailable (null) on every row, never zero."
            ),
        },
        "records": records,
    }


def main() -> int:
    payload = build_source_backed_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(f"{json.dumps(payload, indent=2, allow_nan=False)}\n", encoding="utf-8")
    print(f"Wrote source-backed player season coverage candidate artifact: {OUTPUT_PATH.resolve()}")
    print(f"Record count: {len(payload['records'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
