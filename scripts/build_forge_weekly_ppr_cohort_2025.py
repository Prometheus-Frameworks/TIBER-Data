from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

SEASON = 2025
REGULAR_SEASON_WEEKS = tuple(range(1, 19))
MIN_PLAYERS = 20
MAX_PLAYERS = 50
SCORING_FORMAT = "PPR"
SCHEMA_VERSION = "cohort.v1"
DEFAULT_AS_OF = "2026-04-27T00:00:00Z"
BUILD_ID = "forge-player-weekly-ppr-2025:cohort:v1:source-backed"

SOURCE_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json")
ROSTER_SOURCE_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
OUTPUT_PATH = Path("data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json")

INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}

# Prioritized by user request. IDs are nflverse player IDs; names are verified from
# the existing roster/player-stat source files during build, not fabricated here.
REQUESTED_PLAYERS: tuple[tuple[str, str], ...] = (
    ("00-0036900", "Ja'Marr Chase"),
    ("00-0034857", "Josh Allen"),
    ("00-0038542", "Bijan Robinson"),
    ("00-0039338", "Brock Bowers"),
    ("00-0036963", "Amon-Ra St. Brown"),
    ("00-0033280", "Christian McCaffrey"),
    ("00-0033040", "Tyreek Hill"),
    ("00-0037240", "Jameson Williams"),
    ("00-0031408", "Mike Evans"),
    ("00-0034753", "Mark Andrews"),
)

SCORING_RULES = {
    "passingYards": "yards / 25 when applicable",
    "passingTds": "td * 4 when applicable",
    "interceptions": "interception * -2 when applicable",
    "rushingYards": "yards / 10",
    "rushingTds": "td * 6",
    "receivingYards": "yards / 10",
    "receivingTds": "td * 6",
    "receptions": "reception * 1",
    "fumblesLost": "fumble lost * -2 when available",
}

FORMULA = (
    "receptions + (receivingYards / 10) + (receivingTDs * 6) "
    "+ (rushingYards / 10) + (rushingTDs * 6) "
    "+ applicable passing scoring - (interceptions * 2) - (fumblesLost * 2)"
)


def _json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or not math.isfinite(value)):
        return None
    return value


def _number_or_zero(value: Any) -> float:
    value = _json_safe_value(value)
    if value is None:
        return 0.0
    return float(value)


def _optional_int(value: Any) -> int | None:
    value = _json_safe_value(value)
    if value is None:
        return None
    return int(value)


def _optional_number(value: Any) -> float | int | None:
    value = _json_safe_value(value)
    if value is None:
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def _round(value: float, digits: int = 2) -> float:
    return round(value + 0, digits)


def calculate_ppr_points(row: dict[str, Any]) -> float:
    points = (
        _number_or_zero(row.get("passing_yards")) / 25
        + _number_or_zero(row.get("passing_tds")) * 4
        + _number_or_zero(row.get("interceptions")) * -2
        + _number_or_zero(row.get("rushing_yards")) / 10
        + _number_or_zero(row.get("rushing_tds")) * 6
        + _number_or_zero(row.get("receiving_yards")) / 10
        + _number_or_zero(row.get("receiving_tds")) * 6
        + _number_or_zero(row.get("receptions"))
        + _number_or_zero(row.get("fumbles_lost")) * -2
    )
    return _round(points, 2)


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(
            "Missing source-backed 2025 player-week PPR input. "
            f"Expected {path}. This cohort must fail closed rather than use fixtures, "
            "samples, offline values, or invented rows."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("records"), list):
        raise ValueError(f"Source-backed payload at {path} must contain a records array.")
    return payload


def _load_roster_name_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("records"), list):
        raise ValueError(f"Roster source-backed payload at {path} must contain a records array.")
    names_by_player: dict[str, set[str]] = defaultdict(set)
    for row in payload["records"]:
        player_id = str(row.get("player_id", "")).strip()
        player_name = str(row.get("player_name", "")).strip()
        if player_id and player_name:
            names_by_player[player_id].add(player_name)
    return {player_id: sorted(names)[0] for player_id, names in names_by_player.items()}


def _source_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str, str | None]] = set()
    for raw in payload["records"]:
        row = dict(raw)
        season = int(row.get("season"))
        week = int(row.get("week"))
        player_id = str(row.get("player_id", "")).strip()
        position = str(row.get("position", "")).strip().upper()
        if season != SEASON or week not in REGULAR_SEASON_WEEKS:
            continue
        if not player_id or position not in INCLUDED_POSITIONS:
            continue
        key = (season, week, player_id, _json_safe_value(row.get("game_id")))
        if key in seen:
            raise ValueError(f"Duplicate source-backed player-week row detected: {key}")
        seen.add(key)
        rows.append(row)
    if not rows:
        raise ValueError("No source-backed regular-season 2025 QB/RB/WR/TE rows are available.")
    return rows


def _source_metadata(source_payload: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "provider": "nflverse via nflreadpy",
        "file": str(source_path),
        "path": source_payload.get("source_path"),
        "provenance": source_payload.get("provenance"),
        "generatedFrom": source_payload.get("generated_from", []),
    }


def _row_source_metadata(source_payload: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "sourceProvider": "nflverse via nflreadpy",
        "sourceFile": str(source_path),
        "sourcePath": source_payload.get("source_path"),
        "sourceProvenance": source_payload.get("provenance"),
        "asOf": DEFAULT_AS_OF,
        "sourceUpdatedAt": DEFAULT_AS_OF,
        "buildId": BUILD_ID,
    }


def _stat_block(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "passingYards": _optional_number(row.get("passing_yards")),
        "passingTDs": _optional_int(row.get("passing_tds")),
        "interceptions": _optional_int(row.get("interceptions")),
        "rushingAttempts": _optional_int(row.get("rushing_attempts")),
        "rushingYards": _optional_number(row.get("rushing_yards")),
        "rushingTDs": _optional_int(row.get("rushing_tds")),
        "targets": _optional_int(row.get("targets")),
        "receptions": _optional_int(row.get("receptions")),
        "receivingYards": _optional_number(row.get("receiving_yards")),
        "receivingTDs": _optional_int(row.get("receiving_tds")),
        "fumblesLost": _optional_int(row.get("fumbles_lost")) if "fumbles_lost" in row else None,
    }


def _total_or_null(rows: list[dict[str, Any]], field: str) -> float | int | None:
    values = [row.get(field) for row in rows if _json_safe_value(row.get(field)) is not None]
    if not values:
        return None
    total = sum(float(value) for value in values)
    return int(total) if total.is_integer() else _round(total, 2)


def _season_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ppr_total = _round(sum(calculate_ppr_points(row) for row in rows), 2)
    return {
        "games": len(rows),
        "weeks": [int(row["week"]) for row in rows],
        "pprPoints": ppr_total,
        "passingYards": _total_or_null(rows, "passing_yards"),
        "passingTDs": _total_or_null(rows, "passing_tds"),
        "interceptions": _total_or_null(rows, "interceptions"),
        "rushingAttempts": _total_or_null(rows, "rushing_attempts"),
        "rushingYards": _total_or_null(rows, "rushing_yards"),
        "rushingTDs": _total_or_null(rows, "rushing_tds"),
        "targets": _total_or_null(rows, "targets"),
        "receptions": _total_or_null(rows, "receptions"),
        "receivingYards": _total_or_null(rows, "receiving_yards"),
        "receivingTDs": _total_or_null(rows, "receiving_tds"),
        "fumblesLost": _total_or_null(rows, "fumbles_lost"),
    }


def _latest_team(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: (int(row["week"]), str(row.get("team", ""))))
    return str(ordered[-1].get("team", "")).strip()


def _resolve_requested_players(rows_by_player: dict[str, list[dict[str, Any]]]) -> list[str]:
    resolved: list[str] = []
    for player_id, player_name in REQUESTED_PLAYERS:
        rows = rows_by_player.get(player_id)
        if not rows:
            raise ValueError(
                f"Requested player cannot be resolved from source-backed {SEASON} rows: "
                f"{player_name} ({player_id})."
            )
        resolved.append(player_id)
    return resolved


def _select_player_ids(rows_by_player: dict[str, list[dict[str, Any]]]) -> list[str]:
    selected = _resolve_requested_players(rows_by_player)

    summaries: list[dict[str, Any]] = []
    for player_id, rows in rows_by_player.items():
        total = _round(sum(calculate_ppr_points(row) for row in rows), 2)
        first = sorted(rows, key=lambda row: int(row["week"]))[0]
        summaries.append(
            {
                "playerId": player_id,
                "pprPoints": total,
                "position": str(first.get("position", "")).strip().upper(),
            }
        )

    for summary in sorted(summaries, key=lambda item: (-item["pprPoints"], item["playerId"])):
        if len(selected) >= MAX_PLAYERS:
            break
        if summary["playerId"] not in selected:
            selected.append(summary["playerId"])

    if len(selected) < MIN_PLAYERS:
        raise ValueError(
            f"Only {len(selected)} source-backed fantasy-relevant players are available; "
            f"need at least {MIN_PLAYERS}. Build fails closed."
        )
    return selected


def _weekly_row(
    row: dict[str, Any],
    player_name: str,
    source_payload: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    stats = _stat_block(row)
    return {
        "playerId": str(row.get("player_id", "")).strip(),
        "playerName": player_name,
        "team": str(row.get("team", "")).strip(),
        "position": str(row.get("position", "")).strip().upper(),
        "season": int(row["season"]),
        "week": int(row["week"]),
        "opponent": _json_safe_value(row.get("opponent")),
        "gameId": _json_safe_value(row.get("game_id")),
        "pprPoints": calculate_ppr_points(row),
        **stats,
        **_row_source_metadata(source_payload, source_path),
    }


def build_cohort(
    source_path: Path = SOURCE_PATH,
    roster_source_path: Path = ROSTER_SOURCE_PATH,
) -> dict[str, Any]:
    source_payload = _load_payload(source_path)
    name_map = _load_roster_name_map(roster_source_path)
    rows = _source_rows(source_payload)

    rows_by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_player[str(row["player_id"]).strip()].append(row)

    selected_ids = _select_player_ids(rows_by_player)
    players: list[dict[str, Any]] = []
    for player_id in selected_ids:
        player_rows = sorted(rows_by_player[player_id], key=lambda row: int(row["week"]))
        first = player_rows[0]
        player_name = name_map.get(player_id, str(first.get("player_name", player_id)).strip())
        weekly_rows = [
            _weekly_row(row, player_name, source_payload, source_path) for row in player_rows
        ]
        totals = _season_totals(player_rows)
        weekly_sum = _round(sum(row["pprPoints"] for row in weekly_rows), 2)
        if totals["pprPoints"] != weekly_sum:
            raise ValueError(
                f"Season PPR total for {player_name} ({player_id}) does not equal "
                f"weekly sum: {totals['pprPoints']} != {weekly_sum}."
            )
        players.append(
            {
                "playerId": player_id,
                "playerName": player_name,
                "team": _latest_team(player_rows),
                "position": str(first.get("position", "")).strip().upper(),
                "season": SEASON,
                "source": _source_metadata(source_payload, source_path),
                "seasonTotal": totals,
                "weeklyRows": weekly_rows,
            }
        )

    return {
        "artifactId": "forge_player_weekly_ppr_2025.cohort.v1",
        "schemaVersion": SCHEMA_VERSION,
        "artifactType": "source_backed_weekly_ppr_player_cohort",
        "season": SEASON,
        "regularSeasonWeeks": list(REGULAR_SEASON_WEEKS),
        "playerCount": len(players),
        "scoringFormat": SCORING_FORMAT,
        "scoringFormula": {
            "format": SCORING_FORMAT,
            "formula": FORMULA,
            "rules": SCORING_RULES,
            "rounding": "round half even via Python round(..., 2)",
        },
        "source": _source_metadata(source_payload, source_path),
        "asOf": DEFAULT_AS_OF,
        "sourceUpdatedAt": DEFAULT_AS_OF,
        "buildId": BUILD_ID,
        "cohortSelection": {
            "requestedPlayers": [
                {"playerId": player_id, "playerName": player_name}
                for player_id, player_name in REQUESTED_PLAYERS
            ],
            "fillRule": (
                "After all requested source-backed players resolve, fill by descending "
                "regular-season PPR among QB/RB/WR/TE rows until MAX_PLAYERS."
            ),
            "minPlayers": MIN_PLAYERS,
            "maxPlayers": MAX_PLAYERS,
        },
        "players": players,
    }


def validate_cohort(cohort: dict[str, Any]) -> None:
    players = cohort.get("players")
    if not isinstance(players, list):
        raise ValueError("Cohort artifact must include a players array.")
    if not MIN_PLAYERS <= len(players) <= MAX_PLAYERS:
        raise ValueError(f"Cohort player count must be between {MIN_PLAYERS} and {MAX_PLAYERS}.")
    positions = {str(player.get("position", "")).upper() for player in players}
    if not positions.issubset(INCLUDED_POSITIONS):
        raise ValueError(f"Cohort contains unsupported positions: {sorted(positions)}")

    for player in players:
        if not player.get("source"):
            raise ValueError(f"Player {player.get('playerId')} is missing source metadata.")
        weekly_rows = player.get("weeklyRows")
        if not isinstance(weekly_rows, list) or not weekly_rows:
            raise ValueError(f"Player {player.get('playerId')} must include weekly rows.")
        weekly_sum = _round(sum(float(row["pprPoints"]) for row in weekly_rows), 2)
        if player.get("seasonTotal", {}).get("pprPoints") != weekly_sum:
            raise ValueError(
                f"Player {player.get('playerId')} season total does not equal weekly sum."
            )
        seen: set[tuple[int, Any, Any]] = set()
        for row in weekly_rows:
            key = (int(row["week"]), row.get("gameId"), row.get("opponent"))
            if key in seen:
                raise ValueError(f"Duplicate weekly row for {player.get('playerId')}: {key}")
            seen.add(key)
            for required in (
                "sourceProvider",
                "sourceFile",
                "sourcePath",
                "sourceProvenance",
                "asOf",
                "sourceUpdatedAt",
                "buildId",
            ):
                if not row.get(required):
                    raise ValueError(
                        f"Week {row.get('week')} for {player.get('playerId')} "
                        f"is missing source metadata field {required}."
                    )


def write_cohort(output_path: Path = OUTPUT_PATH) -> Path:
    cohort = build_cohort()
    validate_cohort(cohort)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cohort, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    path = write_cohort()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
