from __future__ import annotations

import json
import sys
from pathlib import Path

import nflreadpy as nfl

SEASON = 2025
OUTPUT_PATH = Path("data/processed/evidence/roster_player_team_map_2025.source_backed.json")
INCLUDED_POSITIONS = {"QB", "RB", "WR", "TE"}


def _resolve_column(columns: set[str], candidates: list[str], field_name: str) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise ValueError(
        f"Missing required column for '{field_name}'. "
        f"Expected one of {candidates}, found columns={sorted(columns)}"
    )


def build_source_backed_payload() -> dict:
    df = nfl.load_rosters_weekly([SEASON])
    source_columns = list(df.columns)
    print("Detected nflreadpy weekly roster columns:")
    print(source_columns)

    columns = set(source_columns)
    season_col = _resolve_column(columns, ["season"], "season")
    week_col = _resolve_column(columns, ["week"], "week")
    player_id_col = _resolve_column(columns, ["gsis_id", "player_id"], "player_id")
    player_name_col = _resolve_column(columns, ["full_name", "player_name", "football_name"], "player_name")
    position_col = _resolve_column(columns, ["position"], "position")
    team_col = _resolve_column(columns, ["team", "recent_team"], "team")

    records: list[dict] = []
    seen = set()

    for row in df.to_dict("records"):
        player_id = row.get(player_id_col)
        team = row.get(team_col)
        if player_id is None or str(player_id).strip() == "":
            continue
        if team is None or str(team).strip() == "":
            continue

        position = str(row.get(position_col, "")).upper().strip()
        if position not in INCLUDED_POSITIONS:
            continue

        season = int(row[season_col])
        week = int(row[week_col])
        player_id_str = str(player_id).strip()
        key = f"{season}-{week}-{player_id_str}"
        if key in seen:
            raise ValueError(f"Duplicate roster player/team row detected ({key}). Build fails closed.")
        seen.add(key)

        records.append(
            {
                "season": season,
                "week": week,
                "player_id": player_id_str,
                "player_name": str(row.get(player_name_col, "")).strip() or player_id_str,
                "position": position,
                "team": str(team).strip(),
                "active_roster_status": "unknown",
                "source_status": "source_verified",
            }
        )

    if not records:
        raise ValueError("No valid source-backed roster records were produced. Build fails closed.")

    records.sort(key=lambda r: (r["season"], r["week"], r["team"], r["player_id"]))

    return {
        "provenance": "nflreadpy.load_rosters_weekly",
        "source_path": "nflverse weekly rosters via nflreadpy",
        "source_status": "source_verified",
        "generated_from": [
            "scripts/build_roster_player_team_map_source_backed_2025.py",
            "nflreadpy.load_rosters_weekly([2025])",
        ],
        "records": records,
    }


def main() -> int:
    payload = build_source_backed_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
    print(f"Wrote source-backed roster identity artifact: {OUTPUT_PATH.resolve()}")
    print(f"Record count: {len(payload['records'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
