#!/usr/bin/env python3
"""Inspect nflreadpy participation column availability for season 2025."""

from __future__ import annotations

import sys

REQUIRED_COLUMNS = [
    "players_on_play",
    "offense_players",
    "defense_players",
    "offense_formation",
    "offense_personnel",
    "defense_personnel",
    "n_offense",
    "n_defense",
    "route",
    "possession_team",
    "season",
    "week",
    "play_id",
]

GAME_ID_CANDIDATES = ["game_id", "nflverse_game_id"]


def main() -> int:
    try:
        import nflreadpy
    except Exception as exc:  # fail-closed requirement
        print(f"ERROR: unable to import nflreadpy: {exc}")
        return 1

    if not hasattr(nflreadpy, "load_participation"):
        print("ERROR: nflreadpy.load_participation is unavailable")
        return 1

    try:
        df = nflreadpy.load_participation([2025])
    except Exception as exc:
        print(f"WARNING: load_participation([2025]) failed: {exc}")
        print("No column audit performed because data could not be loaded in this environment.")
        return 0

    columns = list(getattr(df, "columns", []))

    print("=== nflreadpy.load_participation([2025]) audit ===")
    print(f"row_count: {len(df)}")
    print(f"column_count: {len(columns)}")
    print("\nDetected columns:")
    for col in sorted(columns):
        print(f"- {col}")

    print("\nRequired column checks:")
    for col in REQUIRED_COLUMNS:
        print(f"- {col}: {'present' if col in columns else 'missing'}")

    print("\nGame id column checks:")
    for col in GAME_ID_CANDIDATES:
        print(f"- {col}: {'present' if col in columns else 'missing'}")

    print("\nSummary:")
    if any(col in columns for col in GAME_ID_CANDIDATES):
        print("- game identifier: present via at least one candidate column")
    else:
        print("- game identifier: missing from listed candidates")

    return 0


if __name__ == "__main__":
    sys.exit(main())
