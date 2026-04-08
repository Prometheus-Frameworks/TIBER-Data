from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.settings import PipelineConfig
from src.ingest.public import PublicDataClient

SUPPORTED_SEASON = 2024
SUPPORTED_WEEK = 1
SUPPORTED_PLAYER_IDS = (
    "00-0033901",  # Jared Goff
    "00-0036976",  # Jahmyr Gibbs
    "00-0037183",  # Kirk Cousins
    "00-0037834",  # Amon-Ra St. Brown
    "00-0038047",  # Sam LaPorta
    "00-0038122",  # Kyle Pitts
    "00-0038134",  # Bijan Robinson
    "00-0039152",  # Drake London
)
SUPPORTED_TEAMS = ("ATL", "DET")

WEEKLY_PLAYER_STATS_OUTPUT_PATH = (
    "data/raw/forge/weekly_player_stats.upstream_public_2024_w01_8player_scaffold.json"
)
TEAM_WEEK_CONTEXT_OUTPUT_PATH = (
    "data/raw/forge/team_week_context.upstream_public_2024_w01_2team_scaffold.json"
)


@dataclass(slots=True)
class ForgeWeeklyUpstreamSupportSlice:
    weekly_player_stats_records: list[dict[str, Any]]
    team_week_context_records: list[dict[str, Any]]
    weekly_player_stats_source_path: str
    team_week_context_source_path: str


class ForgeWeeklyUpstreamSupportScaffoldBuilder:
    def __init__(self, config: PipelineConfig) -> None:
        if config.seasons != [SUPPORTED_SEASON]:
            raise ValueError(
                f"Upstream scaffold currently supports seasons=[{SUPPORTED_SEASON}] only; got {config.seasons}."
            )
        self.config = config
        self.client = PublicDataClient(config)

    def build(self) -> ForgeWeeklyUpstreamSupportSlice:
        player_table = self.client.fetch_weekly_player_stats()
        team_table = self.client.fetch_team_week_context()

        if player_table.provenance == "offline_fixture" or team_table.provenance == "offline_fixture":
            raise RuntimeError(
                "Upstream scaffold requires public-source reads. "
                "Disable offline fallback and ensure upstream data is available."
            )

        player_records = self._select_player_records(player_table.records)
        team_records = self._select_team_records(team_table.records)

        return ForgeWeeklyUpstreamSupportSlice(
            weekly_player_stats_records=player_records,
            team_week_context_records=team_records,
            weekly_player_stats_source_path=player_table.source_path,
            team_week_context_source_path=team_table.source_path,
        )

    def _select_player_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected = [
            record
            for record in records
            if int(record.get("season", 0)) == SUPPORTED_SEASON
            and int(record.get("week", 0)) == SUPPORTED_WEEK
            and str(record.get("player_id", "")) in SUPPORTED_PLAYER_IDS
        ]
        selected_by_id = {str(record["player_id"]): record for record in selected}
        missing_ids = sorted(set(SUPPORTED_PLAYER_IDS) - set(selected_by_id))
        if missing_ids:
            raise RuntimeError(
                "Upstream player stats slice is incomplete for supported cohort; "
                f"missing player_ids={missing_ids}."
            )

        ordered: list[dict[str, Any]] = []
        for player_id in sorted(selected_by_id):
            record = selected_by_id[player_id]
            ordered.append(
                {
                    "player_id": str(record["player_id"]),
                    "full_name": str(record["player_display_name"]),
                    "position": str(record["position"]),
                    "team": str(record["recent_team"]),
                    "season": int(record["season"]),
                    "week": int(record["week"]),
                    "targets": int(record.get("targets", 0) or 0),
                    "receptions": int(record.get("receptions", 0) or 0),
                    "receiving_yards": int(record.get("receiving_yards", 0) or 0),
                    "receiving_tds": int(record.get("receiving_tds", 0) or 0),
                    "rushing_attempts": int(record.get("carries", 0) or 0),
                    "rushing_yards": int(record.get("rushing_yards", 0) or 0),
                    "rushing_tds": int(record.get("rushing_tds", 0) or 0),
                    "pass_attempts": int(record.get("attempts", 0) or 0),
                    "completions": int(record.get("completions", 0) or 0),
                    "passing_yards": int(record.get("passing_yards", 0) or 0),
                    "passing_tds": int(record.get("passing_tds", 0) or 0),
                    "fantasy_points_ppr": float(record.get("fantasy_points_ppr", 0) or 0),
                    "air_yards": int(record.get("air_yards", 0) or 0),
                    "red_zone_targets": (
                        int(record["red_zone_targets"]) if record.get("red_zone_targets") is not None else None
                    ),
                }
            )
        return ordered

    def _select_team_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected = [
            record
            for record in records
            if int(record.get("season", 0)) == SUPPORTED_SEASON
            and int(record.get("week", 0)) == SUPPORTED_WEEK
            and str(record.get("team", "")) in SUPPORTED_TEAMS
        ]
        selected_by_team = {str(record["team"]): record for record in selected}
        missing_teams = sorted(set(SUPPORTED_TEAMS) - set(selected_by_team))
        if missing_teams:
            raise RuntimeError(
                "Upstream team context slice is incomplete for supported cohort; "
                f"missing teams={missing_teams}."
            )

        ordered: list[dict[str, Any]] = []
        for team in sorted(selected_by_team):
            record = selected_by_team[team]
            ordered.append(
                {
                    "team": str(record["team"]),
                    "season": int(record["season"]),
                    "week": int(record["week"]),
                    "team_pass_attempts": int(record.get("pass_attempts", 0) or 0),
                    "team_rush_attempts": int(record.get("rush_attempts", 0) or 0),
                    "team_points": int(record.get("points", 0) or 0),
                    "team_air_yards": int(record.get("air_yards", 0) or 0),
                }
            )
        return ordered


def write_forge_weekly_upstream_support_scaffold(
    output_base_dir: Path | None = None,
) -> tuple[Path, Path]:
    config = PipelineConfig(
        seasons=[SUPPORTED_SEASON],
        allow_offline_fallback=False,
    )
    builder = ForgeWeeklyUpstreamSupportScaffoldBuilder(config)
    support = builder.build()

    base_dir = output_base_dir or config.base_dir
    player_path = base_dir / WEEKLY_PLAYER_STATS_OUTPUT_PATH
    team_path = base_dir / TEAM_WEEK_CONTEXT_OUTPUT_PATH
    player_path.parent.mkdir(parents=True, exist_ok=True)

    player_payload = {
        "provenance": "nflreadpy_or_direct_public_source",
        "source_path": support.weekly_player_stats_source_path,
        "records": support.weekly_player_stats_records,
    }
    team_payload = {
        "provenance": "nflreadpy_or_direct_public_source",
        "source_path": support.team_week_context_source_path,
        "records": support.team_week_context_records,
    }

    player_path.write_text(json.dumps(player_payload, indent=2), encoding="utf-8")
    team_path.write_text(json.dumps(team_payload, indent=2), encoding="utf-8")

    return player_path, team_path
