from __future__ import annotations

import argparse
from pathlib import Path

from src.config.settings import build_config
from src.derive.gold import build_player_role_inputs_weekly, build_team_context_weekly
from src.ingest.public import PublicDataClient
from src.transform.silver import (
    build_players,
    build_teams,
    build_weekly_player_stats,
    build_weekly_team_stats,
)
from src.utils.io import ensure_directories, should_write
from src.utils.validation import ValidationRule, validate_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TIBER-Data bootstrap pipeline.")
    parser.add_argument("--season", type=int, help="Single season to ingest.")
    parser.add_argument("--seasons", type=int, nargs="+", help="One or more seasons to ingest.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output files.")
    parser.add_argument(
        "--disable-offline-fallback",
        action="store_true",
        help="Fail instead of using local fixtures when public sources are unavailable.",
    )
    return parser.parse_args()


def write_parquet(frame, path: Path, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if should_write(path, overwrite):
        frame.write_parquet(path)


def validation_rules() -> list[ValidationRule]:
    return [
        ValidationRule(
            "players",
            ["player_id", "full_name", "position", "team", "season"],
            ["player_id", "season"],
            [],
        ),
        ValidationRule(
            "weekly_player_stats",
            ["player_id", "season", "week", "team", "targets"],
            ["player_id", "season", "week"],
            [
                "targets",
                "receptions",
                "receiving_yards",
                "receiving_tds",
                "rushing_attempts",
                "rushing_yards",
                "rushing_tds",
                "pass_attempts",
                "passing_yards",
                "passing_tds",
            ],
        ),
        ValidationRule(
            "weekly_team_stats",
            [
                "team",
                "season",
                "week",
                "team_pass_attempts",
                "team_rush_attempts",
                "team_points",
            ],
            ["team", "season", "week"],
            [
                "team_pass_attempts",
                "team_rush_attempts",
                "team_receiving_yards",
                "team_rushing_yards",
                "team_points",
            ],
        ),
        ValidationRule(
            "player_role_inputs_weekly",
            ["player_id", "team", "season", "week", "target_share"],
            ["player_id", "season", "week"],
            [
                "targets",
                "receptions",
                "receiving_yards",
                "receiving_tds",
                "target_share",
            ],
        ),
        ValidationRule(
            "team_context_weekly",
            ["team", "season", "week", "team_pass_attempts", "team_rush_attempts"],
            ["team", "season", "week"],
            ["team_pass_attempts", "team_rush_attempts", "pace_proxy"],
        ),
    ]


def main() -> int:
    args = parse_args()
    seasons = args.seasons or ([args.season] if args.season else None)
    config = build_config(
        seasons=seasons,
        overwrite=args.overwrite,
        allow_offline_fallback=not args.disable_offline_fallback,
    )
    ensure_directories([config.raw_dir, config.silver_dir, config.gold_dir])

    client = PublicDataClient(config)
    public_tables = client.ingest_all()
    client.write_raw_exports(public_tables)

    players = build_players(public_tables["players"].records)
    teams = build_teams(public_tables["teams"].records)
    weekly_player_stats = build_weekly_player_stats(public_tables["weekly_player_stats"].records)
    weekly_team_stats = build_weekly_team_stats(
        weekly_player_stats,
        public_tables["team_week_context"].records,
    )

    player_role_inputs_weekly = build_player_role_inputs_weekly(
        weekly_player_stats,
        weekly_team_stats,
    )
    team_context_weekly = build_team_context_weekly(
        weekly_team_stats,
        player_role_inputs_weekly,
    )

    rules = validation_rules()
    frames_to_validate = [
        (players, rules[0]),
        (weekly_player_stats, rules[1]),
        (weekly_team_stats, rules[2]),
        (player_role_inputs_weekly, rules[3]),
        (team_context_weekly, rules[4]),
    ]
    for frame, rule in frames_to_validate:
        validate_frame(frame, rule)

    write_parquet(players, config.silver_dir / "players.parquet", config.overwrite)
    write_parquet(teams, config.silver_dir / "teams.parquet", config.overwrite)
    write_parquet(
        weekly_player_stats,
        config.silver_dir / "weekly_player_stats.parquet",
        config.overwrite,
    )
    write_parquet(
        weekly_team_stats,
        config.silver_dir / "weekly_team_stats.parquet",
        config.overwrite,
    )
    write_parquet(
        player_role_inputs_weekly,
        config.gold_dir / "player_role_inputs_weekly.parquet",
        config.overwrite,
    )
    write_parquet(
        team_context_weekly,
        config.gold_dir / "team_context_weekly.parquet",
        config.overwrite,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
