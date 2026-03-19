# player_role_inputs_weekly

Gold table for first-pass role and opportunity modeling inputs. The current contract is regular-season only.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Canonical player identifier. | Carried from silver player-week table. |
| full_name | string | required_now | yes | Player full name. | Carried from silver player-week table. |
| position | string | required_now | yes | Position code. | Carried from silver player-week table. |
| team | string | required_now | yes | Team abbreviation. | Carried from silver player-week table. |
| season | int | required_now | yes | NFL season. | Carried from silver player-week table. |
| week | int | required_now | yes | NFL week number. | Carried from silver player-week table. |
| targets | float | required_now | yes | Weekly targets. | Carried from silver player-week table. |
| receptions | float | required_now | yes | Weekly receptions. | Carried from silver player-week table. |
| receiving_yards | float | required_now | yes | Weekly receiving yards. | Carried from silver player-week table. |
| receiving_tds | float | required_now | yes | Weekly receiving touchdowns. | Carried from silver player-week table. |
| target_share | float | required_now | yes | Player targets divided by team total targets. | Deterministically derived from silver team targets. |
| red_zone_targets | float | derived_now_if_available | no | Weekly red zone targets. | Carried when available from the public source; null otherwise. |
| air_yards | float | derived_now_if_available | no | Weekly air yards. | Carried when available from the public source. |
| air_yards_share | float | derived_now_if_available | no | Player air yards divided by team air yards. | Deterministically derived when team air yards are available. |
| routes_run | float | future_optional | no | Weekly routes run. | Pending future participation source. |
| route_share | float | future_optional | no | Player routes divided by team routes. | Pending future derivation when routes exist. |
| snap_share | float | future_optional | no | Offensive snap share. | Pending future participation source. |
| yprr | float | future_optional | no | Yards per route run. | Pending future derivation when routes exist. |
| tprr | float | future_optional | no | Targets per route run. | Pending future derivation when routes exist. |
