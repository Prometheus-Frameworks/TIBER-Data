# weekly_player_stats

Canonical silver table for player-week production from the deterministic public ingest path. The current contract is regular-season only.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Canonical player identifier. | Real source normalization from nflverse player-week stats. |
| full_name | string | required_now | yes | Player full name. | Real source normalization. |
| position | string | required_now | yes | Position code. | Real source normalization. |
| team | string | required_now | yes | Team abbreviation for the player-week. | Real source normalization. |
| season | int | required_now | yes | NFL season. | Real source normalization. |
| week | int | required_now | yes | NFL week number. | Real source normalization. |
| targets | float | required_now | yes | Player passing targets. | Real source field. |
| receptions | float | required_now | yes | Receptions. | Real source field. |
| receiving_yards | float | required_now | yes | Receiving yards. | Real source field. |
| receiving_tds | float | required_now | yes | Receiving touchdowns. | Real source field. |
| rushing_attempts | float | required_now | yes | Rushing attempts. | Real source field or normalized alias such as `carries`. |
| rushing_yards | float | required_now | yes | Rushing yards. | Real source field. |
| rushing_tds | float | required_now | yes | Rushing touchdowns. | Real source field. |
| pass_attempts | float | derived_now_if_available | no | Player pass attempts for aggregation and QB modeling. | Real source field or normalized alias such as `attempts`; zero-filled for non-passers. |
| completions | float | derived_now_if_available | no | Player completions. | Real source field; zero-filled for non-passers. |
| passing_yards | float | derived_now_if_available | no | Player passing yards. | Real source field; zero-filled for non-passers. |
| passing_tds | float | derived_now_if_available | no | Player passing touchdowns. | Real source field; zero-filled for non-passers. |
| fantasy_points_ppr | float | derived_now_if_available | no | PPR fantasy points. | Real source passthrough when available; otherwise deterministic box-score formula. |
| air_yards | float | derived_now_if_available | no | Receiving air yards. | Real source passthrough when available; null otherwise. |
| red_zone_targets | float | future_optional | no | Red zone targets. | Null when the stable public ingest path does not expose the field cleanly. |
| routes_run | float | future_optional | no | Routes run. | Pending future public participation/tracking-compatible source. |
| snap_share | float | future_optional | no | Offensive snap share. | Pending future public participation/tracking-compatible source. |
