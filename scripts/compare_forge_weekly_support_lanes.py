from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest.forge_weekly_upstream_support_scaffold import SUPPORTED_SEASON, SUPPORTED_WEEKS

LEGACY_PLAYER_PATH = Path("data/raw/forge/weekly_player_stats.offline_fixture.json")
LEGACY_TEAM_PATH = Path("data/raw/forge/team_week_context.offline_fixture.json")
UPSTREAM_PLAYER_PATH = Path(
    "data/raw/forge/weekly_player_stats.upstream_public_2024_w01_w03_8player_scaffold.json"
)
UPSTREAM_TEAM_PATH = Path("data/raw/forge/team_week_context.upstream_public_2024_w01_w03_2team_scaffold.json")

PLAYER_FIELDS = (
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "air_yards",
    "fantasy_points_ppr",
)
TEAM_FIELDS = (
    "team_pass_attempts",
    "team_rush_attempts",
    "team_points",
    "team_air_yards",
)


def _load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["records"]


def _player_filter(
    records: list[dict[str, Any]],
    *,
    player_id: str | None,
    player_name: str | None,
) -> list[dict[str, Any]]:
    filtered = [
        record
        for record in records
        if int(record.get("season", 0)) == SUPPORTED_SEASON and int(record.get("week", 0)) in SUPPORTED_WEEKS
    ]
    if player_id:
        filtered = [record for record in filtered if str(record.get("player_id", "")) == player_id]
    if player_name:
        normalized = player_name.strip().lower()
        filtered = [record for record in filtered if str(record.get("full_name", "")).strip().lower() == normalized]
    return sorted(filtered, key=lambda row: (int(row["week"]), str(row["player_id"])))


def _team_filter(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [
            record
            for record in records
            if int(record.get("season", 0)) == SUPPORTED_SEASON and int(record.get("week", 0)) in SUPPORTED_WEEKS
        ],
        key=lambda row: (int(row["week"]), str(row["team"])),
    )


def _print_field_block(label: str, legacy: dict[str, Any] | None, upstream: dict[str, Any] | None, fields: tuple[str, ...]) -> None:
    print(label)
    for field in fields:
        legacy_value = "-" if legacy is None else legacy.get(field, "-")
        upstream_value = "-" if upstream is None else upstream.get(field, "-")
        print(f"  {field:20} legacy={str(legacy_value):>8} | upstream={str(upstream_value):>8}")


def _compare_players(
    legacy_records: list[dict[str, Any]],
    upstream_records: list[dict[str, Any]],
    *,
    player_id: str | None,
    player_name: str | None,
) -> None:
    filtered_legacy = _player_filter(legacy_records, player_id=player_id, player_name=player_name)
    filtered_upstream = _player_filter(upstream_records, player_id=player_id, player_name=player_name)

    legacy_by_key = {(int(row["week"]), str(row["player_id"])): row for row in filtered_legacy}
    upstream_by_key = {(int(row["week"]), str(row["player_id"])): row for row in filtered_upstream}

    print("\n=== Player lane comparison (legacy offline fixture vs upstream scaffold) ===")
    if player_id or player_name:
        print(f"Focus filter: player_id={player_id or '-'} player_name={player_name or '-'}")

    keys = sorted(set(legacy_by_key) | set(upstream_by_key))
    if not keys:
        print("No player rows matched filters in supported 2024 W1-W3 slice.")
        return

    for week, resolved_player_id in keys:
        legacy = legacy_by_key.get((week, resolved_player_id))
        upstream = upstream_by_key.get((week, resolved_player_id))
        player_name_value = (
            str((legacy or upstream or {}).get("full_name", "unknown"))
            if (legacy or upstream)
            else "unknown"
        )
        print(f"\nW{week} | {player_name_value} ({resolved_player_id})")
        _print_field_block("player_metrics", legacy, upstream, PLAYER_FIELDS)


def _compare_teams(legacy_records: list[dict[str, Any]], upstream_records: list[dict[str, Any]]) -> None:
    filtered_legacy = _team_filter(legacy_records)
    filtered_upstream = _team_filter(upstream_records)

    legacy_by_key = {(int(row["week"]), str(row["team"])): row for row in filtered_legacy}
    upstream_by_key = {(int(row["week"]), str(row["team"])): row for row in filtered_upstream}

    print("\n=== Team context comparison (legacy offline fixture vs upstream scaffold) ===")
    keys = sorted(set(legacy_by_key) | set(upstream_by_key))
    if not keys:
        print("No team rows found in supported 2024 W1-W3 slice.")
        return

    for week, team in keys:
        legacy = legacy_by_key.get((week, team))
        upstream = upstream_by_key.get((week, team))
        print(f"\nW{week} | {team}")
        _print_field_block("team_metrics", legacy, upstream, TEAM_FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare legacy offline fixture weekly support rows vs upstream-backed scaffold rows."
    )
    parser.add_argument("--player-name", default=None, help="Exact player full name focus (e.g. Amon-Ra St. Brown).")
    parser.add_argument("--player-id", default=None, help="Player id focus (e.g. 00-0037834).")
    parser.add_argument("--legacy-player-path", type=Path, default=LEGACY_PLAYER_PATH)
    parser.add_argument("--legacy-team-path", type=Path, default=LEGACY_TEAM_PATH)
    parser.add_argument("--upstream-player-path", type=Path, default=UPSTREAM_PLAYER_PATH)
    parser.add_argument("--upstream-team-path", type=Path, default=UPSTREAM_TEAM_PATH)
    args = parser.parse_args()

    legacy_player_records = _load_records(args.legacy_player_path)
    legacy_team_records = _load_records(args.legacy_team_path)
    upstream_player_records = _load_records(args.upstream_player_path)
    upstream_team_records = _load_records(args.upstream_team_path)

    print(f"Supported slice: season={SUPPORTED_SEASON}, weeks={list(SUPPORTED_WEEKS)}")
    _compare_players(
        legacy_player_records,
        upstream_player_records,
        player_id=args.player_id,
        player_name=args.player_name,
    )
    _compare_teams(legacy_team_records, upstream_team_records)


if __name__ == "__main__":
    main()
