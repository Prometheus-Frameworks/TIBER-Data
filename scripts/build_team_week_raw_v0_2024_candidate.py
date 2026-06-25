from __future__ import annotations

import importlib.metadata
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import nflreadpy as nfl
import polars as pl

SEASON = 2024

CANDIDATE_ARTIFACT_PATH = Path(
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json"
)
CANDIDATE_VALIDATION_REPORT_PATH = Path(
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json"
)
LINEAGE_MANIFEST_PATH = Path(
    "data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json"
)
TRANSFORM_CODE_PATH = "scripts/build_team_week_raw_v0_2024_candidate.py"
PREFLIGHT_DOC_PATH = "docs/data/team-week-raw-v0-2024-pr-c-preflight.md"

TEAM_CODE_CANONICAL_MAP = {"LA": "LAR"}
CANONICAL_TEAMS = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
        "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
        "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
        "TEN", "WAS",
    }
)
EXPECTED_WEEKS: tuple[int, ...] = tuple(range(1, 19))

OFFENSIVE_PLAY_TYPES = {"pass", "run", "qb_kneel", "qb_spike"}
PASS_RUN_PLAY_TYPES = {"pass", "run"}
NEUTRAL_SCRIPT_MARGIN = 8
NEUTRAL_Q4_MIN_SECONDS = 300
PASS_EXPLOSIVE_YARDS = 15
RUSH_EXPLOSIVE_YARDS = 10
RED_ZONE_YARDLINE_100 = 20

PRESSURE_DEFERRAL_REASON = (
    "no confirmed governed pressure-rate source as of PR C preflight "
    f"({PREFLIGHT_DOC_PATH} §8)"
)

REQUIRED_FIELDS_MINUS_PRESSURE: tuple[str, ...] = (
    "season", "week", "teamCode", "opponentCode", "offensivePlays", "neutralPlays",
    "secondsPerPlay", "passRate", "neutralPassRate", "rushRate", "epaPerPlay",
    "passEpaPerPlay", "rushEpaPerPlay", "successRate", "explosivePlayRate",
    "drives", "pointsPerDrive", "pointsFor", "pointsAgainst", "turnovers",
    "sacksAllowed", "redZoneTrips", "redZoneTdRate",
)

RATE_FIELDS: tuple[str, ...] = (
    "passRate", "neutralPassRate", "rushRate", "successRate",
    "explosivePlayRate", "redZoneTdRate",
)

REQUIRED_RETRIEVAL_KEYS = (
    "sourceName", "sourceType", "retrievalMethod", "retrievalTimestamp",
    "packageVersion", "sourceUrlOrDatasetId", "transformCodePath", "sourceRefs",
)


# ---------------------------------------------------------------------------
# Pure play-classification helpers
# ---------------------------------------------------------------------------

def canon_team(code: str | None) -> str | None:
    if code is None:
        return None
    return TEAM_CODE_CANONICAL_MAP.get(code, code)


def is_offensive_play(row: dict[str, Any]) -> bool:
    return row.get("play_type") in OFFENSIVE_PLAY_TYPES and not row.get("two_point_attempt")


def is_competitive_play(row: dict[str, Any]) -> bool:
    return row.get("play_type") in PASS_RUN_PLAY_TYPES and not row.get("two_point_attempt")


def is_neutral_script(row: dict[str, Any]) -> bool:
    score_differential = row.get("score_differential")
    if score_differential is None:
        return False
    if score_differential < -NEUTRAL_SCRIPT_MARGIN or score_differential > NEUTRAL_SCRIPT_MARGIN:
        return False
    if row.get("game_half") == "Overtime":
        return False
    qtr = row.get("qtr")
    if qtr == 4:
        remaining = row.get("quarter_seconds_remaining")
        if remaining is None or remaining <= NEUTRAL_Q4_MIN_SECONDS:
            return False
    elif qtr not in (1, 2, 3):
        return False
    return True


def is_explosive_pass(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("pass_attempt"))
        and bool(row.get("complete_pass"))
        and (row.get("yards_gained") or 0) >= PASS_EXPLOSIVE_YARDS
    )


def is_explosive_rush(row: dict[str, Any]) -> bool:
    return bool(row.get("rush_attempt")) and (row.get("yards_gained") or 0) >= RUSH_EXPLOSIVE_YARDS


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


# ---------------------------------------------------------------------------
# Per-team-game accumulator and aggregation
# ---------------------------------------------------------------------------

class TeamGameStats:
    def __init__(self) -> None:
        self.offensive_plays = 0
        self.competitive_plays = 0
        self.pass_plays = 0
        self.rush_plays = 0
        self.epa_values: list[float] = []
        self.pass_epa_values: list[float] = []
        self.rush_epa_values: list[float] = []
        self.success_count = 0
        self.explosive_count = 0
        self.neutral_plays = 0
        self.neutral_pass_plays = 0
        self.drive_ids: set[Any] = set()
        self.red_zone_trip_drive_ids: set[Any] = set()
        self.offensive_td_drive_ids: set[Any] = set()
        self.sacks_allowed = 0
        self.turnovers = 0
        self.pace_elapsed_seconds = 0.0
        self.pace_valid_intervals = 0
        self.pace_anomalous_intervals = 0
        self.dropback_null_rows = 0
        self.excluded_possession_plays = 0


def aggregate_game(plays: list[dict[str, Any]]) -> dict[str, TeamGameStats]:
    """Single-pass aggregation over one game's full play sequence (sorted by play_id).

    The sequence must be the full, unfiltered game (all teams, all play types) so
    that pace adjacency can see intervening administrative rows; pre-filtering to
    one team before computing adjacency would hide them.
    """
    stats_by_team: dict[str, TeamGameStats] = defaultdict(TeamGameStats)
    previous_row: dict[str, Any] | None = None
    previous_team: str | None = None

    for row in plays:
        team = canon_team(row.get("posteam"))
        if team:
            if is_offensive_play(row):
                stats = stats_by_team[team]
                stats.offensive_plays += 1
                drive_id = row.get("fixed_drive")
                if drive_id is not None:
                    stats.drive_ids.add(drive_id)
                    yardline = row.get("yardline_100")
                    if yardline is not None and yardline <= RED_ZONE_YARDLINE_100:
                        stats.red_zone_trip_drive_ids.add(drive_id)
                    if row.get("pass_touchdown") or row.get("rush_touchdown"):
                        stats.offensive_td_drive_ids.add(drive_id)

                if is_competitive_play(row):
                    stats.competitive_plays += 1
                    epa = row.get("epa")
                    dropback = row.get("qb_dropback")
                    if dropback is None:
                        stats.dropback_null_rows += 1
                    elif dropback:
                        stats.pass_plays += 1
                        if epa is not None:
                            stats.pass_epa_values.append(epa)
                    else:
                        stats.rush_plays += 1
                        if epa is not None:
                            stats.rush_epa_values.append(epa)
                    if epa is not None:
                        stats.epa_values.append(epa)
                    if row.get("success"):
                        stats.success_count += 1
                    if is_explosive_pass(row) or is_explosive_rush(row):
                        stats.explosive_count += 1
                    if is_neutral_script(row):
                        stats.neutral_plays += 1
                        if dropback:
                            stats.neutral_pass_plays += 1
                    if row.get("sack"):
                        stats.sacks_allowed += 1
                    if row.get("interception") or row.get("fumble_lost"):
                        stats.turnovers += 1
            else:
                stats_by_team[team].excluded_possession_plays += 1

        if (
            previous_row is not None
            and previous_team is not None
            and team == previous_team
            and is_competitive_play(previous_row)
            and is_competitive_play(row)
            and previous_row.get("fixed_drive") == row.get("fixed_drive")
            and previous_row.get("qtr") == row.get("qtr")
        ):
            previous_clock = previous_row.get("quarter_seconds_remaining")
            current_clock = row.get("quarter_seconds_remaining")
            if previous_clock is not None and current_clock is not None:
                elapsed = previous_clock - current_clock
                team_stats = stats_by_team[previous_team]
                if elapsed > 0:
                    team_stats.pace_elapsed_seconds += elapsed
                    team_stats.pace_valid_intervals += 1
                else:
                    team_stats.pace_anomalous_intervals += 1

        previous_row = row
        previous_team = team

    return stats_by_team


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _records_from_dataframe(df: Any) -> list[dict[str, Any]]:
    if hasattr(df, "to_dicts"):
        return df.to_dicts()
    return df.to_dict("records")


def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _nflverse_data_url(path: str) -> str:
    from nflreadpy.downloader import NflverseDownloader

    base_url = NflverseDownloader.BASE_URLS["nflverse-data"]
    if not path.endswith((".parquet", ".csv")):
        path = f"{path}.parquet"
    return urljoin(base_url, path)


def retrieve_pbp() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    retrieval_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    table = nfl.load_pbp([SEASON])
    reg = table.filter(pl.col("season_type") == "REG")
    source_info = {
        "sourceName": "nflverse play-by-play",
        "sourceType": "nflverse",
        "retrievalMethod": f"nflreadpy.load_pbp([{SEASON}])",
        "retrievalTimestamp": retrieval_timestamp,
        "packageVersion": _package_version("nflreadpy"),
        "sourceUrlOrDatasetId": _nflverse_data_url(f"pbp/play_by_play_{SEASON}"),
        "transformCodePath": TRANSFORM_CODE_PATH,
        "sourceRefs": [f"nflverse-data:pbp/play_by_play_{SEASON}"],
    }
    return _records_from_dataframe(reg), source_info


def retrieve_schedules() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    retrieval_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    table = nfl.load_schedules([SEASON])
    reg = table.filter(pl.col("game_type") == "REG")
    source_info = {
        "sourceName": "nflverse schedules",
        "sourceType": "nflverse",
        "retrievalMethod": f"nflreadpy.load_schedules([{SEASON}])",
        "retrievalTimestamp": retrieval_timestamp,
        "packageVersion": _package_version("nflreadpy"),
        "sourceUrlOrDatasetId": _nflverse_data_url("schedules/games"),
        "transformCodePath": TRANSFORM_CODE_PATH,
        "sourceRefs": ["nflverse-data:schedules/games"],
    }
    return _records_from_dataframe(reg), source_info


def _to_contract_input_source(source_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source_info["sourceUrlOrDatasetId"],
        "sourceType": "nflverse",
        "sourceSnapshotAt": source_info["retrievalTimestamp"],
        "notes": (
            f"{source_info['sourceName']} via {source_info['retrievalMethod']} "
            f"(nflreadpy {source_info['packageVersion']})."
        ),
    }


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------

def build_team_week_row(
    *,
    season: int,
    week: int,
    team: str,
    opponent: str,
    game_id: str,
    points_for: int,
    points_against: int,
    stats: TeamGameStats,
) -> tuple[dict[str, Any], dict[str, Any]]:
    drives = len(stats.drive_ids)
    red_zone_trips = len(stats.red_zone_trip_drive_ids)
    red_zone_tds = len(stats.red_zone_trip_drive_ids & stats.offensive_td_drive_ids)

    dropback_split_blocked = stats.dropback_null_rows > 0
    pass_rate = safe_ratio(stats.pass_plays, stats.competitive_plays)
    rush_rate = safe_ratio(stats.rush_plays, stats.competitive_plays)
    pass_epa_per_play = (
        safe_ratio(sum(stats.pass_epa_values), len(stats.pass_epa_values))
        if stats.pass_epa_values
        else None
    )
    rush_epa_per_play = (
        safe_ratio(sum(stats.rush_epa_values), len(stats.rush_epa_values))
        if stats.rush_epa_values
        else None
    )
    if dropback_split_blocked:
        pass_rate = None
        rush_rate = None
        pass_epa_per_play = None
        rush_epa_per_play = None

    pace_blocked = False
    seconds_per_play = None
    if stats.competitive_plays > 0:
        if stats.pace_valid_intervals > 0:
            seconds_per_play = stats.pace_elapsed_seconds / stats.competitive_plays
        else:
            pace_blocked = True

    row = {
        "season": season,
        "week": week,
        "teamCode": team,
        "opponentCode": opponent,
        "gameId": game_id,
        "isByeWeek": False,
        "pointsFor": points_for,
        "pointsAgainst": points_against,
        "offensivePlays": stats.offensive_plays,
        "neutralPlays": stats.neutral_plays,
        "secondsPerPlay": _round(seconds_per_play),
        "passRate": _round(pass_rate),
        "neutralPassRate": _round(safe_ratio(stats.neutral_pass_plays, stats.neutral_plays)),
        "rushRate": _round(rush_rate),
        "epaPerPlay": _round(
            safe_ratio(sum(stats.epa_values), len(stats.epa_values)) if stats.epa_values else None
        ),
        "passEpaPerPlay": _round(pass_epa_per_play),
        "rushEpaPerPlay": _round(rush_epa_per_play),
        "successRate": _round(safe_ratio(stats.success_count, stats.competitive_plays)),
        "explosivePlayRate": _round(safe_ratio(stats.explosive_count, stats.competitive_plays)),
        "drives": drives,
        "pointsPerDrive": _round(safe_ratio(points_for, drives)),
        "redZoneTrips": red_zone_trips,
        "redZoneTdRate": _round(safe_ratio(red_zone_tds, red_zone_trips)),
        "sacksAllowed": stats.sacks_allowed,
        "pressureRateAllowed": None,
        "turnovers": stats.turnovers,
        "fantasyPointsForQB": None,
        "fantasyPointsForRB": None,
        "fantasyPointsForWR": None,
        "fantasyPointsForTE": None,
        "fantasyPointsAllowedQB": None,
        "fantasyPointsAllowedRB": None,
        "fantasyPointsAllowedWR": None,
        "fantasyPointsAllowedTE": None,
    }

    diagnostics = {
        "season": season,
        "week": week,
        "teamCode": team,
        "competitivePlays": stats.competitive_plays,
        "neutralPlaysDenominatorZero": stats.neutral_plays == 0,
        "redZoneTripsDenominatorZero": red_zone_trips == 0,
        "paceBlocked": pace_blocked,
        "paceAnomalousIntervals": stats.pace_anomalous_intervals,
        "dropbackSplitBlocked": dropback_split_blocked,
        "dropbackNullRows": stats.dropback_null_rows,
        "excludedPossessionPlays": stats.excluded_possession_plays,
    }
    return row, diagnostics


def build_rows(
    pbp_rows: list[dict[str, Any]], schedule_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plays_by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for play in pbp_rows:
        plays_by_game[play["game_id"]].append(play)
    for plays in plays_by_game.values():
        plays.sort(key=lambda play: play["play_id"])

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    schedule_rows_sorted = sorted(schedule_rows, key=lambda game: (game["week"], game["game_id"]))
    for game in schedule_rows_sorted:
        game_id = str(game["game_id"])
        plays = plays_by_game.get(game_id, [])
        if not plays:
            raise ValueError(
                f"No play-by-play rows found for scheduled REG game {game_id}. Build fails closed."
            )
        stats_by_team = aggregate_game(plays)
        season = int(game["season"])
        week = int(game["week"])
        home = canon_team(game["home_team"])
        away = canon_team(game["away_team"])
        for team, opponent, points_for, points_against in (
            (home, away, game["home_score"], game["away_score"]),
            (away, home, game["away_score"], game["home_score"]),
        ):
            stats = stats_by_team.get(team, TeamGameStats())
            row, diag = build_team_week_row(
                season=season,
                week=week,
                team=team,
                opponent=opponent,
                game_id=game_id,
                points_for=int(points_for),
                points_against=int(points_against),
                stats=stats,
            )
            pairs.append((row, diag))

    pairs.sort(key=lambda pair: (pair[0]["season"], pair[0]["week"], pair[0]["teamCode"]))
    rows = [pair[0] for pair in pairs]
    diagnostics = [pair[1] for pair in pairs]
    return rows, diagnostics


# ---------------------------------------------------------------------------
# Coverage / metadata / envelope
# ---------------------------------------------------------------------------

def build_coverage(
    season: int, rows: list[dict[str, Any]], scheduled_game_count: int
) -> dict[str, Any]:
    present_teams = sorted({row["teamCode"] for row in rows})
    missing_teams = sorted(CANONICAL_TEAMS - set(present_teams))
    unexpected_teams = sorted(set(present_teams) - CANONICAL_TEAMS)
    weeks_present = sorted({row["week"] for row in rows})
    return {
        "season": season,
        "expectedTeams": sorted(CANONICAL_TEAMS),
        "presentTeams": present_teams,
        "missingTeams": missing_teams,
        "unexpectedTeams": unexpected_teams,
        "weeks": weeks_present,
        "expectedWeeks": list(EXPECTED_WEEKS),
        "isFullLeague": not missing_teams and not unexpected_teams,
        "isFullRegularSeasonCalendar": weeks_present == list(EXPECTED_WEEKS),
        "expectedTeamGameRows": scheduled_game_count * 2,
        "actualTeamGameRows": len(rows),
        "byeWeeksHandled": True,
    }


def build_metadata(
    *,
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    scheduled_game_count: int,
    input_sources_meta: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage = build_coverage(SEASON, rows, scheduled_game_count)

    pace_blocked_rows = [d for d in diagnostics if d["paceBlocked"]]
    dropback_blocked_rows = [d for d in diagnostics if d["dropbackSplitBlocked"]]
    total_anomalous_intervals = sum(d["paceAnomalousIntervals"] for d in diagnostics)
    total_excluded_possession_plays = sum(d["excludedPossessionPlays"] for d in diagnostics)

    provenance_notes = [
        "Built from real 2024 nflverse play-by-play and schedules via nflreadpy; "
        "not a fixture or sample.",
        "provenanceStatus is partial_real_data: pressureRateAllowed is deferred-null for "
        f"every row per {PREFLIGHT_DOC_PATH} §8; this artifact must not be treated as "
        "governed_real_data.",
        "Team code 'LA' from the raw nflverse source is canonicalized to 'LAR' for every "
        "team-code-bearing field.",
        "Two-point conversion attempts are excluded from offensive-play, drive, and rate "
        f"accounting per {PREFLIGHT_DOC_PATH} §2; they remain included in full-game "
        "pointsFor/pointsAgainst.",
        "secondsPerPlay denominator is the full competitive offensive-play count (the same "
        f"set used for epaPerPlay), not the count of clean pace intervals, per "
        f"{PREFLIGHT_DOC_PATH} §6.",
        f"{total_anomalous_intervals} consecutive-snap pace interval(s) were excluded from "
        "the secondsPerPlay elapsed-time numerator because the computed elapsed time was "
        f"not positive; {len(pace_blocked_rows)} team-week row(s) were null-blocked for "
        "secondsPerPlay because zero clean intervals were found for that row.",
        f"{total_excluded_possession_plays} possession-team play(s) were excluded from "
        "offensive-snap accounting across the artifact (special-teams plays, two-point "
        "attempts, no-plays/aborted plays).",
        f"{len(dropback_blocked_rows)} team-week row(s) had "
        "passRate/rushRate/passEpaPerPlay/rushEpaPerPlay null-blocked because the source's "
        "qb_dropback indicator could not classify one or more competitive plays as pass or "
        "rush for that row.",
        "No governance marker is set by this build. governanceStatus is 'ungoverned' and "
        "governanceSource is 'not_set'; promotion to governed_real_data requires a "
        "separate, explicitly authorized human promotion review (PR D), not build success "
        "or validation passing.",
    ]

    return {
        "provenanceStatus": "partial_real_data",
        "provenanceNotes": provenance_notes,
        "inputSources": input_sources_meta,
        "coverage": coverage,
        "governance": {
            "governanceStatus": "ungoverned",
            "governanceSource": "not_set",
            "notes": (
                "No human promotion review has been performed. Build success and "
                "validation passing do not constitute governance."
            ),
        },
        "deferredFields": ["pressureRateAllowed"],
        "deferredFieldReasons": {"pressureRateAllowed": PRESSURE_DEFERRAL_REASON},
        "blockedFieldRows": {
            "secondsPerPlay": [
                {"season": d["season"], "week": d["week"], "teamCode": d["teamCode"]}
                for d in pace_blocked_rows
            ],
            "dropbackSplit(passRate/rushRate/passEpaPerPlay/rushEpaPerPlay)": [
                {"season": d["season"], "week": d["week"], "teamCode": d["teamCode"]}
                for d in dropback_blocked_rows
            ],
        },
        "buildDiagnostics": {
            "paceAnomalousIntervalsTotal": total_anomalous_intervals,
            "excludedPossessionPlaysTotal": total_excluded_possession_plays,
            "secondsPerPlayBlockedRowCount": len(pace_blocked_rows),
            "dropbackSplitBlockedRowCount": len(dropback_blocked_rows),
        },
        "validationReportPath": str(CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(LINEAGE_MANIFEST_PATH),
    }


def build_artifact(
    rows: list[dict[str, Any]], metadata: dict[str, Any], source_refs: list[str]
) -> dict[str, Any]:
    return {
        "artifact": "team_week_raw_v0",
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "season": SEASON,
        "sourceArtifacts": source_refs,
        "metadata": metadata,
        "rows": rows,
    }


def build_lineage_manifest(source_infos: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact": "team_week_raw_v0_2024_real_source_candidate",
        "season": SEASON,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sources": source_infos,
        "validationReportPath": str(CANDIDATE_VALIDATION_REPORT_PATH),
        "lineageManifestPath": str(LINEAGE_MANIFEST_PATH),
        "governanceStatus": "ungoverned",
        "governanceSource": "not_set",
        "notes": [
            "This manifest documents source retrieval for a partial_real_data candidate "
            "artifact only.",
            "No governed_real_data claim is made or implied by this manifest.",
            "Promotion to governed status requires a separate, explicitly authorized "
            "human review (PR D).",
        ],
    }


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

def _check(name: str, passed: bool, details: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def build_validation_report(
    artifact: dict[str, Any],
    diagnostics: list[dict[str, Any]],
    lineage_manifest: dict[str, Any],
) -> dict[str, Any]:
    rows = artifact["rows"]
    coverage = artifact["metadata"]["coverage"]
    checks: list[dict[str, Any]] = []

    checks.append(
        _check(
            "all_32_teams_present",
            not coverage["missingTeams"] and not coverage["unexpectedTeams"],
            {
                "missingTeams": coverage["missingTeams"],
                "unexpectedTeams": coverage["unexpectedTeams"],
            },
        )
    )

    rows_per_team: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        rows_per_team[row["teamCode"]].append(row["week"])
    out_of_window = {
        team: weeks_for_team
        for team, weeks in rows_per_team.items()
        if (weeks_for_team := [week for week in weeks if week not in EXPECTED_WEEKS])
    }
    too_many_rows = {team: len(weeks) for team, weeks in rows_per_team.items() if len(weeks) > 18}
    checks.append(
        _check(
            "expected_weeks_present_per_team",
            not out_of_window and not too_many_rows,
            {"outOfWindowWeeksByTeam": out_of_window, "teamsWithMoreThan18Rows": too_many_rows},
        )
    )

    expected_team_game_rows = coverage["expectedTeamGameRows"]
    actual_team_game_rows = coverage["actualTeamGameRows"]
    row_count = len(rows)
    checks.append(
        _check(
            "expected_team_game_row_count",
            expected_team_game_rows == actual_team_game_rows == row_count,
            {
                "expectedTeamGameRows": expected_team_game_rows,
                "actualTeamGameRows": actual_team_game_rows,
                "rowCount": row_count,
            },
        )
    )

    keys = [(row["season"], row["week"], row["teamCode"]) for row in rows]
    duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
    checks.append(
        _check(
            "no_duplicate_team_week_rows", not duplicate_keys, {"duplicateKeys": duplicate_keys}
        )
    )

    invalid_codes = sorted(
        {row["teamCode"] for row in rows if row["teamCode"] not in CANONICAL_TEAMS}
        | {row["opponentCode"] for row in rows if row["opponentCode"] not in CANONICAL_TEAMS}
    )
    checks.append(
        _check(
            "valid_team_and_opponent_codes", not invalid_codes, {"invalidCodes": invalid_codes}
        )
    )

    by_key = {(row["season"], row["week"], row["teamCode"]): row for row in rows}
    bad_reciprocal = []
    for row in rows:
        opponent_row = by_key.get((row["season"], row["week"], row["opponentCode"]))
        if opponent_row is None or opponent_row["opponentCode"] != row["teamCode"]:
            bad_reciprocal.append(
                {"season": row["season"], "week": row["week"], "teamCode": row["teamCode"]}
            )
    checks.append(
        _check("reciprocal_opponent_consistency", not bad_reciprocal, {"badRows": bad_reciprocal})
    )

    out_of_bounds = []
    for row in rows:
        for field in RATE_FIELDS:
            value = row[field]
            if value is not None and not (0.0 <= value <= 1.0):
                out_of_bounds.append(
                    {"season": row["season"], "week": row["week"], "teamCode": row["teamCode"],
                     "field": field, "value": value}
                )
    checks.append(
        _check(
            "rate_fields_bounded_0_1_or_null",
            not out_of_bounds,
            {"outOfBoundsRows": out_of_bounds},
        )
    )

    diagnostics_by_key = {(d["season"], d["week"], d["teamCode"]): d for d in diagnostics}
    unexplained_nulls = []
    non_finite = []
    for row in rows:
        key = (row["season"], row["week"], row["teamCode"])
        diag = diagnostics_by_key.get(key, {})
        key_dict = {"season": key[0], "week": key[1], "teamCode": key[2]}
        for field in REQUIRED_FIELDS_MINUS_PRESSURE:
            value = row[field]
            if value is None:
                allowed = (
                    (field == "neutralPassRate" and diag.get("neutralPlaysDenominatorZero"))
                    or (field == "redZoneTdRate" and diag.get("redZoneTripsDenominatorZero"))
                    or (field == "secondsPerPlay" and diag.get("paceBlocked"))
                    or (
                        field in ("passRate", "rushRate", "passEpaPerPlay", "rushEpaPerPlay")
                        and diag.get("dropbackSplitBlocked")
                    )
                    or (
                        field in ("epaPerPlay", "passEpaPerPlay", "rushEpaPerPlay")
                        and diag.get("competitivePlays") == 0
                    )
                )
                if not allowed:
                    unexplained_nulls.append({**key_dict, "field": field})
                continue
            is_non_finite = value != value or value in (float("inf"), float("-inf"))
            if isinstance(value, float) and is_non_finite:
                non_finite.append({**key_dict, "field": field, "value": value})
    checks.append(
        _check(
            "required_finite_numeric_fields",
            not unexplained_nulls and not non_finite,
            {"unexplainedNulls": unexplained_nulls, "nonFiniteValues": non_finite},
        )
    )

    pressure_violations = [
        {"season": row["season"], "week": row["week"], "teamCode": row["teamCode"]}
        for row in rows
        if row["pressureRateAllowed"] is not None
    ]
    deferred_fields = artifact["metadata"].get("deferredFields", [])
    checks.append(
        _check(
            "pressure_rate_allowed_null_and_deferred",
            not pressure_violations and "pressureRateAllowed" in deferred_fields,
            {"nonNullRows": pressure_violations, "deferredFields": deferred_fields},
        )
    )

    pace_blocked = [d for d in diagnostics if d["paceBlocked"]]
    pace_blocked_recorded = artifact["metadata"]["blockedFieldRows"].get("secondsPerPlay", [])
    checks.append(
        _check(
            "seconds_per_play_block_metadata_if_applicable",
            len(pace_blocked) == len(pace_blocked_recorded),
            {
                "blockedRowCount": len(pace_blocked),
                "recordedInMetadataCount": len(pace_blocked_recorded),
            },
        )
    )

    dropback_blocked = [d for d in diagnostics if d["dropbackSplitBlocked"]]
    dropback_blocked_recorded = artifact["metadata"]["blockedFieldRows"].get(
        "dropbackSplit(passRate/rushRate/passEpaPerPlay/rushEpaPerPlay)", []
    )
    checks.append(
        _check(
            "epa_split_block_metadata_if_applicable",
            len(dropback_blocked) == len(dropback_blocked_recorded),
            {
                "blockedRowCount": len(dropback_blocked),
                "recordedInMetadataCount": len(dropback_blocked_recorded),
            },
        )
    )

    source_refs_present = bool(artifact["sourceArtifacts"])
    checks.append(
        _check(
            "source_refs_present",
            source_refs_present,
            {"sourceArtifacts": artifact["sourceArtifacts"]},
        )
    )

    incomplete_sources = []
    lineage_sources = lineage_manifest.get("sources", [])
    for source in lineage_sources:
        missing_keys = sorted(key for key in REQUIRED_RETRIEVAL_KEYS if not source.get(key))
        if missing_keys:
            incomplete_sources.append(
                {"sourceName": source.get("sourceName"), "missingKeys": missing_keys}
            )
    checks.append(
        _check(
            "retrieval_metadata_complete",
            bool(lineage_sources) and not incomplete_sources,
            {"incompleteSources": incomplete_sources, "sourceCount": len(lineage_sources)},
        )
    )

    provenance_status = artifact["metadata"]["provenanceStatus"]
    governance_status = artifact["metadata"].get("governance", {}).get("governanceStatus")
    checks.append(
        _check(
            "non_governed_status",
            provenance_status != "governed_real_data" and governance_status != "governed",
            {"provenanceStatus": provenance_status, "governanceStatus": governance_status},
        )
    )

    all_passed = all(check["passed"] for check in checks)
    return {
        "report": "team_week_raw_v0_2024_real_source_candidate_validation",
        "season": SEASON,
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "artifactPath": str(CANDIDATE_ARTIFACT_PATH),
        "rowCount": len(rows),
        "teamCount": len(coverage["presentTeams"]),
        "allPassed": all_passed,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    pbp_rows, pbp_source_info = retrieve_pbp()
    schedule_rows, schedules_source_info = retrieve_schedules()

    rows, diagnostics = build_rows(pbp_rows, schedule_rows)

    input_sources_meta = [
        _to_contract_input_source(pbp_source_info),
        _to_contract_input_source(schedules_source_info),
    ]
    metadata = build_metadata(
        rows=rows,
        diagnostics=diagnostics,
        scheduled_game_count=len(schedule_rows),
        input_sources_meta=input_sources_meta,
    )
    source_refs = sorted(
        {ref for info in (pbp_source_info, schedules_source_info) for ref in info["sourceRefs"]}
    )
    artifact = build_artifact(rows, metadata, source_refs)
    lineage_manifest = build_lineage_manifest([pbp_source_info, schedules_source_info])
    validation_report = build_validation_report(artifact, diagnostics, lineage_manifest)

    print(f"Built {len(rows)} team-week rows across {len(schedule_rows)} scheduled REG games.")
    for check in validation_report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"  [{status}] {check['name']}")

    if not validation_report["allPassed"]:
        print(
            "ERROR: validation failed; refusing to emit candidate artifact, validation report, "
            "or lineage manifest.",
            file=sys.stderr,
        )
        return 1

    CANDIDATE_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LINEAGE_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_ARTIFACT_PATH.write_text(f"{json.dumps(artifact, indent=2)}\n", encoding="utf-8")
    CANDIDATE_VALIDATION_REPORT_PATH.write_text(
        f"{json.dumps(validation_report, indent=2)}\n", encoding="utf-8"
    )
    LINEAGE_MANIFEST_PATH.write_text(
        f"{json.dumps(lineage_manifest, indent=2)}\n", encoding="utf-8"
    )

    print(f"Wrote candidate artifact: {CANDIDATE_ARTIFACT_PATH.resolve()}")
    print(f"Wrote validation report: {CANDIDATE_VALIDATION_REPORT_PATH.resolve()}")
    print(f"Wrote lineage manifest: {LINEAGE_MANIFEST_PATH.resolve()}")
    print(
        f"provenanceStatus: {metadata['provenanceStatus']}  "
        f"governanceStatus: {metadata['governance']['governanceStatus']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with a clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
