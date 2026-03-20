from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
import pytest
from fastapi import HTTPException

import src.api as api

TEAM_CONTEXT_ROW: dict[str, Any] = {
    "team": "BAL",
    "season": 2024,
    "week": 1,
    "team_pass_attempts": 30.0,
    "team_rush_attempts": 20.0,
    "neutral_pass_rate": None,
    "red_zone_pass_rate": None,
    "pace_proxy": 50.0,
    "team_air_yards": 280.0,
    "qb_epa_per_dropback": None,
    "target_competition_index": 2.5,
    "receiver_room_certainty": None,
}

PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW: dict[str, Any] = {
    "player_id": "p1",
    "player_name": "Player One",
    "position": "WR",
    "team": "BAL",
    "season": 2024,
    "week": 1,
    "target_share": 0.25,
    "air_yard_share": 0.3,
    "route_participation": None,
    "slot_rate": None,
    "inline_rate": None,
    "wide_rate": None,
    "red_zone_target_share": None,
    "first_read_share": None,
    "average_depth_of_target": 12.5,
    "explosive_target_rate": None,
    "personnel_versatility": None,
    "competition_for_role": 0.35,
    "injury_risk": None,
    "vacated_targets_available": 0.18,
}

TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW: dict[str, Any] = {
    "team_id": "BAL",
    "team_name": "Ravens",
    "team": "BAL",
    "season": 2024,
    "week": 1,
    "pass_rate_over_expected": None,
    "neutral_pass_rate": None,
    "red_zone_pass_rate": None,
    "pace_index": 1.05,
    "quarterback_stability": None,
    "play_caller_continuity": None,
    "target_competition_index": 2.5,
    "receiver_room_certainty": None,
    "vacated_target_share": 0.18,
}

PLAYER_ROLE_ROW: dict[str, Any] = {
    "player_id": "p1",
    "full_name": "Player One",
    "position": "WR",
    "team": "BAL",
    "season": 2024,
    "week": 1,
    "targets": 8.0,
    "receptions": 6.0,
    "receiving_yards": 80.0,
    "receiving_tds": 1.0,
    "target_share": 0.25,
    "red_zone_targets": None,
    "air_yards": 100.0,
    "air_yards_share": 0.3,
    "routes_run": None,
    "route_share": None,
    "snap_share": None,
    "yprr": None,
    "tprr": None,
}


def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(path)


def configure_datasets(base_dir: Path) -> None:
    api.DATASETS = {
        "teams": base_dir / "silver" / "teams.parquet",
        "players": base_dir / "silver" / "players.parquet",
        "team_context": base_dir / "gold" / "team_context_weekly.parquet",
        "player_role_inputs": base_dir / "gold" / "player_role_inputs_weekly.parquet",
        "player_role_profile_compatibility": base_dir
        / "gold"
        / "player_role_profile_compatibility_weekly.parquet",
        "team_opportunity_context_compatibility": base_dir
        / "gold"
        / "team_opportunity_context_compatibility_weekly.parquet",
    }


def response_body(response: Any) -> dict[str, Any]:
    return json.loads(response.body.decode("utf-8"))


def test_health_reports_missing_outputs(tmp_path: Path) -> None:
    configure_datasets(tmp_path)

    response = api.health()

    assert response.status_code == 503
    body = response_body(response)
    assert body["status"] == "error"
    assert {item["dataset"] for item in body["missing"]} == {
        "teams",
        "players",
        "team_context",
        "player_role_inputs",
        "player_role_profile_compatibility",
        "team_opportunity_context_compatibility",
    }


def test_read_only_endpoints_return_expected_rows(tmp_path: Path) -> None:
    configure_datasets(tmp_path)
    write_parquet(
        api.DATASETS["teams"],
        [
            {
                "team": "BAL",
                "team_name": "Ravens",
                "conference": "AFC",
                "division": "North",
            }
        ],
    )
    write_parquet(
        api.DATASETS["players"],
        [
            {
                "player_id": "p1",
                "full_name": "Player One",
                "position": "WR",
                "team": "BAL",
                "season": 2024,
            }
        ],
    )
    write_parquet(api.DATASETS["team_context"], [TEAM_CONTEXT_ROW])
    write_parquet(api.DATASETS["player_role_inputs"], [PLAYER_ROLE_ROW])
    write_parquet(
        api.DATASETS["player_role_profile_compatibility"],
        [PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW],
    )
    write_parquet(
        api.DATASETS["team_opportunity_context_compatibility"],
        [TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW],
    )

    health = api.health()
    assert health.status_code == 200
    assert response_body(health)["status"] == "ok"

    teams = api.get_teams()
    assert teams.status_code == 200
    assert response_body(teams)["data"][0]["team"] == "BAL"

    players = api.get_players(team=None, season=None, player_id=None, position=None)
    assert players.status_code == 200
    assert response_body(players)["data"][0]["player_id"] == "p1"

    team_context = api.get_team_context_for_team("BAL")
    assert team_context.status_code == 200
    assert response_body(team_context)["count"] == 1

    player_role_inputs = api.get_player_role_inputs_for_player("p1")
    assert player_role_inputs.status_code == 200
    assert response_body(player_role_inputs)["data"][0]["target_share"] == 0.25

    compat_player = api.get_player_role_profile_compatibility_for_player("p1")
    assert compat_player.status_code == 200
    assert response_body(compat_player)["data"][0]["player_name"] == "Player One"

    compat_team = api.get_team_opportunity_context_compatibility_for_team("BAL")
    assert compat_team.status_code == 200
    assert response_body(compat_team)["data"][0]["team_id"] == "BAL"


def test_filtered_endpoints_return_not_found_for_unknown_keys(tmp_path: Path) -> None:
    configure_datasets(tmp_path)
    write_parquet(api.DATASETS["team_context"], [TEAM_CONTEXT_ROW])
    write_parquet(api.DATASETS["player_role_inputs"], [PLAYER_ROLE_ROW])
    write_parquet(
        api.DATASETS["player_role_profile_compatibility"],
        [PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW],
    )
    write_parquet(
        api.DATASETS["team_opportunity_context_compatibility"],
        [TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW],
    )

    with pytest.raises(HTTPException) as missing_team:
        api.get_team_context_for_team("KC")
    assert missing_team.value.status_code == 404
    assert missing_team.value.detail["error"] == "team_not_found"

    with pytest.raises(HTTPException) as missing_player:
        api.get_player_role_inputs_for_player("p2")
    assert missing_player.value.status_code == 404
    assert missing_player.value.detail["error"] == "player_not_found"

    with pytest.raises(HTTPException) as missing_compat_team:
        api.get_team_opportunity_context_compatibility_for_team("KC")
    assert missing_compat_team.value.status_code == 404
    assert missing_compat_team.value.detail["error"] == "team_not_found"

    with pytest.raises(HTTPException) as missing_compat_player:
        api.get_player_role_profile_compatibility_for_player("p2")
    assert missing_compat_player.value.status_code == 404
    assert missing_compat_player.value.detail["error"] == "player_not_found"


def test_collection_filters_return_only_matching_rows(tmp_path: Path) -> None:
    configure_datasets(tmp_path)
    write_parquet(
        api.DATASETS["players"],
        [
            {
                "player_id": "p1",
                "full_name": "Player One",
                "position": "WR",
                "team": "BAL",
                "season": 2024,
            },
            {
                "player_id": "p2",
                "full_name": "Player Two",
                "position": "RB",
                "team": "KC",
                "season": 2023,
            },
        ],
    )
    write_parquet(
        api.DATASETS["team_context"],
        [
            TEAM_CONTEXT_ROW,
            {
                **TEAM_CONTEXT_ROW,
                "team": "KC",
                "season": 2023,
                "week": 2,
                "team_pass_attempts": 35.0,
            },
        ],
    )
    write_parquet(
        api.DATASETS["player_role_inputs"],
        [
            PLAYER_ROLE_ROW,
            {
                **PLAYER_ROLE_ROW,
                "player_id": "p2",
                "full_name": "Player Two",
                "position": "RB",
                "team": "KC",
                "season": 2023,
                "week": 2,
                "targets": 4.0,
                "target_share": 0.1,
            },
        ],
    )
    write_parquet(
        api.DATASETS["player_role_profile_compatibility"],
        [
            PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW,
            {
                **PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW,
                "player_id": "p2",
                "player_name": "Player Two",
                "position": "RB",
                "team": "KC",
                "season": 2023,
                "week": 2,
                "target_share": 0.1,
                "competition_for_role": 0.2,
            },
        ],
    )
    write_parquet(
        api.DATASETS["team_opportunity_context_compatibility"],
        [
            TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW,
            {
                **TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW,
                "team_id": "KC",
                "team_name": "Chiefs",
                "team": "KC",
                "season": 2023,
                "week": 2,
                "pace_index": 0.95,
            },
        ],
    )

    players = api.get_players(team="bal", season=2024, player_id=None, position="wr")
    assert players.status_code == 200
    assert response_body(players)["count"] == 1
    assert response_body(players)["data"] == [
        {
            "player_id": "p1",
            "full_name": "Player One",
            "position": "WR",
            "team": "BAL",
            "season": 2024,
        }
    ]

    team_context = api.get_team_context(team="kc", season=2023, week=2)
    assert team_context.status_code == 200
    assert response_body(team_context)["count"] == 1
    assert response_body(team_context)["data"][0]["team"] == "KC"

    player_role_inputs = api.get_player_role_inputs(
        team="bal", season=2024, week=1, position="wr", player_id="p1"
    )
    assert player_role_inputs.status_code == 200
    assert response_body(player_role_inputs)["count"] == 1
    assert response_body(player_role_inputs)["data"][0]["player_id"] == "p1"

    compat_player = api.get_player_role_profile_compatibility(
        team="bal", season=2024, week=1, position="wr", player_id="p1"
    )
    assert compat_player.status_code == 200
    assert response_body(compat_player)["count"] == 1
    assert response_body(compat_player)["data"][0]["vacated_targets_available"] == 0.18

    compat_team = api.get_team_opportunity_context_compatibility(
        team="kc", season=2023, week=2
    )
    assert compat_team.status_code == 200
    assert response_body(compat_team)["count"] == 1
    assert response_body(compat_team)["data"][0]["team_name"] == "Chiefs"


def test_collection_filters_return_empty_data_for_valid_no_match_queries(tmp_path: Path) -> None:
    configure_datasets(tmp_path)
    write_parquet(
        api.DATASETS["players"],
        [
            {
                "player_id": "p1",
                "full_name": "Player One",
                "position": "WR",
                "team": "BAL",
                "season": 2024,
            }
        ],
    )
    write_parquet(api.DATASETS["team_context"], [TEAM_CONTEXT_ROW])
    write_parquet(api.DATASETS["player_role_inputs"], [PLAYER_ROLE_ROW])
    write_parquet(
        api.DATASETS["player_role_profile_compatibility"],
        [PLAYER_ROLE_PROFILE_COMPATIBILITY_ROW],
    )
    write_parquet(
        api.DATASETS["team_opportunity_context_compatibility"],
        [TEAM_OPPORTUNITY_CONTEXT_COMPATIBILITY_ROW],
    )

    players = api.get_players(team="KC", season=None, player_id=None, position=None)
    assert players.status_code == 200
    assert response_body(players) == {"dataset": "players", "count": 0, "data": []}

    team_context = api.get_team_context(team="KC", season=2024, week=None)
    assert team_context.status_code == 200
    assert response_body(team_context) == {"dataset": "team_context", "count": 0, "data": []}

    player_role_inputs = api.get_player_role_inputs(
        team=None, season=None, week=None, position="RB", player_id="missing"
    )
    assert player_role_inputs.status_code == 200
    assert response_body(player_role_inputs) == {
        "dataset": "player_role_inputs",
        "count": 0,
        "data": [],
    }

    compat_player = api.get_player_role_profile_compatibility(
        team=None, season=None, week=None, position="RB", player_id="missing"
    )
    assert compat_player.status_code == 200
    assert response_body(compat_player) == {
        "dataset": "player_role_profile_compatibility",
        "count": 0,
        "data": [],
    }

    compat_team = api.get_team_opportunity_context_compatibility(
        team="KC", season=2024, week=None
    )
    assert compat_team.status_code == 200
    assert response_body(compat_team) == {
        "dataset": "team_opportunity_context_compatibility",
        "count": 0,
        "data": [],
    }
