from __future__ import annotations

import csv
import importlib
import json
from dataclasses import dataclass
from io import BytesIO, StringIO
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from src.config.settings import PipelineConfig
from src.utils.frames import require_polars
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
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
            "red_zone_targets": None,
        },
    ],
    "team_week_context": [
        {
            "team": "DET",
            "season": 2024,
            "week": 1,
            "team_pass_attempts": 28,
            "team_rush_attempts": 15,
            "team_points": 27,
            "team_air_yards": 151,
        },
        {
            "team": "ATL",
            "season": 2024,
            "week": 1,
            "team_pass_attempts": 31,
            "team_rush_attempts": 18,
            "team_points": 24,
            "team_air_yards": 134,
        },
    ],
}

ROSTERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.parquet"
PLAYER_STATS_WEEK_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "stats_player/stats_player_week_{season}.parquet"
)
TEAM_STATS_WEEK_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "stats_team/stats_team_week_{season}.parquet"
)
TEAMS_CSV_URL = (
    "https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/teams_colors_logos.csv"
)


@dataclass(slots=True)
class PublicTable:
    name: str
    records: list[dict[str, Any]]
    provenance: str
    source_path: str


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
        source_path = self._describe_seasonal_source(ROSTERS_URL)
        data = self._load_via_nflreadpy(
            method_name="load_rosters",
            seasons=self.config.seasons,
            file_type="parquet",
        )
        if data is None:
            data = self._load_seasonal_parquet(ROSTERS_URL)
        if data is None:
            data = self._fixture("players")
        return PublicTable(
            name="players",
            records=data,
            provenance=self._provenance("players", data),
            source_path=source_path,
        )

    def fetch_teams(self) -> PublicTable:
        data = self._load_via_nflreadpy(
            method_name="load_teams",
        )
        if data is None:
            data = self._load_csv(TEAMS_CSV_URL)
        if data is None:
            data = self._fixture("teams")
        return PublicTable(
            name="teams",
            records=data,
            provenance=self._provenance("teams", data),
            source_path=TEAMS_CSV_URL,
        )

    def fetch_weekly_player_stats(self) -> PublicTable:
        source_path = self._describe_seasonal_source(PLAYER_STATS_WEEK_URL)
        data = self._load_via_nflreadpy(
            method_name="load_player_stats",
            seasons=self.config.seasons,
            summary_level="week",
            file_type="parquet",
        )
        if data is None:
            data = self._load_seasonal_parquet(PLAYER_STATS_WEEK_URL)
        if data is None:
            data = self._fixture("weekly_player_stats")
        return PublicTable(
            name="weekly_player_stats",
            records=data,
            provenance=self._provenance("weekly_player_stats", data),
            source_path=source_path,
        )

    def fetch_team_week_context(self) -> PublicTable:
        source_path = self._describe_seasonal_source(TEAM_STATS_WEEK_URL)
        data = self._load_via_nflreadpy(
            method_name="load_team_stats",
            seasons=self.config.seasons,
            summary_level="week",
            file_type="parquet",
        )
        if data is None:
            data = self._load_seasonal_parquet(TEAM_STATS_WEEK_URL)
        if data is None:
            data = self._fixture("team_week_context")
        return PublicTable(
            name="team_week_context",
            records=data,
            provenance=self._provenance("team_week_context", data),
            source_path=source_path,
        )

    def write_raw_exports(self, tables: dict[str, PublicTable]) -> None:
        for table in tables.values():
            raw_path = self.config.raw_dir / f"{table.name}.json"
            payload = {
                "provenance": table.provenance,
                "source_path": table.source_path,
                "records": table.records,
            }
            if should_write(raw_path, self.config.overwrite):
                raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_via_nflreadpy(
        self,
        method_name: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]] | None:
        try:
            module = importlib.import_module("nflreadpy")
        except ModuleNotFoundError:
            return None

        loader = getattr(module, method_name, None)
        if not callable(loader):
            return None

        try:
            result = loader(**kwargs)
        except Exception:
            return None
        records = self._records_from_tabular(result)
        return records

    def _load_seasonal_parquet(self, url_template: str) -> list[dict[str, Any]] | None:
        pl = require_polars()
        frames = []
        for season in self.config.seasons:
            url = url_template.format(season=season)
            payload = self._download_bytes(url)
            if payload is None:
                return None
            frames.append(pl.read_parquet(BytesIO(payload)))
        if not frames:
            return []
        return pl.concat(frames, how="diagonal_relaxed").to_dicts()

    def _load_csv(self, url: str) -> list[dict[str, Any]] | None:
        payload = self._download_bytes(url)
        if payload is None:
            return None
        return list(csv.DictReader(StringIO(payload.decode("utf-8"))))

    def _download_bytes(self, url: str) -> bytes | None:
        try:
            with urlopen(url, timeout=60) as response:
                return response.read()
        except (URLError, TimeoutError):
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
        return "nflreadpy_or_direct_public_source"

    def _describe_seasonal_source(self, url_template: str) -> str:
        return ", ".join(url_template.format(season=season) for season in self.config.seasons)

    def _records_from_tabular(self, result: Any) -> list[dict[str, Any]] | None:
        if result is None:
            return None
        to_dict = getattr(result, "to_dict", None)
        if callable(to_dict):
            try:
                return to_dict(orient="records")
            except TypeError:
                try:
                    return result.to_dicts()  # type: ignore[attr-defined]
                except AttributeError:
                    return None
        to_dicts = getattr(result, "to_dicts", None)
        if callable(to_dicts):
            return to_dicts()
        if isinstance(result, list):
            return result
        return None
