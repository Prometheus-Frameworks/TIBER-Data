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
            pl.when(pl.col("routes_run").sum().over(["team", "season", "week"]) > 0)
            .then(
                pl.col("routes_run")
                / pl.col("routes_run").sum().over(["team", "season", "week"])
            )
            .otherwise(None)
            .alias("route_share"),
            pl.col("snap_share").cast(pl.Float64),
            pl.when(pl.col("routes_run") > 0)
            .then(pl.col("receiving_yards") / pl.col("routes_run"))
            .otherwise(None)
            .alias("yprr"),
            pl.when(pl.col("routes_run") > 0)
            .then(pl.col("targets") / pl.col("routes_run"))
            .otherwise(None)
            .alias("tprr"),
        ]
    return (
        joined.with_columns(
            pl.when(pl.col("team_targets") > 0)
            .then(pl.col("targets") / pl.col("team_targets"))
            .otherwise(0.0)
            .alias("target_share"),
            pl.when(pl.col("team_air_yards") > 0)
            .then(pl.col("air_yards") / pl.col("team_air_yards"))
            .otherwise(None)
            .alias("air_yards_share"),
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
        pl.when(pl.col("target_share").pow(2).sum() > 0)
        .then(1 / pl.col("target_share").pow(2).sum())
        .otherwise(None)
        .alias("target_competition_index")
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


def build_player_role_profile_compatibility_weekly(player_role_weekly, players):
    pl = require_polars()
    team_red_zone = player_role_weekly.group_by(["team", "season", "week"]).agg(
        pl.when(pl.col("red_zone_targets").is_not_null().sum() > 0)
        .then(pl.col("red_zone_targets").fill_null(0.0).sum())
        .otherwise(None)
        .alias("team_red_zone_targets")
    )
    same_position_competition = player_role_weekly.group_by(
        ["team", "season", "week", "position"]
    ).agg(pl.col("target_share").sum().alias("position_target_share_total"))
    vacated_targets = _build_team_vacated_target_share(player_role_weekly, players).select(
        ["team", "season", "vacated_target_share"]
    )
    return (
        player_role_weekly.join(team_red_zone, on=["team", "season", "week"], how="left")
        .join(
            same_position_competition,
            on=["team", "season", "week", "position"],
            how="left",
        )
        .join(vacated_targets, on=["team", "season"], how="left")
        .with_columns(
            pl.col("player_id").alias("player_id"),
            pl.col("full_name").alias("player_name"),
            pl.col("air_yards_share").alias("air_yard_share"),
            pl.col("route_share").alias("route_participation"),
            pl.lit(None).cast(pl.Float64).alias("slot_rate"),
            pl.lit(None).cast(pl.Float64).alias("inline_rate"),
            pl.lit(None).cast(pl.Float64).alias("wide_rate"),
            pl.when(pl.col("team_red_zone_targets") > 0)
            .then(pl.col("red_zone_targets").fill_null(0.0) / pl.col("team_red_zone_targets"))
            .otherwise(None)
            .alias("red_zone_target_share"),
            pl.lit(None).cast(pl.Float64).alias("first_read_share"),
            pl.when(pl.col("targets") > 0)
            .then(pl.col("air_yards") / pl.col("targets"))
            .otherwise(None)
            .alias("average_depth_of_target"),
            pl.lit(None).cast(pl.Float64).alias("explosive_target_rate"),
            pl.lit(None).cast(pl.Float64).alias("personnel_versatility"),
            (pl.col("position_target_share_total") - pl.col("target_share"))
            .clip(lower_bound=0.0)
            .alias("competition_for_role"),
            pl.lit(None).cast(pl.Float64).alias("injury_risk"),
            pl.col("vacated_target_share").alias("vacated_targets_available"),
        )
        .select(
            [
                "player_id",
                "player_name",
                "position",
                "team",
                "season",
                "week",
                "target_share",
                "air_yard_share",
                "route_participation",
                "slot_rate",
                "inline_rate",
                "wide_rate",
                "red_zone_target_share",
                "first_read_share",
                "average_depth_of_target",
                "explosive_target_rate",
                "personnel_versatility",
                "competition_for_role",
                "injury_risk",
                "vacated_targets_available",
            ]
        )
        .sort(["season", "week", "team", "player_name"])
    )


def build_team_opportunity_context_compatibility_weekly(
    team_context_weekly,
    teams,
    player_role_weekly,
    players,
):
    pl = require_polars()
    vacated_targets = _build_team_vacated_target_share(player_role_weekly, players)
    league_pace = team_context_weekly.group_by(["season", "week"]).agg(
        pl.col("pace_proxy").mean().alias("league_average_pace_proxy")
    )
    return (
        team_context_weekly.join(teams, on="team", how="left")
        .join(league_pace, on=["season", "week"], how="left")
        .join(vacated_targets, on=["team", "season"], how="left")
        .with_columns(
            pl.col("team").alias("team_id"),
            pl.when(pl.col("league_average_pace_proxy") > 0)
            .then(pl.col("pace_proxy") / pl.col("league_average_pace_proxy"))
            .otherwise(None)
            .alias("pace_index"),
            pl.lit(None).cast(pl.Float64).alias("pass_rate_over_expected"),
            pl.lit(None).cast(pl.Float64).alias("quarterback_stability"),
            pl.lit(None).cast(pl.Float64).alias("play_caller_continuity"),
        )
        .select(
            [
                "team_id",
                "team_name",
                "team",
                "season",
                "week",
                "pass_rate_over_expected",
                "neutral_pass_rate",
                "red_zone_pass_rate",
                "pace_index",
                "quarterback_stability",
                "play_caller_continuity",
                "target_competition_index",
                "receiver_room_certainty",
                "vacated_target_share",
            ]
        )
        .sort(["season", "week", "team_id"])
    )


def _build_team_vacated_target_share(player_role_weekly, players):
    pl = require_polars()
    current_roster = (
        players.select(["team", "season", "player_id"])
        .unique(subset=["team", "season", "player_id"])
    )
    prior_season_targets = player_role_weekly.group_by(["team", "season", "player_id"]).agg(
        pl.col("targets").sum().alias("prior_season_player_targets")
    )
    shifted_prior_targets = prior_season_targets.with_columns(
        (pl.col("season") + 1).alias("season")
    )
    prior_team_totals = shifted_prior_targets.group_by(["team", "season"]).agg(
        pl.col("prior_season_player_targets").sum().alias("prior_season_team_targets")
    )
    departed_targets = shifted_prior_targets.join(
        current_roster,
        on=["team", "season", "player_id"],
        how="anti",
    )
    return (
        departed_targets.group_by(["team", "season"]).agg(
            pl.col("prior_season_player_targets").sum().alias("departed_targets")
        )
        .join(prior_team_totals, on=["team", "season"], how="outer")
        .with_columns(pl.col("departed_targets").fill_null(0.0))
        .group_by(["team", "season"])
        .agg(
            pl.when(pl.col("prior_season_team_targets").max() > 0)
            .then(
                pl.col("departed_targets").max()
                / pl.col("prior_season_team_targets").max()
            )
            .otherwise(None)
            .alias("vacated_target_share")
        )
    )
