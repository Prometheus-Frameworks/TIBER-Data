from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest.forge_weekly_upstream_support_scaffold import (
    TEAM_WEEK_CONTEXT_OUTPUT_PATH,
    WEEKLY_PLAYER_STATS_OUTPUT_PATH,
    write_forge_weekly_upstream_support_scaffold,
)


if __name__ == "__main__":
    player_path, team_path = write_forge_weekly_upstream_support_scaffold()
    print("Wrote FORGE upstream-backed weekly support scaffold artifacts:")
    print(f" - {WEEKLY_PLAYER_STATS_OUTPUT_PATH}: {player_path}")
    print(f" - {TEAM_WEEK_CONTEXT_OUTPUT_PATH}: {team_path}")
