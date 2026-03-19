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
    if not columns:
        return frame
    for column in columns:
        if column not in frame.columns:
            frame = frame.with_columns(pl.lit(None).alias(column))
    return frame.select(columns)


def _coalesce(frame, aliases: dict[str, list[str]]):
    pl = require_polars()
    expressions = []
    for destination, candidates in aliases.items():
        available = [pl.col(candidate) for candidate in candidates if candidate in frame.columns]
        if not available:
            expressions.append(pl.lit(None).alias(destination))
            continue
        expressions.append(pl.coalesce(available).alias(destination))
    return frame.with_columns(expressions)


def build_players(records: list[dict[str, Any]]):
    pl = require_polars()
    frame = pl.DataFrame(records)
    frame = _coalesce(
        frame,
        {
            "player_id": ["player_id", "gsis_id"],
            "full_name": ["full_name", "player_name", "player_display_name", "display_name"],
            "position": ["position", "pos"],
            "team": ["team", "recent_team", "current_team", "team_abbr"],
            "season": ["season"],
            "college": ["college", "college_name"],
            "draft_team": ["draft_team", "draft_club"],
            "draft_round": ["draft_round"],
            "birth_date": ["birth_date"],
        },
    )
    season_year = pl.col("season").cast(pl.Int64, strict=False)
    birth_year = pl.col("birth_date").cast(pl.Utf8).str.slice(0, 4).cast(pl.Int64, strict=False)
    age_expr = (
        pl.when(pl.col("birth_date").is_not_null() & pl.col("season").is_not_null())
        .then(season_year - birth_year)
        .otherwise(None)
        .alias("age")
    )
    selected = _frame(frame.to_dicts(), PLAYER_COLUMNS + ["birth_date"])
    return (
        selected.with_columns(
            pl.col("player_id").cast(pl.Utf8),
            pl.col("full_name").cast(pl.Utf8),
            pl.col("position").cast(pl.Utf8),
            pl.col("team").cast(pl.Utf8),
            pl.col("season").cast(pl.Int64, strict=False),
            pl.col("college").cast(pl.Utf8),
            pl.col("draft_team").cast(pl.Utf8),
            pl.col("draft_round").cast(pl.Int64, strict=False),
            age_expr,
        )
        .select(PLAYER_COLUMNS)
        .filter(pl.col("player_id").is_not_null() & pl.col("season").is_not_null())
        .unique(subset=["player_id", "season"], keep="last")
        .sort(["season", "team", "full_name"])
    )


def build_teams(records: list[dict[str, Any]]):
    pl = require_polars()
    frame = _coalesce(
        pl.DataFrame(records),
        {
            "team": ["team", "team_abbr", "team_code", "abbr"],
            "team_name": ["team_name", "team_nick", "team_wordmark", "team_full_name"],
            "conference": ["conference", "team_conf"],
            "division": ["division", "team_division"],
        },
    )
    return (
        _frame(frame.to_dicts(), TEAM_COLUMNS)
        .with_columns(
            pl.col("team").cast(pl.Utf8),
            pl.col("team_name").cast(pl.Utf8),
            pl.col("conference").cast(pl.Utf8),
            pl.col("division").cast(pl.Utf8),
        )
        .filter(pl.col("team").is_not_null())
        .unique(subset=["team"], keep="last")
        .sort("team")
    )


def build_weekly_player_stats(records: list[dict[str, Any]]):
    pl = require_polars()
    raw_frame = pl.DataFrame(records)
    if "season_type" in raw_frame.columns:
        raw_frame = raw_frame.filter(
            pl.col("season_type").cast(pl.Utf8).str.to_lowercase().is_in(["reg", "regular"])
        )
    frame = _coalesce(
        raw_frame,
        {
            "player_id": ["player_id", "gsis_id"],
            "full_name": ["full_name", "player_display_name", "player_name", "display_name"],
            "position": ["position", "position_group"],
            "team": ["team", "recent_team", "team_abbr"],
            "season": ["season"],
            "week": ["week"],
            "targets": ["targets"],
            "receptions": ["receptions"],
            "receiving_yards": ["receiving_yards"],
            "receiving_tds": ["receiving_tds"],
            "rushing_attempts": ["rushing_attempts", "carries"],
            "rushing_yards": ["rushing_yards"],
            "rushing_tds": ["rushing_tds"],
            "pass_attempts": ["pass_attempts", "attempts"],
            "completions": ["completions"],
            "passing_yards": ["passing_yards"],
            "passing_tds": ["passing_tds"],
            "fantasy_points_ppr": ["fantasy_points_ppr"],
            "air_yards": ["air_yards", "receiving_air_yards"],
            "red_zone_targets": ["red_zone_targets", "receiving_redzone_targets"],
        },
    )
    core_numeric_columns = [
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
    ]
    optional_numeric_columns = ["fantasy_points_ppr", "air_yards", "red_zone_targets"]
    frame = _frame(frame.to_dicts(), WEEKLY_PLAYER_COLUMNS)
    fantasy_formula = (
        pl.col("receptions")
        + pl.col("receiving_yards") / 10.0
        + pl.col("receiving_tds") * 6.0
        + pl.col("rushing_yards") / 10.0
        + pl.col("rushing_tds") * 6.0
        + pl.col("passing_yards") / 25.0
        + pl.col("passing_tds") * 4.0
    )
    expressions = [
        pl.col("player_id").cast(pl.Utf8),
        pl.col("full_name").cast(pl.Utf8),
        pl.col("position").cast(pl.Utf8),
        pl.col("team").cast(pl.Utf8),
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("week").cast(pl.Int64, strict=False),
    ]
    expressions.extend(
        pl.col(column).cast(pl.Float64, strict=False).fill_null(0.0) for column in core_numeric_columns
    )
    expressions.extend(
        pl.col(column).cast(pl.Float64, strict=False) for column in optional_numeric_columns
    )
    return (
        frame.with_columns(expressions)
        .with_columns(pl.col("fantasy_points_ppr").fill_null(fantasy_formula))
        .filter(
            pl.col("player_id").is_not_null()
            & pl.col("season").is_not_null()
            & pl.col("week").is_not_null()
        )
        .sort(["season", "week", "team", "full_name"])
    )


def build_weekly_team_stats(player_weekly, team_week_records: list[dict[str, Any]]):
    pl = require_polars()
    raw_team_context = pl.DataFrame(team_week_records)
    if "season_type" in raw_team_context.columns:
        raw_team_context = raw_team_context.filter(
            pl.col("season_type").cast(pl.Utf8).str.to_lowercase().is_in(["reg", "regular"])
        )
    team_context = _coalesce(
        raw_team_context,
        {
            "team": ["team", "recent_team", "team_abbr"],
            "season": ["season"],
            "week": ["week"],
            "team_pass_attempts": ["team_pass_attempts", "attempts", "pass_attempts"],
            "team_rush_attempts": ["team_rush_attempts", "carries", "rush_attempts"],
            "team_points": ["team_points", "points", "total_points"],
            "team_air_yards": ["team_air_yards", "passing_air_yards", "air_yards"],
        },
    )
    team_context = team_context.select(
        [
            pl.col("team").cast(pl.Utf8),
            pl.col("season").cast(pl.Int64, strict=False),
            pl.col("week").cast(pl.Int64, strict=False),
            pl.col("team_pass_attempts").cast(pl.Float64, strict=False),
            pl.col("team_rush_attempts").cast(pl.Float64, strict=False),
            pl.col("team_points").cast(pl.Float64, strict=False),
            pl.col("team_air_yards").cast(pl.Float64, strict=False),
        ]
    )
    aggregated = player_weekly.group_by(["team", "season", "week"]).agg(
        pl.col("receiving_yards").sum().alias("team_receiving_yards"),
        pl.col("rushing_yards").sum().alias("team_rushing_yards"),
        pl.col("targets").sum().alias("team_targets"),
        pl.when(pl.col("air_yards").is_not_null().sum() > 0)
        .then(pl.col("air_yards").sum())
        .otherwise(None)
        .alias("player_air_yards_total"),
    )
    return (
        aggregated.join(team_context, on=["team", "season", "week"], how="left")
        .with_columns(
            pl.col("team_pass_attempts").fill_null(0.0),
            pl.col("team_rush_attempts").fill_null(0.0),
            pl.col("team_points").fill_null(0.0),
            pl.coalesce([pl.col("team_air_yards"), pl.col("player_air_yards_total")]).alias(
                "team_air_yards"
            ),
        )
        .drop("player_air_yards_total")
        .sort(["season", "week", "team"])
    )
