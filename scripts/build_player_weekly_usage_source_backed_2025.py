from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import nflreadpy as nfl

SEASON = 2025
OUTPUT_PATH = Path("data/processed/evidence/player_weekly_usage_2025.source_backed.json")
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




def _is_missing_identity(value) -> bool:
    safe = _json_safe_value(value)
    if safe is None:
        return True
    text = str(safe).strip()
    return text == "" or text.lower() in {"nan", "inf", "-inf", "infinity", "-infinity"}

def build_source_backed_payload() -> dict:
    df = nfl.load_player_stats([SEASON])
    source_columns = list(df.columns)
    print("Detected nflreadpy player stats columns:")
    print(source_columns)

    columns = set(source_columns)
    season_col = _resolve_column(columns, ["season"], "season")
    week_col = _resolve_column(columns, ["week"], "week")
    player_id_col = _resolve_column(columns, ["player_id"], "player_id")
    player_name_col = _resolve_column(columns, ["player_name", "player_display_name"], "player_name", required=False)
    team_col = _resolve_column(columns, ["team", "recent_team"], "team")
    position_col = _resolve_column(columns, ["position"], "position")

    opponent_col = _resolve_column(columns, ["opponent_team"], "opponent", required=False)
    targets_col = _resolve_column(columns, ["targets"], "targets", required=False)
    receptions_col = _resolve_column(columns, ["receptions"], "receptions", required=False)
    target_share_col = _resolve_column(columns, ["target_share"], "target_share", required=False)
    air_yards_col = _resolve_column(columns, ["receiving_air_yards"], "air_yards", required=False)
    air_yards_share_col = _resolve_column(columns, ["air_yards_share"], "air_yards_share", required=False)
    rushing_attempts_col = _resolve_column(columns, ["carries"], "rushing_attempts", required=False)

    records: list[dict] = []
    seen = set()

    def _value(row: dict, col: str | None):
        return None if col is None else _json_safe_value(row.get(col))

    for row in _records_from_dataframe(df):
        player_id = _json_safe_value(row.get(player_id_col))
        team = _json_safe_value(row.get(team_col))
        if _is_missing_identity(player_id):
            continue
        if _is_missing_identity(team):
            continue

        season = int(row[season_col])
        week = int(row[week_col])
        player_id_str = str(player_id).strip()
        team_str = str(team).strip()
        position = str(_json_safe_value(row.get(position_col, "")) or "").strip().upper()
        if position not in INCLUDED_POSITIONS:
            continue

        key = f"{season}-{week}-{player_id_str}"
        if key in seen:
            raise ValueError(f"Duplicate player weekly usage row detected ({key}). Build fails closed.")
        seen.add(key)

        records.append(
            {
                "season": season,
                "week": week,
                "player_id": player_id_str,
                "player_name": str(_json_safe_value(row.get(player_name_col, "")) or "").strip() or player_id_str,
                "team": team_str,
                "position": position,
                "opponent": _value(row, opponent_col) or "",
                "targets": _value(row, targets_col) or 0,
                "receptions": _value(row, receptions_col) or 0,
                "routes_run": None,
                "route_participation": None,
                "target_share": _value(row, target_share_col) if _value(row, target_share_col) is not None else 0,
                "air_yards": _value(row, air_yards_col) if _value(row, air_yards_col) is not None else 0,
                "air_yards_share": _value(row, air_yards_share_col) if _value(row, air_yards_share_col) is not None else 0,
                "rushing_attempts": _value(row, rushing_attempts_col) if _value(row, rushing_attempts_col) is not None else 0,
                "team_rushing_attempts": None,
                "rush_share": None,
                "red_zone_targets": None,
                "red_zone_carries": None,
                "snap_share": None,
            }
        )

    if not records:
        raise ValueError("No valid source-backed player weekly usage records were produced. Build fails closed.")

    records.sort(key=lambda r: (r["season"], r["week"], r["player_id"]))

    return {
        "provenance": "nflreadpy.load_player_stats",
        "source_path": "nflverse player stats via nflreadpy",
        "generated_from": [
            "scripts/build_player_weekly_usage_source_backed_2025.py",
            "nflreadpy.load_player_stats([2025])",
        ],
        "records": records,
    }


def main() -> int:
    payload = build_source_backed_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(f"{json.dumps(payload, indent=2, allow_nan=False)}\n", encoding="utf-8")
    print(f"Wrote source-backed player weekly usage artifact: {OUTPUT_PATH.resolve()}")
    print(f"Record count: {len(payload['records'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
