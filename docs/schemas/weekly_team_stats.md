# weekly_team_stats

Canonical silver table for team-week context built from real player-week and real team-week public inputs. The current contract is regular-season only.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team | string | required_now | yes | Canonical team abbreviation. | Real source normalization. |
| season | int | required_now | yes | NFL season. | Real source normalization. |
| week | int | required_now | yes | NFL week number. | Real source normalization. |
| team_pass_attempts | float | required_now | yes | Team pass attempts. | Real weekly team stats source. |
| team_rush_attempts | float | required_now | yes | Team rush attempts. | Real weekly team stats source. |
| team_receiving_yards | float | required_now | yes | Team receiving yards. | Deterministic aggregation from real player-week stats. |
| team_rushing_yards | float | required_now | yes | Team rushing yards. | Deterministic aggregation from real player-week stats. |
| team_points | float | required_now | yes | Team points scored. | Real weekly team stats source. |
| team_air_yards | float | derived_now_if_available | no | Team air yards. | Real team-week source when available; otherwise deterministic aggregation from player air yards. |
| team_targets | float | derived_now_if_available | no | Total targets credited to team skill players. | Deterministic aggregation from real player-week stats. |
| team_epa_dropback | float | future_optional | no | Team or QB EPA per dropback. | Pending future play-by-play derivation. |
