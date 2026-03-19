# players

Canonical silver table for player roster and identity metadata.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Stable player identifier used as the canonical join key. | Real roster ingest from `nflreadpy.load_rosters()` or `roster_{season}.parquet`. |
| full_name | string | required_now | yes | Player full display name. | Real source field normalization. |
| position | string | required_now | yes | Primary position code. | Real source field normalization. |
| team | string | required_now | yes | Team abbreviation for the configured season snapshot. | Real source field normalization. |
| season | int | required_now | yes | Season the roster snapshot applies to. | Real source field normalization. |
| age | float | derived_now_if_available | no | Approximate age for the season snapshot. | Deterministically derived from `birth_date` when the roster source exposes it; null otherwise. |
| college | string | derived_now_if_available | no | College name. | Real source passthrough when available. |
| draft_team | string | future_optional | no | Drafting team abbreviation. | Real source passthrough when available; null otherwise. |
| draft_round | int | future_optional | no | Draft round. | Real source passthrough when available; null otherwise. |
