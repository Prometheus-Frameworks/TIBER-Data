# weekly_player_stats

Canonical silver table for player-week production from the initial public ingest path.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Canonical player identifier. | Source normalization. |
| full_name | string | required_now | yes | Player full name. | Source normalization. |
| position | string | required_now | yes | Position code. | Source normalization. |
| team | string | required_now | yes | Team abbreviation for the player-week. | Source normalization. |
| season | int | required_now | yes | NFL season. | Source normalization. |
| week | int | required_now | yes | NFL week number. | Source normalization. |
| targets | float | required_now | yes | Player passing targets. | Direct source field or normalized alias. |
| receptions | float | required_now | yes | Receptions. | Direct source field or normalized alias. |
| receiving_yards | float | required_now | yes | Receiving yards. | Direct source field or normalized alias. |
| receiving_tds | float | required_now | yes | Receiving touchdowns. | Direct source field or normalized alias. |
| rushing_attempts | float | required_now | yes | Rushing attempts. | Direct source field or normalized alias. |
| rushing_yards | float | required_now | yes | Rushing yards. | Direct source field or normalized alias. |
| rushing_tds | float | required_now | yes | Rushing touchdowns. | Direct source field or normalized alias. |
| pass_attempts | float | derived_now_if_available | no | Player pass attempts for team aggregation. | Direct source passthrough if available. |
| completions | float | derived_now_if_available | no | Player completions. | Direct source passthrough if available. |
| passing_yards | float | derived_now_if_available | no | Player passing yards. | Direct source passthrough if available. |
| passing_tds | float | derived_now_if_available | no | Player passing touchdowns. | Direct source passthrough if available. |
| fantasy_points_ppr | float | derived_now_if_available | no | PPR fantasy points. | Source passthrough or deterministic calculation. |
| air_yards | float | derived_now_if_available | no | Receiving air yards. | Source passthrough when available; otherwise null. |
| red_zone_targets | float | derived_now_if_available | no | Red zone targets. | Source passthrough or later derivation; null when unavailable. |
| routes_run | float | future_optional | no | Routes run. | Future public participation/tracking-compatible source. |
| snap_share | float | future_optional | no | Offensive snap share. | Future public participation/tracking-compatible source. |
