from __future__ import annotations

from typing import Any

from src.utils.frames import require_polars

PLAYER_COLUMNS = [
    "player_id",
    "full_name",
    "position",
    "team",
    "season",
    "age",
    "college",
    "draft_team",
    "draft_round",
]

WEEKLY_PLAYER_COLUMNS = [
    "player_id",
    "full_name",
    "position",
    "team",
    "season",
    "week",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "rushing_attempts",
    "rushing_yards",
    "rushing_tds",
    "pass_attempts",
    "completions",
    "passing_yards",
    "passing_tds",
    "fantasy_points_ppr",
    "air_yards",
    "red_zone_targets",
]

TEAM_COLUMNS = ["team", "team_name", "conference", "division"]


def _frame(records: list[dict[str, Any]], columns: list[str]):
    pl = require_polars()
    frame = pl.DataFrame(records)
    for column in columns:
        if column not in frame.columns:
            frame = frame.with_columns(pl.lit(None).alias(column))
    return frame.select(columns)


def build_players(records: list[dict[str, Any]]):
    pl = require_polars()
    return (
        _frame(records, PLAYER_COLUMNS)
        .with_columns(
            pl.col("player_id").cast(pl.Utf8),
            pl.col("full_name").cast(pl.Utf8),
            pl.col("position").cast(pl.Utf8),
            pl.col("team").cast(pl.Utf8),
            pl.col("season").cast(pl.Int64),
        )
        .unique(subset=["player_id", "season"], keep="last")
        .sort(["season", "team", "full_name"])
    )


def build_teams(records: list[dict[str, Any]]):
    pl = require_polars()
    return (
        _frame(records, TEAM_COLUMNS)
        .with_columns(pl.col("team").cast(pl.Utf8), pl.col("team_name").cast(pl.Utf8))
        .unique(subset=["team"], keep="last")
        .sort("team")
    )


def build_weekly_player_stats(records: list[dict[str, Any]]):
    pl = require_polars()
    numeric_columns = [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "rushing_attempts",
        "rushing_yards",
        "rushing_tds",
        "pass_attempts",
        "completions",
        "passing_yards",
        "passing_tds",
        "fantasy_points_ppr",
        "air_yards",
        "red_zone_targets",
    ]
    frame = _frame(records, WEEKLY_PLAYER_COLUMNS)
    expressions = [
        pl.col("player_id").cast(pl.Utf8),
        pl.col("full_name").cast(pl.Utf8),
        pl.col("position").cast(pl.Utf8),
        pl.col("team").cast(pl.Utf8),
        pl.col("season").cast(pl.Int64),
        pl.col("week").cast(pl.Int64),
    ]
    expressions.extend(pl.col(column).cast(pl.Float64).fill_null(0.0) for column in numeric_columns)
    return frame.with_columns(expressions).sort(["season", "week", "team", "full_name"])


def build_weekly_team_stats(player_weekly, team_week_records: list[dict[str, Any]]):
    pl = require_polars()
    team_context = pl.DataFrame(team_week_records)
    if "team_points" not in team_context.columns:
        team_context = team_context.with_columns(pl.lit(0.0).alias("team_points"))
    aggregated = player_weekly.group_by(["team", "season", "week"]).agg(
        pl.col("pass_attempts").sum().alias("team_pass_attempts"),
        pl.col("rushing_attempts").sum().alias("team_rush_attempts"),
        pl.col("receiving_yards").sum().alias("team_receiving_yards"),
        pl.col("rushing_yards").sum().alias("team_rushing_yards"),
        pl.col("targets").sum().alias("team_targets"),
        pl.col("air_yards").sum().alias("team_air_yards"),
    )
    return (
        aggregated.join(team_context, on=["team", "season", "week"], how="left")
        .with_columns(pl.col("team_points").cast(pl.Float64).fill_null(0.0))
        .sort(["season", "week", "team"])
    )
