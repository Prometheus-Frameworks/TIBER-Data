from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import PipelineConfig
from src.ingest.forge_weekly_upstream_support_scaffold import (
    ForgeWeeklyUpstreamSupportScaffoldBuilder,
    SUPPORTED_PLAYER_IDS,
    SUPPORTED_SEASON,
    SUPPORTED_TEAMS,
    SUPPORTED_WEEKS,
)


def test_scaffold_selection_is_deterministic_for_supported_slice() -> None:
    builder = ForgeWeeklyUpstreamSupportScaffoldBuilder(
        PipelineConfig(seasons=[SUPPORTED_SEASON], allow_offline_fallback=False)
    )

    player_rows = []
    for week in reversed(SUPPORTED_WEEKS):
        for idx, player_id in enumerate(reversed(SUPPORTED_PLAYER_IDS)):
            player_rows.append(
                {
                    "player_id": player_id,
                    "player_display_name": f"Player {idx}",
                    "position": "WR",
                    "recent_team": "DET" if idx % 2 == 0 else "ATL",
                    "season": SUPPORTED_SEASON,
                    "week": week,
                    "targets": 1,
                    "receptions": 1,
                    "receiving_yards": 1,
                    "receiving_tds": 0,
                    "carries": 0,
                    "rushing_yards": 0,
                    "rushing_tds": 0,
                    "attempts": 0,
                    "completions": 0,
                    "passing_yards": 0,
                    "passing_tds": 0,
                    "fantasy_points_ppr": 1.0,
                    "air_yards": 1,
                    "red_zone_targets": None,
                }
            )

    team_rows = []
    for week in reversed(SUPPORTED_WEEKS):
        for team in reversed(SUPPORTED_TEAMS):
            team_rows.append(
                {
                    "team": team,
                    "season": SUPPORTED_SEASON,
                    "week": week,
                    "pass_attempts": 30,
                    "rush_attempts": 20,
                    "points": 24,
                    "air_yards": 150,
                }
            )

    selected_players = builder._select_player_records(player_rows)
    selected_teams = builder._select_team_records(team_rows)

    assert [record["player_id"] for record in selected_players] == [
        player_id for _ in sorted(SUPPORTED_WEEKS) for player_id in sorted(SUPPORTED_PLAYER_IDS)
    ]
    assert [record["team"] for record in selected_teams] == [
        team for _ in sorted(SUPPORTED_WEEKS) for team in sorted(SUPPORTED_TEAMS)
    ]
    assert [record["week"] for record in selected_players] == [
        week for week in sorted(SUPPORTED_WEEKS) for _ in SUPPORTED_PLAYER_IDS
    ]
    assert [record["week"] for record in selected_teams] == [
        week for week in sorted(SUPPORTED_WEEKS) for _ in SUPPORTED_TEAMS
    ]


def test_scaffold_requires_complete_weekly_support_set() -> None:
    builder = ForgeWeeklyUpstreamSupportScaffoldBuilder(
        PipelineConfig(seasons=[SUPPORTED_SEASON], allow_offline_fallback=False)
    )

    player_rows = []
    for week in SUPPORTED_WEEKS:
        for player_id in SUPPORTED_PLAYER_IDS:
            if week == 3 and player_id == SUPPORTED_PLAYER_IDS[-1]:
                continue
            player_rows.append(
                {
                    "player_id": player_id,
                    "player_display_name": "X",
                    "position": "WR",
                    "recent_team": "DET",
                    "season": SUPPORTED_SEASON,
                    "week": week,
                }
            )

    try:
        builder._select_player_records(player_rows)
        assert False, "expected RuntimeError for missing supported row"
    except RuntimeError as exc:
        assert "missing week/player_id pairs" in str(exc)
