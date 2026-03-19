from __future__ import annotations

from src.utils.frames import require_polars


def build_player_role_inputs_weekly(player_weekly, team_weekly):
    pl = require_polars()
    joined = player_weekly.join(
        team_weekly.select(["team", "season", "week", "team_targets", "team_air_yards"]),
        on=["team", "season", "week"],
        how="left",
    )
    routes_available = "routes_run" in joined.columns
    route_expr = [
        pl.lit(None).cast(pl.Float64).alias("routes_run"),
        pl.lit(None).cast(pl.Float64).alias("route_share"),
        pl.lit(None).cast(pl.Float64).alias("snap_share"),
        pl.lit(None).cast(pl.Float64).alias("yprr"),
        pl.lit(None).cast(pl.Float64).alias("tprr"),
    ]
    if routes_available:
        route_expr = [
            pl.col("routes_run").cast(pl.Float64),
            (pl.col("routes_run") / pl.col("routes_run").sum().over(["team", "season", "week"]))
            .fill_nan(None)
            .alias("route_share"),
            pl.col("snap_share").cast(pl.Float64),
            (pl.col("receiving_yards") / pl.col("routes_run")).fill_nan(None).alias("yprr"),
            (pl.col("targets") / pl.col("routes_run")).fill_nan(None).alias("tprr"),
        ]
    return (
        joined.with_columns(
            (pl.col("targets") / pl.col("team_targets")).fill_nan(0.0).alias("target_share"),
            (pl.col("air_yards") / pl.col("team_air_yards")).fill_nan(0.0).alias("air_yards_share"),
            *route_expr,
        )
        .select(
            [
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
                "target_share",
                "red_zone_targets",
                "air_yards",
                "air_yards_share",
                "routes_run",
                "route_share",
                "snap_share",
                "yprr",
                "tprr",
            ]
        )
        .sort(["season", "week", "team", "full_name"])
    )


def build_team_context_weekly(team_weekly, player_role_weekly):
    pl = require_polars()
    concentration = player_role_weekly.group_by(["team", "season", "week"]).agg(
        (1 / pl.col("target_share").pow(2).sum()).alias("target_competition_index")
    )
    return (
        team_weekly.join(concentration, on=["team", "season", "week"], how="left")
        .with_columns(
            (pl.col("team_pass_attempts") + pl.col("team_rush_attempts")).alias("pace_proxy"),
            pl.lit(None).cast(pl.Float64).alias("neutral_pass_rate"),
            pl.lit(None).cast(pl.Float64).alias("red_zone_pass_rate"),
            pl.lit(None).cast(pl.Float64).alias("qb_epa_per_dropback"),
            pl.lit(None).cast(pl.Float64).alias("receiver_room_certainty"),
        )
        .select(
            [
                "team",
                "season",
                "week",
                "team_pass_attempts",
                "team_rush_attempts",
                "neutral_pass_rate",
                "red_zone_pass_rate",
                "pace_proxy",
                "team_air_yards",
                "qb_epa_per_dropback",
                "target_competition_index",
                "receiver_room_certainty",
            ]
        )
        .sort(["season", "week", "team"])
    )
