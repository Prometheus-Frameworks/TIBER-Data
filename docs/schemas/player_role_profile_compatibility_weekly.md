# player_role_profile_compatibility_weekly

Explicit gold compatibility view for downstream role-and-opportunity consumers. This table preserves the raw/silver/gold layering by publishing a separate client-facing shape instead of renaming the core `player_role_inputs_weekly` contract.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Canonical player identifier. | Carried from `player_role_inputs_weekly`. |
| player_name | string | required_now | yes | Player display name expected by the upstream client. | Renamed from `full_name`. |
| position | string | required_now | yes | Position code. | Carried from `player_role_inputs_weekly`. |
| team | string | required_now | yes | Team abbreviation for filtering and joins. | Carried from `player_role_inputs_weekly`. |
| season | int | required_now | yes | NFL season. | Carried from `player_role_inputs_weekly`. |
| week | int | required_now | yes | NFL week number. | Carried from `player_role_inputs_weekly`. |
| target_share | float | required_now | yes | Share of team targets. | Carried from `player_role_inputs_weekly`. |
| air_yard_share | float | derived_now_if_available | no | Share of team air yards. | Renamed from `air_yards_share`. |
| route_participation | float | future_optional | no | Participation proxy based on route share when routes exist. | Renamed from `route_share`; null when routes are unavailable. |
| slot_rate | float | null_when_unavailable | no | Slot alignment rate. | Explicit null; tracking/alignment source not in current public path. |
| inline_rate | float | null_when_unavailable | no | Inline alignment rate. | Explicit null; tracking/alignment source not in current public path. |
| wide_rate | float | null_when_unavailable | no | Wide alignment rate. | Explicit null; tracking/alignment source not in current public path. |
| red_zone_target_share | float | derived_now_if_available | no | Share of team red-zone targets in the same week. | Player red-zone targets divided by summed team red-zone targets when available; null otherwise. |
| first_read_share | float | null_when_unavailable | no | First-read target share. | Explicit null; not derivable from the current public box-score path. |
| average_depth_of_target | float | derived_now_if_available | no | Average target depth. | Player air yards divided by targets when both exist and targets are positive. |
| explosive_target_rate | float | null_when_unavailable | no | Rate of explosive targets/receptions. | Explicit null; public source does not expose tracking-grade explosive-target labeling. |
| personnel_versatility | float | null_when_unavailable | no | Cross-personnel role versatility score. | Explicit null; would require richer formation/alignment participation data. |
| competition_for_role | float | derived_now_if_available | no | Same-position competition proxy within the same team-week. | Same-team, same-position target-share total minus the player's own target share. |
| injury_risk | float | null_when_unavailable | no | Injury-risk feature for compatibility consumers. | Explicit null; no injury model or public medical probability source is included here. |
| vacated_targets_available | float | derived_now_if_available | no | Prior-season targets available to current roster players. | Team `vacated_target_share` carried onto each current team-season row when adjacent seasons are present; null otherwise. |
