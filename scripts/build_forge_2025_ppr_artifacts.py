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
SCHEMA_VERSION = "v1"
DEFAULT_AS_OF = "2026-04-27T00:00:00Z"

SOURCE_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json")
ROSTER_SOURCE_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
SEASON_OUTPUT_PATH = Path("data/gold/forge/forge_season_player_input_2025.ppr.v1.json")
WEEKLY_OUTPUT_PATH = Path("data/gold/forge/forge_weekly_player_ppr_2025.v1.json")

INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}
STAT_FIELDS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_attempts",
    "rushing_yards",
    "rushing_tds",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "fumbles_lost",
)

# Existing FORGE fixture/calibration names are selected first when the same
# source-backed player rows exist.
PRIORITY_PLAYER_NAME_KEYS = (
    "j.goff",
    "j.gibbs",
    "k.cousins",
    "b.robinson",
    "a.st. brown",
    "d.mooney",
    "s.laporta",
    "z.flowers",
    "k.williams",
    "j.hurts",
)


def _json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if isinstance(value, float) and (math.isnan(value) or not math.isfinite(value)):
            return None
    except TypeError:
        pass
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
        + _number_or_zero(row.get("receptions")) * 1
        + _number_or_zero(row.get("fumbles_lost")) * -2
    )
    return _round(points, 2)


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(
            "Missing source-backed 2025 player-week PPR input. "
            f"Expected {path}. Run the source-backed upstream builder first; "
            "FORGE gold artifacts must not be built from fixture or invented rows."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _load_roster_name_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    for row in payload.get("records", []):
        player_id = str(row.get("player_id", "")).strip()
        player_name = str(row.get("player_name", "")).strip()
        if player_id and player_name:
            names[player_id] = player_name
    return names


def _source_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Source-backed player-week PPR payload must contain a records array.")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for raw in records:
        row = dict(raw)
        season = int(row.get("season"))
        week = int(row.get("week"))
        player_id = str(row.get("player_id", "")).strip()
        position = str(row.get("position", "")).strip().upper()
        if season != SEASON or week not in REGULAR_SEASON_WEEKS:
            continue
        if not player_id or position not in INCLUDED_POSITIONS:
            continue
        key = (season, week, player_id)
        if key in seen:
            raise ValueError(f"Duplicate source-backed player-week row detected: {key}")
        seen.add(key)
        rows.append(row)
    if not rows:
        raise ValueError("No source-backed regular-season 2025 QB/RB/WR/TE rows are available.")
    return rows


def _latest_team(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: (int(row["week"]), str(row.get("team", ""))))
    return str(ordered[-1].get("team", "")).strip()


def _stat_block(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "passingYards": _optional_number(row.get("passing_yards")),
        "passingTds": _optional_int(row.get("passing_tds")),
        "interceptions": _optional_int(row.get("interceptions")),
        "rushingAttempts": _optional_int(row.get("rushing_attempts")),
        "rushingYards": _optional_number(row.get("rushing_yards")),
        "rushingTds": _optional_int(row.get("rushing_tds")),
        "targets": _optional_int(row.get("targets")),
        "receptions": _optional_int(row.get("receptions")),
        "receivingYards": _optional_number(row.get("receiving_yards")),
        "receivingTds": _optional_int(row.get("receiving_tds")),
        "fumblesLost": _optional_int(row.get("fumbles_lost")) if "fumbles_lost" in row else None,
    }


def _zero_total_or_null(rows: list[dict[str, Any]], field: str) -> float | int | None:
    values = [row.get(field) for row in rows if _json_safe_value(row.get(field)) is not None]
    if not values:
        return None
    total = sum(float(value) for value in values)
    return int(total) if total.is_integer() else _round(total, 2)


def _season_stat_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "passingYards": _zero_total_or_null(rows, "passing_yards"),
        "passingTds": _zero_total_or_null(rows, "passing_tds"),
        "interceptions": _zero_total_or_null(rows, "interceptions"),
        "rushingAttempts": _zero_total_or_null(rows, "rushing_attempts"),
        "rushingYards": _zero_total_or_null(rows, "rushing_yards"),
        "rushingTds": _zero_total_or_null(rows, "rushing_tds"),
        "targets": _zero_total_or_null(rows, "targets"),
        "receptions": _zero_total_or_null(rows, "receptions"),
        "receivingYards": _zero_total_or_null(rows, "receiving_yards"),
        "receivingTds": _zero_total_or_null(rows, "receiving_tds"),
        "fumblesLost": _zero_total_or_null(rows, "fumbles_lost"),
    }


def _opportunities_from_stats(stats: dict[str, Any]) -> int | None:
    values = [stats.get("rushingAttempts"), stats.get("targets")]
    if all(value is None for value in values):
        return None
    opportunities = _number_or_zero(stats.get("rushingAttempts")) + _number_or_zero(
        stats.get("targets")
    )
    return int(opportunities)


def _build_metadata(source_payload: dict[str, Any], build_id: str) -> dict[str, Any]:
    return {
        "sourceSetId": "nflreadpy.load_player_stats.2025.regular_season.source_backed",
        "asOf": DEFAULT_AS_OF,
        "sourceUpdatedAt": DEFAULT_AS_OF,
        "buildId": build_id,
        "sourceProviders": ["nflverse via nflreadpy"],
        "sourcePaths": [str(SOURCE_PATH), str(ROSTER_SOURCE_PATH)],
        "sourceProvenance": source_payload.get("provenance"),
        "sourcePathLabel": source_payload.get("source_path"),
        "generatedFrom": source_payload.get("generated_from", []),
        "scoringFormat": SCORING_FORMAT,
    }


def _select_player_ids(rows_by_player: dict[str, list[dict[str, Any]]]) -> list[str]:
    summaries: list[dict[str, Any]] = []
    for player_id, rows in rows_by_player.items():
        total = _round(sum(calculate_ppr_points(row) for row in rows), 2)
        first = sorted(rows, key=lambda row: int(row["week"]))[0]
        name_key = str(first.get("player_name", "")).strip().lower()
        summaries.append({"player_id": player_id, "ppr": total, "name_key": name_key})

    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        by_name[summary["name_key"]].append(summary)

    selected: list[str] = []
    for name_key in PRIORITY_PLAYER_NAME_KEYS:
        matches = sorted(
            by_name.get(name_key, []), key=lambda item: (-item["ppr"], item["player_id"])
        )
        if matches and matches[0]["player_id"] not in selected:
            selected.append(matches[0]["player_id"])

    for summary in sorted(summaries, key=lambda item: (-item["ppr"], item["player_id"])):
        if len(selected) >= MAX_PLAYERS:
            break
        if summary["player_id"] not in selected:
            selected.append(summary["player_id"])

    if len(selected) < MIN_PLAYERS:
        raise ValueError(
            f"Only {len(selected)} source-backed fantasy-relevant players are available; "
            f"need at least {MIN_PLAYERS}. Build fails closed."
        )
    return selected


def build_artifacts(
    source_path: Path = SOURCE_PATH,
    roster_source_path: Path = ROSTER_SOURCE_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_payload = _load_payload(source_path)
    name_map = _load_roster_name_map(roster_source_path)
    rows = _source_rows(source_payload)

    rows_by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_player[str(row["player_id"]).strip()].append(row)

    selected_ids = _select_player_ids(rows_by_player)
    selected_set = set(selected_ids)
    selected_rows = [row for row in rows if str(row["player_id"]).strip() in selected_set]
    available_weeks = sorted({int(row["week"]) for row in selected_rows})

    base_metadata = _build_metadata(
        source_payload, "forge-2025-ppr-v1:source-backed:regular-season"
    )
    scoring_rules = {
        "passingYards": "yards / 25",
        "passingTds": "td * 4",
        "interceptions": "interception * -2",
        "rushingYards": "yards / 10",
        "rushingTds": "td * 6",
        "receivingYards": "yards / 10",
        "receivingTds": "td * 6",
        "receptions": "reception * 1",
        "fumblesLost": "fumble lost * -2 when available",
    }

    weekly_records: list[dict[str, Any]] = []
    sorted_weekly_rows = sorted(
        selected_rows,
        key=lambda item: (
            int(item["season"]),
            int(item["week"]),
            str(item["player_id"]),
        ),
    )
    for row in sorted_weekly_rows:
        player_id = str(row["player_id"]).strip()
        stats = _stat_block(row)
        weekly_records.append(
            {
                "playerId": player_id,
                "playerName": name_map.get(
                    player_id, str(row.get("player_name", player_id)).strip()
                ),
                "team": str(row.get("team", "")).strip(),
                "position": str(row.get("position", "")).strip().upper(),
                "season": int(row["season"]),
                "week": int(row["week"]),
                "opponent": _json_safe_value(row.get("opponent")),
                "scoringFormat": SCORING_FORMAT,
                "pprPoints": calculate_ppr_points(row),
                "opportunities": _opportunities_from_stats(stats),
                "stats": stats,
                "source": {
                    "sourceSetId": base_metadata["sourceSetId"],
                    "sourceUpdatedAt": base_metadata["sourceUpdatedAt"],
                    "sourceProviders": base_metadata["sourceProviders"],
                },
            }
        )

    season_records: list[dict[str, Any]] = []
    for player_id in selected_ids:
        player_rows = sorted(rows_by_player[player_id], key=lambda row: int(row["week"]))
        stats = _season_stat_block(player_rows)
        total = _round(sum(calculate_ppr_points(row) for row in player_rows), 2)
        games = len(player_rows)
        first = player_rows[0]
        season_records.append(
            {
                "playerId": player_id,
                "playerName": name_map.get(
                    player_id, str(first.get("player_name", player_id)).strip()
                ),
                "team": _latest_team(player_rows),
                "position": str(first.get("position", "")).strip().upper(),
                "season": SEASON,
                "weeks": [int(row["week"]) for row in player_rows],
                "games": games,
                "scoringFormat": SCORING_FORMAT,
                "pprTotal": total,
                "ppg": _round(total / games, 2) if games else None,
                "opportunities": _opportunities_from_stats(stats),
                "stats": stats,
                "source": {
                    "sourceSetId": base_metadata["sourceSetId"],
                    "sourceUpdatedAt": base_metadata["sourceUpdatedAt"],
                    "sourceProviders": base_metadata["sourceProviders"],
                },
            }
        )

    shared = {
        "season": SEASON,
        "schemaVersion": SCHEMA_VERSION,
        "scoringFormat": SCORING_FORMAT,
        "regularSeasonWeeks": list(REGULAR_SEASON_WEEKS),
        "availableWeeks": available_weeks,
        "playerCount": len(selected_ids),
        "scoringRules": scoring_rules,
        "metadata": base_metadata,
    }
    season_artifact = {
        "artifactId": "forge_season_player_input_2025.ppr.v1",
        **shared,
        "records": season_records,
    }
    weekly_artifact = {
        "artifactId": "forge_weekly_player_ppr_2025.v1",
        **shared,
        "records": weekly_records,
    }
    return season_artifact, weekly_artifact


def write_artifacts(
    season_output_path: Path = SEASON_OUTPUT_PATH,
    weekly_output_path: Path = WEEKLY_OUTPUT_PATH,
) -> tuple[Path, Path]:
    season_artifact, weekly_artifact = build_artifacts()
    season_output_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_output_path.parent.mkdir(parents=True, exist_ok=True)
    season_output_path.write_text(
        json.dumps(season_artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    weekly_output_path.write_text(
        json.dumps(weekly_artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return season_output_path, weekly_output_path


def main() -> None:
    season_path, weekly_path = write_artifacts()
    print(f"Wrote {season_path}")
    print(f"Wrote {weekly_path}")


if __name__ == "__main__":
    main()
