# team_context_weekly

Gold table for team-week environment and opportunity context.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team | string | required_now | yes | Canonical team abbreviation. | Carried from silver team-week table. |
| season | int | required_now | yes | NFL season. | Carried from silver team-week table. |
| week | int | required_now | yes | NFL week number. | Carried from silver team-week table. |
| team_pass_attempts | float | required_now | yes | Team pass attempts. | Carried from silver team-week table. |
| team_rush_attempts | float | required_now | yes | Team rush attempts. | Carried from silver team-week table. |
| neutral_pass_rate | float | future_optional | no | Pass rate in neutral game states. | Future play-by-play derivation. |
| red_zone_pass_rate | float | future_optional | no | Pass rate inside the red zone. | Future play-by-play derivation. |
| pace_proxy | float | derived_now_if_available | no | First-pass pace proxy based on offensive plays. | Derived from team pass and rush attempts. |
| team_air_yards | float | derived_now_if_available | no | Team air yards. | Carried from silver team-week table when available. |
| qb_epa_per_dropback | float | future_optional | no | QB/team EPA per dropback. | Future play-by-play derivation. |
| target_competition_index | float | derived_now_if_available | no | Effective number of target earners via inverse target-share concentration. | Derived from player target shares by team-week. |
| receiver_room_certainty | float | future_optional | no | Placeholder certainty score for receiver room continuity. | Reserved for future roster/usage logic. |
