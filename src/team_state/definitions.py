from __future__ import annotations

TEAM_STATE_ARTIFACT_NAME = "tiber_team_state_v0_1"

DEFINITIONS: dict[str, str] = {
    "neutralSituation": (
        "Offensive plays with down in {1,2,3,4}, quarter in {1,2,3}, and absolute score "
        "differential <= 8 at snap."
    ),
    "earlyDown": "Offensive plays on 1st or 2nd down.",
    "garbageTimeExclusion": (
        "Excluded only for early-down rates: 4th quarter plays with absolute score "
        "differential > 16."
    ),
    "successRate": (
        "Standard success rule: gain >=40% of yards-to-go on 1st down, >=60% on 2nd down, "
        "and 100% on 3rd/4th down."
    ),
    "explosivePlay": "Offensive play with yards_gained >= 16.",
    "driveSustainRate": "Share of offensive drives with at least one first down.",
    "redZone": "Offensive plays snapped at yardline_100 <= 20.",
    "redZoneTdEfficiency": (
        "Offensive touchdowns scored on drives that reached the red zone divided by total "
        "red-zone drives."
    ),
    "paceSecondsPerPlay": (
        "Median seconds between consecutive offensive snaps for a team in a game, excluding "
        "deltas <=0 or >45 seconds. Omitted if required timing fields are unavailable."
    ),
}

REQUIRED_PBP_COLUMNS = [
    "posteam",
    "season",
    "season_type",
    "week",
    "game_id",
    "drive",
    "down",
    "ydstogo",
    "yards_gained",
    "touchdown",
    "first_down",
    "score_differential",
]
