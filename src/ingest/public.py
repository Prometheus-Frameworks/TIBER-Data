from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from src.config.settings import PipelineConfig
from src.utils.io import should_write

FIXTURE_DATA: dict[str, list[dict[str, Any]]] = {
    "players": [
        {
            "player_id": "00-0037834",
            "full_name": "Amon-Ra St. Brown",
            "position": "WR",
            "team": "DET",
            "season": 2024,
            "age": 24,
            "college": "USC",
            "draft_team": "DET",
            "draft_round": 4,
        },
        {
            "player_id": "00-0038047",
            "full_name": "Sam LaPorta",
            "position": "TE",
            "team": "DET",
            "season": 2024,
            "age": 23,
            "college": "Iowa",
            "draft_team": "DET",
            "draft_round": 2,
        },
        {
            "player_id": "00-0033901",
            "full_name": "Jared Goff",
            "position": "QB",
            "team": "DET",
            "season": 2024,
            "age": 30,
            "college": "California",
            "draft_team": "LAR",
            "draft_round": 1,
        },
        {
            "player_id": "00-0036976",
            "full_name": "Jahmyr Gibbs",
            "position": "RB",
            "team": "DET",
            "season": 2024,
            "age": 22,
            "college": "Alabama",
            "draft_team": "DET",
            "draft_round": 1,
        },
        {
            "player_id": "00-0039152",
            "full_name": "Drake London",
            "position": "WR",
            "team": "ATL",
            "season": 2024,
            "age": 23,
            "college": "USC",
            "draft_team": "ATL",
            "draft_round": 1,
        },
        {
            "player_id": "00-0038134",
            "full_name": "Bijan Robinson",
            "position": "RB",
            "team": "ATL",
            "season": 2024,
            "age": 22,
            "college": "Texas",
            "draft_team": "ATL",
            "draft_round": 1,
        },
        {
            "player_id": "00-0038122",
            "full_name": "Kyle Pitts",
            "position": "TE",
            "team": "ATL",
            "season": 2024,
            "age": 23,
            "college": "Florida",
            "draft_team": "ATL",
            "draft_round": 1,
        },
        {
            "player_id": "00-0037183",
            "full_name": "Kirk Cousins",
            "position": "QB",
            "team": "ATL",
            "season": 2024,
            "age": 36,
            "college": "Michigan State",
            "draft_team": "WAS",
            "draft_round": 4,
        },
    ],
    "teams": [
        {
            "team": "DET",
            "team_name": "Detroit Lions",
            "conference": "NFC",
            "division": "North",
        },
        {
            "team": "ATL",
            "team_name": "Atlanta Falcons",
            "conference": "NFC",
            "division": "South",
        },
    ],
    "weekly_player_stats": [
        {
            "player_id": "00-0037834",
            "full_name": "Amon-Ra St. Brown",
            "position": "WR",
            "team": "DET",
            "season": 2024,
            "week": 1,
            "targets": 9,
            "receptions": 7,
            "receiving_yards": 78,
            "receiving_tds": 1,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 20.8,
            "air_yards": 92,
            "red_zone_targets": 2,
        },
        {
            "player_id": "00-0038047",
            "full_name": "Sam LaPorta",
            "position": "TE",
            "team": "DET",
            "season": 2024,
            "week": 1,
            "targets": 6,
            "receptions": 5,
            "receiving_yards": 58,
            "receiving_tds": 0,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 10.8,
            "air_yards": 48,
            "red_zone_targets": 1,
        },
        {
            "player_id": "00-0033901",
            "full_name": "Jared Goff",
            "position": "QB",
            "team": "DET",
            "season": 2024,
            "week": 1,
            "targets": 0,
            "receptions": 0,
            "receiving_yards": 0,
            "receiving_tds": 0,
            "rushing_attempts": 3,
            "rushing_yards": 7,
            "rushing_tds": 0,
            "pass_attempts": 28,
            "completions": 19,
            "passing_yards": 250,
            "passing_tds": 2,
            "fantasy_points_ppr": 17.7,
            "air_yards": 0,
            "red_zone_targets": 0,
        },
        {
            "player_id": "00-0036976",
            "full_name": "Jahmyr Gibbs",
            "position": "RB",
            "team": "DET",
            "season": 2024,
            "week": 1,
            "targets": 5,
            "receptions": 4,
            "receiving_yards": 32,
            "receiving_tds": 0,
            "rushing_attempts": 12,
            "rushing_yards": 64,
            "rushing_tds": 1,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 19.6,
            "air_yards": 11,
            "red_zone_targets": 0,
        },
        {
            "player_id": "00-0039152",
            "full_name": "Drake London",
            "position": "WR",
            "team": "ATL",
            "season": 2024,
            "week": 1,
            "targets": 8,
            "receptions": 6,
            "receiving_yards": 81,
            "receiving_tds": 1,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 20.1,
            "air_yards": 89,
            "red_zone_targets": 2,
        },
        {
            "player_id": "00-0038134",
            "full_name": "Bijan Robinson",
            "position": "RB",
            "team": "ATL",
            "season": 2024,
            "week": 1,
            "targets": 4,
            "receptions": 3,
            "receiving_yards": 24,
            "receiving_tds": 0,
            "rushing_attempts": 16,
            "rushing_yards": 77,
            "rushing_tds": 1,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 22.1,
            "air_yards": 6,
            "red_zone_targets": 1,
        },
        {
            "player_id": "00-0038122",
            "full_name": "Kyle Pitts",
            "position": "TE",
            "team": "ATL",
            "season": 2024,
            "week": 1,
            "targets": 5,
            "receptions": 4,
            "receiving_yards": 46,
            "receiving_tds": 0,
            "rushing_attempts": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "pass_attempts": 0,
            "completions": 0,
            "passing_yards": 0,
            "passing_tds": 0,
            "fantasy_points_ppr": 8.6,
            "air_yards": 39,
            "red_zone_targets": 0,
        },
        {
            "player_id": "00-0037183",
            "full_name": "Kirk Cousins",
            "position": "QB",
            "team": "ATL",
            "season": 2024,
            "week": 1,
            "targets": 0,
            "receptions": 0,
            "receiving_yards": 0,
            "receiving_tds": 0,
            "rushing_attempts": 2,
            "rushing_yards": 1,
            "rushing_tds": 0,
            "pass_attempts": 31,
            "completions": 22,
            "passing_yards": 271,
            "passing_tds": 2,
            "fantasy_points_ppr": 18.7,
            "air_yards": 0,
            "red_zone_targets": 0,
        },
    ],
    "team_week_context": [
        {"team": "DET", "season": 2024, "week": 1, "team_points": 27},
        {"team": "ATL", "season": 2024, "week": 1, "team_points": 24},
    ],
}


@dataclass(slots=True)
class PublicTable:
    name: str
    records: list[dict[str, Any]]
    provenance: str


class PublicDataClient:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def ingest_all(self) -> dict[str, PublicTable]:
        return {
            "players": self.fetch_players(),
            "teams": self.fetch_teams(),
            "weekly_player_stats": self.fetch_weekly_player_stats(),
            "team_week_context": self.fetch_team_week_context(),
        }

    def fetch_players(self) -> PublicTable:
        data = self._load_via_nflreadpy("players")
        if data is None:
            data = self._fixture("players")
        return PublicTable("players", data, self._provenance("players", data))

    def fetch_teams(self) -> PublicTable:
        data = self._load_via_nflreadpy("teams")
        if data is None:
            data = self._fixture("teams")
        return PublicTable("teams", data, self._provenance("teams", data))

    def fetch_weekly_player_stats(self) -> PublicTable:
        data = self._load_via_nflreadpy("weekly_player_stats")
        if data is None:
            data = self._fixture("weekly_player_stats")
        return PublicTable(
            "weekly_player_stats",
            data,
            self._provenance("weekly_player_stats", data),
        )

    def fetch_team_week_context(self) -> PublicTable:
        data = self._load_http_json(
            "https://example.invalid/tiber-data/team_week_context.json",
            "team_week_context",
        )
        if data is None:
            data = self._fixture("team_week_context")
        return PublicTable(
            "team_week_context",
            data,
            self._provenance("team_week_context", data),
        )

    def write_raw_exports(self, tables: dict[str, PublicTable]) -> None:
        for table in tables.values():
            raw_path = self.config.raw_dir / f"{table.name}.json"
            payload = {"provenance": table.provenance, "records": table.records}
            if should_write(raw_path, self.config.overwrite):
                raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_via_nflreadpy(self, dataset: str) -> list[dict[str, Any]] | None:
        try:
            module = importlib.import_module("nflreadpy")
        except ModuleNotFoundError:
            return None

        fetchers = {
            "players": ["load_players", "load_rosters", "players"],
            "teams": ["load_teams", "teams"],
            "weekly_player_stats": [
                "load_weekly_player_stats",
                "load_weekly",
                "weekly",
            ],
        }
        for candidate in fetchers.get(dataset, []):
            func = getattr(module, candidate, None)
            if not callable(func):
                continue
            result = func(seasons=self.config.seasons) if dataset != "teams" else func()
            if hasattr(result, "to_dict"):
                return result.to_dict(orient="records")
            if isinstance(result, list):
                return result
        return None

    def _load_http_json(self, url: str, dataset: str) -> list[dict[str, Any]] | None:
        try:
            with urlopen(url, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError):
            return None
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and dataset in payload:
            return payload[dataset]
        return None

    def _fixture(self, dataset: str) -> list[dict[str, Any]]:
        if not self.config.allow_offline_fallback:
            raise RuntimeError(
                f"No public data available for {dataset} and offline fallback is disabled."
            )
        seasons = set(self.config.seasons)
        records = FIXTURE_DATA[dataset]
        if records and "season" in records[0]:
            return [record for record in records if int(record["season"]) in seasons]
        return records

    def _provenance(self, dataset: str, data: list[dict[str, Any]]) -> str:
        fixture = FIXTURE_DATA.get(dataset, [])
        filtered_fixture = [
            record for record in fixture if record.get("season", 0) in self.config.seasons
        ]
        if data == fixture or data == filtered_fixture:
            return "offline_fixture"
        return "nflreadpy_or_http"
