# team_opportunity_context_compatibility_weekly

Explicit gold compatibility view for downstream opportunity-context consumers. This table exposes the field names expected by the upstream client while keeping the core `team_context_weekly` table unchanged.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team_id | string | required_now | yes | Canonical team identifier expected by the upstream client. | Renamed from `team`. |
| team_name | string | required_now | yes | Human-readable team name. | Joined from the silver `teams` table. |
| team | string | required_now | yes | Canonical team abbreviation retained for local filtering and joins. | Carried from `team_context_weekly`. |
| season | int | required_now | yes | NFL season. | Carried from `team_context_weekly`. |
| week | int | required_now | yes | NFL week number. | Carried from `team_context_weekly`. |
| pass_rate_over_expected | float | null_when_unavailable | no | Team pass rate over expected. | Explicit null; requires play-by-play/game-state modeling not in the current public path. |
| neutral_pass_rate | float | null_when_unavailable | no | Team pass rate in neutral situations. | Carried from `team_context_weekly`; currently null pending play-by-play derivation. |
| red_zone_pass_rate | float | null_when_unavailable | no | Team pass rate inside the red zone. | Carried from `team_context_weekly`; currently null pending play-by-play derivation. |
| pace_index | float | derived_now_if_available | no | Relative pace index for the same season-week. | Team `pace_proxy` divided by the season-week league average `pace_proxy`. |
| quarterback_stability | float | null_when_unavailable | no | QB continuity/stability signal. | Explicit null; would require roster depth-chart/QB start continuity logic beyond current scope. |
| play_caller_continuity | float | null_when_unavailable | no | Play-caller continuity signal. | Explicit null; no coaching data source is included in the current public pipeline. |
| target_competition_index | float | derived_now_if_available | no | Effective number of target earners in the offense. | Carried from `team_context_weekly`; inverse target-share concentration by team-week. |
| receiver_room_certainty | float | null_when_unavailable | no | Receiver room certainty or continuity metric. | Carried from `team_context_weekly`; currently null pending future roster/usage logic. |
| vacated_target_share | float | derived_now_if_available | no | Share of prior-season team targets vacated from the current roster. | Prior-season targets from players absent from the current season roster divided by prior-season team targets when adjacent seasons are present; null otherwise. |
