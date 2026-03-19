# players

Canonical silver table for player roster and identity metadata.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| player_id | string | required_now | yes | Stable player identifier used as the canonical join key. | Public roster/player metadata source via `nflreadpy` or offline fixture fallback. |
| full_name | string | required_now | yes | Player full display name. | Source field normalization. |
| position | string | required_now | yes | Primary position code. | Source field normalization. |
| team | string | required_now | yes | Current team abbreviation for the configured season snapshot. | Source field normalization. |
| season | int | required_now | yes | Season the roster snapshot applies to. | Pipeline config + source snapshot tagging. |
| age | float | future_optional | no | Player age if cleanly exposed by the public source. | Direct source passthrough when available. |
| college | string | future_optional | no | College name. | Direct source passthrough when available. |
| draft_team | string | future_optional | no | Drafting team abbreviation. | Direct source passthrough when available. |
| draft_round | int | future_optional | no | Draft round. | Direct source passthrough when available. |
