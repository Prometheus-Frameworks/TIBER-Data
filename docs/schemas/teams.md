# teams

Canonical silver table for team metadata.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team | string | required_now | yes | Canonical team abbreviation. | Public team metadata source or normalized static fallback. |
| team_name | string | required_now | yes | Full franchise or display name. | Source normalization. |
| conference | string | future_optional | no | Conference affiliation. | Public team metadata passthrough if available. |
| division | string | future_optional | no | Division affiliation. | Public team metadata passthrough if available. |
| season | int | derived_now_if_available | no | Optional season snapshot if metadata is season-bound. | Added when source data is seasonal. |
