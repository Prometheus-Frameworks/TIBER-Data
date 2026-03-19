# weekly_team_stats

Canonical silver table for team-week context aggregated from player-week or team-level source data.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team | string | required_now | yes | Canonical team abbreviation. | Aggregated from weekly player stats or team source. |
| season | int | required_now | yes | NFL season. | Source normalization. |
| week | int | required_now | yes | NFL week number. | Source normalization. |
| team_pass_attempts | float | required_now | yes | Team pass attempts. | Aggregated from passing stats or team-level source. |
| team_rush_attempts | float | required_now | yes | Team rush attempts. | Aggregated from player rushing attempts. |
| team_receiving_yards | float | required_now | yes | Team receiving yards. | Aggregated from player receiving yards. |
| team_rushing_yards | float | required_now | yes | Team rushing yards. | Aggregated from player rushing yards. |
| team_points | float | required_now | yes | Team points scored. | Team-level source or public scoreboard field when available. |
| team_air_yards | float | derived_now_if_available | no | Team air yards. | Aggregated from player air yards when available. |
| team_targets | float | derived_now_if_available | no | Total targets credited to team skill players. | Aggregated from player targets. |
| team_epa_dropback | float | future_optional | no | Team or QB EPA per dropback. | Future play-by-play derivation. |
