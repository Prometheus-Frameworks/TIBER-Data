from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import PipelineConfig
from src.ingest.forge_weekly_upstream_support_scaffold import (
    ForgeWeeklyUpstreamSupportScaffoldBuilder,
    SUPPORTED_PLAYER_COHORT,
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
        for idx, (player_name, team) in enumerate(reversed(SUPPORTED_PLAYER_COHORT)):
            player_rows.append(
                {
                    "player_id": f"id-{idx}",
                    "player_display_name": player_name,
                    "position": "WR",
                    "team": team,
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

    assert [record["full_name"] for record in selected_players] == [
        player_name for _ in sorted(SUPPORTED_WEEKS) for player_name, _team in SUPPORTED_PLAYER_COHORT
    ]
    assert [record["team"] for record in selected_teams] == [
        team for _ in sorted(SUPPORTED_WEEKS) for team in sorted(SUPPORTED_TEAMS)
    ]
    assert [record["week"] for record in selected_players] == [
        week for week in sorted(SUPPORTED_WEEKS) for _ in SUPPORTED_PLAYER_COHORT
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
        for idx, (player_name, team) in enumerate(SUPPORTED_PLAYER_COHORT):
            if week == 3 and (player_name, team) == SUPPORTED_PLAYER_COHORT[-1]:
                continue
            player_rows.append(
                {
                    "player_id": f"id-{idx}",
                    "player_display_name": player_name,
                    "position": "WR",
                    "team": team,
                    "season": SUPPORTED_SEASON,
                    "week": week,
                }
            )

    try:
        builder._select_player_records(player_rows)
        assert False, "expected RuntimeError for missing supported row"
    except RuntimeError as exc:
        assert "missing week/player pairs" in str(exc)
