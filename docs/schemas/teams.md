# teams

Canonical silver table for team metadata.

| column | type | requirement_tier | required | description | source / derivation |
|---|---|---|---|---|---|
| team | string | required_now | yes | Canonical team abbreviation. | Real team metadata source or normalized restricted-environment fixture. |
| team_name | string | required_now | yes | Full franchise or display name. | Real source normalization. |
| conference | string | derived_now_if_available | no | Conference affiliation. | Real source passthrough when available. |
| division | string | derived_now_if_available | no | Division affiliation. | Real source passthrough when available. |
| season | int | derived_now_if_available | no | Optional season snapshot if metadata is season-bound. | Not currently materialized in the silver contract. |
