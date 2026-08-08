from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import nflreadpy as nfl

SEASON = 2025
OUTPUT_PATH = Path("data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json")
ROSTER_SOURCE_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}


def _resolve_column(columns: set[str], candidates: list[str], field_name: str, required: bool = True) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    if required:
        raise ValueError(
            f"Missing required column for '{field_name}'. Expected one of {candidates}, found columns={sorted(columns)}"
        )
    return None


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
    return value


def _load_roster_position_map() -> dict[tuple[int, int, str], str]:
    if not ROSTER_SOURCE_PATH.exists():
        raise ValueError(f"Roster source-backed artifact required for position fallback is missing: {ROSTER_SOURCE_PATH}")
    payload = json.loads(ROSTER_SOURCE_PATH.read_text(encoding="utf-8"))
    position_map: dict[tuple[int, int, str], str] = {}
    for row in payload.get("records", []):
        key = (int(row["season"]), int(row["week"]), str(row["player_id"]).strip())
        position = str(row.get("position", "")).strip().upper()
        if position in INCLUDED_POSITIONS:
            position_map[key] = position
    return position_map


def build_source_backed_payload() -> dict:
    df = nfl.load_player_stats([SEASON])
    source_columns = list(df.columns)
    print("Detected nflreadpy player stats columns:")
    print(source_columns)

    columns = set(source_columns)
    season_col = _resolve_column(columns, ["season"], "season")
    week_col = _resolve_column(columns, ["week"], "week")
    player_id_col = _resolve_column(columns, ["player_id", "gsis_id"], "player_id")
    player_name_col = _resolve_column(columns, ["player_name", "player_display_name", "full_name"], "player_name")
    team_col = _resolve_column(columns, ["recent_team", "team"], "team")
    position_col = _resolve_column(columns, ["position"], "position", required=False)
    opponent_col = _resolve_column(columns, ["opponent_team", "opponent"], "opponent", required=False)

    receptions_col = _resolve_column(columns, ["receptions"], "receptions", required=False)
    targets_col = _resolve_column(columns, ["targets"], "targets", required=False)
    receiving_yards_col = _resolve_column(columns, ["receiving_yards"], "receiving_yards", required=False)
    receiving_tds_col = _resolve_column(columns, ["receiving_tds"], "receiving_tds", required=False)
    rushing_attempts_col = _resolve_column(columns, ["carries", "rushing_attempts"], "rushing_attempts", required=False)
    rushing_yards_col = _resolve_column(columns, ["rushing_yards"], "rushing_yards", required=False)
    rushing_tds_col = _resolve_column(columns, ["rushing_tds"], "rushing_tds", required=False)
    passing_yards_col = _resolve_column(columns, ["passing_yards"], "passing_yards", required=False)
    passing_tds_col = _resolve_column(columns, ["passing_tds"], "passing_tds", required=False)
    interceptions_col = _resolve_column(columns, ["interceptions", "passing_interceptions"], "interceptions", required=False)

    roster_position_map = _load_roster_position_map()

    records: list[dict] = []
    seen = set()

    for row in _records_from_dataframe(df):
        player_id = row.get(player_id_col)
        team = row.get(team_col)
        if player_id is None or str(player_id).strip() == "":
            continue
        if team is None or str(team).strip() == "":
            continue

        season = int(row[season_col])
        week = int(row[week_col])
        player_id_str = str(player_id).strip()

        position = ""
        if position_col is not None:
            position = str(_json_safe_value(row.get(position_col, "")) or "").strip().upper()
        if position not in INCLUDED_POSITIONS:
            position = roster_position_map.get((season, week, player_id_str), "")
        if position not in INCLUDED_POSITIONS:
            continue

        key = f"{season}-{week}-{player_id_str}"
        if key in seen:
            raise ValueError(f"Duplicate player weekly outcome row detected ({key}). Build fails closed.")
        seen.add(key)

        def _value(col: str | None):
            return None if col is None else _json_safe_value(row.get(col))

        records.append(
            {
                "season": season,
                "week": week,
                "player_id": player_id_str,
                "player_name": str(row.get(player_name_col, "")).strip() or player_id_str,
                "team": str(team).strip(),
                "position": position,
                "opponent": _value(opponent_col),
                "receptions": _value(receptions_col),
                "targets": _value(targets_col),
                "receiving_yards": _value(receiving_yards_col),
                "receiving_tds": _value(receiving_tds_col),
                "rushing_attempts": _value(rushing_attempts_col),
                "rushing_yards": _value(rushing_yards_col),
                "rushing_tds": _value(rushing_tds_col),
                "passing_yards": _value(passing_yards_col),
                "passing_tds": _value(passing_tds_col),
                "interceptions": _value(interceptions_col),
            }
        )

    if not records:
        raise ValueError("No valid source-backed player weekly ppr outcome records were produced. Build fails closed.")

    records.sort(key=lambda r: (r["season"], r["week"], r["player_id"]))

    return {
        "provenance": "nflreadpy.load_player_stats",
        "source_path": "nflverse player stats via nflreadpy",
        "generated_from": [
            "scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py",
            "nflreadpy.load_player_stats([2025])",
        ],
        "records": records,
    }


def main() -> int:
    payload = build_source_backed_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(f"{json.dumps(payload, indent=2, allow_nan=False)}\n", encoding="utf-8")
    print(f"Wrote source-backed player weekly ppr outcomes artifact: {OUTPUT_PATH.resolve()}")
    print(f"Record count: {len(payload['records'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
