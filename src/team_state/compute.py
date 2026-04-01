from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.team_state.definitions import DEFINITIONS, REQUIRED_PBP_COLUMNS, TEAM_STATE_ARTIFACT_NAME
from src.utils.frames import require_polars


def _safe_rate(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _base_offense_plays(pbp: Any) -> Any:
    pl = require_polars()
    play_type = pl.col("play_type").fill_null("") if "play_type" in pbp.columns else pl.lit("")
    return pbp.filter(pl.col("posteam").is_not_null()).with_columns(
        (
            (pl.col("pass") == 1)
            | (pl.col("rush") == 1)
            | play_type.is_in(["pass", "run"])
        )
        .alias("is_offense_play")
    ).filter(pl.col("is_offense_play"))


def build_team_state_artifact(
    pbp: Any,
    season: int,
    through_week: int | None = None,
) -> dict[str, Any]:
    pl = require_polars()

    missing = [column for column in REQUIRED_PBP_COLUMNS if column not in pbp.columns]
    if missing:
        raise ValueError(f"PBP input missing required columns: {missing}")

    plays = _base_offense_plays(pbp)
    if plays.height == 0:
        return {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "artifact": TEAM_STATE_ARTIFACT_NAME,
            "source": {
                "provider": "nflverse-pbp",
                "season": season,
                "throughWeek": through_week,
                "seasonType": "REG",
                "gamesIncluded": 0,
                "notes": ["No qualifying offensive plays found for selected filters."],
            },
            "definitions": DEFINITIONS,
            "teams": [],
        }

    plays = plays.with_columns((pl.col("down").is_in([1, 2])).alias("is_early_down"))
    plays = plays.with_columns(
        [
            (
                pl.col("down").is_in([1, 2, 3, 4])
                & pl.col("qtr").is_in([1, 2, 3])
                & (pl.col("score_differential").abs() <= 8)
            ).alias("is_neutral"),
            (
                pl.col("is_early_down")
                & ~((pl.col("qtr") == 4) & (pl.col("score_differential").abs() > 16))
            ).alias("is_early_down_non_garbage"),
            (pl.col("yardline_100") <= 20).fill_null(False).alias("is_red_zone_play"),
            (pl.col("yards_gained") >= 16).fill_null(False).alias("is_explosive"),
            (
                ((pl.col("down") == 1) & (pl.col("yards_gained") >= pl.col("ydstogo") * 0.4))
                | ((pl.col("down") == 2) & (pl.col("yards_gained") >= pl.col("ydstogo") * 0.6))
                | ((pl.col("down").is_in([3, 4])) & (pl.col("yards_gained") >= pl.col("ydstogo")))
            )
            .fill_null(False)
            .alias("is_success"),
        ]
    )

    team_groups = plays.group_by("posteam")
    sample = team_groups.agg(
        [
            pl.col("game_id").n_unique().alias("games"),
            pl.len().alias("plays"),
            pl.col("is_neutral").sum().alias("neutralPlays"),
            pl.col("is_early_down_non_garbage").sum().alias("earlyDownPlays"),
            pl.col("is_red_zone_play").sum().alias("redZonePlays"),
            pl.col("drive").n_unique().alias("drives"),
        ]
    )

    by_drive = plays.group_by(["posteam", "game_id", "drive"]).agg(
        [
            pl.col("first_down").fill_null(0).max().alias("had_first_down"),
            pl.col("is_red_zone_play").max().alias("reached_red_zone"),
            (
                (pl.col("is_red_zone_play"))
                & (pl.col("touchdown").fill_null(0) == 1)
            )
            .max()
            .alias("red_zone_td_scored"),
        ]
    )

    drive_stats = by_drive.group_by("posteam").agg(
        [
            pl.col("had_first_down").sum().alias("sustained_drives"),
            pl.col("reached_red_zone").sum().alias("red_zone_drives"),
            pl.col("red_zone_td_scored").sum().alias("red_zone_td_drives"),
        ]
    )

    metrics = team_groups.agg(
        [
            ((pl.col("is_neutral") & (pl.col("pass") == 1)).sum()).alias("neutral_pass_plays"),
            ((pl.col("is_early_down_non_garbage") & (pl.col("pass") == 1)).sum()).alias(
                "early_down_pass_plays"
            ),
            ((pl.col("is_early_down_non_garbage") & pl.col("is_success")).sum()).alias(
                "early_down_success_plays"
            ),
            ((pl.col("is_red_zone_play") & (pl.col("pass") == 1)).sum()).alias(
                "red_zone_pass_plays"
            ),
            pl.col("is_explosive").sum().alias("explosive_plays"),
        ]
    )

    pace_available = {"game_seconds_remaining", "play_id"}.issubset(set(plays.columns))
    pace = None
    pace_note = None
    if pace_available:
        pace = (
            plays.sort(["posteam", "game_id", "play_id"])
            .with_columns(
                (
                    pl.col("game_seconds_remaining")
                    - pl.col("game_seconds_remaining").shift(-1).over(["posteam", "game_id"])
                ).alias("play_delta_seconds")
            )
            .filter((pl.col("play_delta_seconds") > 0) & (pl.col("play_delta_seconds") <= 45))
            .group_by("posteam")
            .agg(pl.col("play_delta_seconds").median().round(2).alias("paceSecondsPerPlay"))
        )
    else:
        pace_note = (
            "paceSecondsPerPlay omitted because game_seconds_remaining or play_id "
            "was missing."
        )

    combined = sample.join(metrics, on="posteam", how="left").join(
        drive_stats,
        on="posteam",
        how="left",
    )
    if pace is not None:
        combined = combined.join(pace, on="posteam", how="left")

    teams = []
    for row in combined.sort("posteam").to_dicts():
        plays_count = float(row.get("plays") or 0)
        sample_flag = "ok"
        stability_notes: list[str] = []
        if plays_count < 250:
            sample_flag = "thin"
            stability_notes.append("Fewer than 250 offensive plays in sample.")

        if pace_note:
            stability_notes.append(pace_note)

        team_payload = {
            "team": row["posteam"],
            "sample": {
                "games": int(row.get("games") or 0),
                "plays": int(row.get("plays") or 0),
                "neutralPlays": int(row.get("neutralPlays") or 0),
                "earlyDownPlays": int(row.get("earlyDownPlays") or 0),
                "redZonePlays": int(row.get("redZonePlays") or 0),
                "drives": int(row.get("drives") or 0),
            },
            "features": {
                "neutralPassRate": _safe_rate(
                    float(row.get("neutral_pass_plays") or 0),
                    float(row.get("neutralPlays") or 0),
                ),
                "earlyDownPassRate": _safe_rate(
                    float(row.get("early_down_pass_plays") or 0),
                    float(row.get("earlyDownPlays") or 0),
                ),
                "earlyDownSuccessRate": _safe_rate(
                    float(row.get("early_down_success_plays") or 0),
                    float(row.get("earlyDownPlays") or 0),
                ),
                "redZonePassRate": _safe_rate(
                    float(row.get("red_zone_pass_plays") or 0),
                    float(row.get("redZonePlays") or 0),
                ),
                "redZoneTdEfficiency": _safe_rate(
                    float(row.get("red_zone_td_drives") or 0),
                    float(row.get("red_zone_drives") or 0),
                ),
                "explosivePlayRate": _safe_rate(
                    float(row.get("explosive_plays") or 0),
                    float(row.get("plays") or 0),
                ),
                "driveSustainRate": _safe_rate(
                    float(row.get("sustained_drives") or 0),
                    float(row.get("drives") or 0),
                ),
                "paceSecondsPerPlay": row.get("paceSecondsPerPlay"),
            },
            "stability": {
                "sampleFlag": sample_flag,
                "confidenceBand": "medium" if sample_flag == "ok" else "low",
                "notes": stability_notes,
            },
        }
        teams.append(team_payload)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "artifact": TEAM_STATE_ARTIFACT_NAME,
        "source": {
            "provider": "nflverse-pbp",
            "season": season,
            "throughWeek": through_week,
            "seasonType": "REG",
            "gamesIncluded": plays.select(pl.col("game_id").n_unique()).item(),
            "notes": [],
        },
        "definitions": DEFINITIONS,
        "teams": teams,
    }
