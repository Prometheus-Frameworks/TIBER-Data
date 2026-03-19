from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
from fastapi.testclient import TestClient

import src.api as api
from src.api import app

client = TestClient(app)

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
    }


def test_health_reports_missing_outputs(tmp_path: Path) -> None:
    configure_datasets(tmp_path)

    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert {item["dataset"] for item in body["missing"]} == {
        "teams",
        "players",
        "team_context",
        "player_role_inputs",
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

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    teams = client.get("/api/teams")
    assert teams.status_code == 200
    assert teams.json()["data"][0]["team"] == "BAL"

    players = client.get("/api/players")
    assert players.status_code == 200
    assert players.json()["data"][0]["player_id"] == "p1"

    team_context = client.get("/api/team-context/BAL")
    assert team_context.status_code == 200
    assert team_context.json()["count"] == 1

    player_role_inputs = client.get("/api/player-role-inputs/p1")
    assert player_role_inputs.status_code == 200
    assert player_role_inputs.json()["data"][0]["target_share"] == 0.25


def test_filtered_endpoints_return_not_found_for_unknown_keys(tmp_path: Path) -> None:
    configure_datasets(tmp_path)
    write_parquet(api.DATASETS["team_context"], [TEAM_CONTEXT_ROW])
    write_parquet(api.DATASETS["player_role_inputs"], [PLAYER_ROLE_ROW])

    missing_team = client.get("/api/team-context/KC")
    assert missing_team.status_code == 404
    assert missing_team.json()["detail"]["error"] == "team_not_found"

    missing_player = client.get("/api/player-role-inputs/p2")
    assert missing_player.status_code == 404
    assert missing_player.json()["detail"]["error"] == "player_not_found"


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

    players = client.get("/api/players", params={"team": "bal", "season": 2024, "position": "wr"})
    assert players.status_code == 200
    assert players.json()["count"] == 1
    assert players.json()["data"] == [
        {
            "player_id": "p1",
            "full_name": "Player One",
            "position": "WR",
            "team": "BAL",
            "season": 2024,
        }
    ]

    team_context = client.get("/api/team-context", params={"team": "kc", "season": 2023, "week": 2})
    assert team_context.status_code == 200
    assert team_context.json()["count"] == 1
    assert team_context.json()["data"][0]["team"] == "KC"

    player_role_inputs = client.get(
        "/api/player-role-inputs",
        params={"team": "bal", "season": 2024, "week": 1, "position": "wr", "player_id": "p1"},
    )
    assert player_role_inputs.status_code == 200
    assert player_role_inputs.json()["count"] == 1
    assert player_role_inputs.json()["data"][0]["player_id"] == "p1"


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

    players = client.get("/api/players", params={"team": "KC"})
    assert players.status_code == 200
    assert players.json() == {"dataset": "players", "count": 0, "data": []}

    team_context = client.get("/api/team-context", params={"team": "KC", "season": 2024})
    assert team_context.status_code == 200
    assert team_context.json() == {"dataset": "team_context", "count": 0, "data": []}

    player_role_inputs = client.get(
        "/api/player-role-inputs",
        params={"position": "RB", "player_id": "missing"},
    )
    assert player_role_inputs.status_code == 200
    assert player_role_inputs.json() == {"dataset": "player_role_inputs", "count": 0, "data": []}
