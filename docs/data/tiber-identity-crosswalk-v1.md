# TIBER Identity Crosswalk V1

`TIBER_IDENTITY_CROSSWALK_V1` is the TIBER-Data-owned identity bridge from external provider player identifiers to TIBER canonical player identifiers.

The promoted artifact lives at:

```text
exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json
```

## Ownership boundary

TIBER-Data owns durable identity crosswalks. Downstream systems, including TIBER-Fantasy Management, should consume this artifact rather than hardcoding Sleeper-to-TIBER bridges in application code.

This keeps Fantasy as a consumer shell and keeps identity truth in the data repository that also owns deterministic producer artifacts and handoff contracts.

## Current scope

The V1 artifact currently supports only the `sleeper` provider namespace and only contains operator-verified seed mappings proven during the Management production smoke:

- `sleeper:6797` → `tiber-data-player-2025-justin-herbert`
- `sleeper:9493` → `tiber-data-player-2025-puka-nacua`
- `sleeper:9509` → `tiber-data-player-2025-bijan-robinson`

This is not a claim of full Sleeper player-universe coverage. If a player is absent, downstream consumers should treat that player as unmapped rather than inferring a match. No additional starter rows were added because this repo did not contain reliable Sleeper IDs beyond the operator-verified Management smoke mappings at the time of this artifact.

## Row contract

Each row includes:

- `provider` — provider namespace, currently `sleeper`
- `provider_player_id` — provider raw player ID, for example `6797`
- `provider_canonical_id` — provider-prefixed canonical ID, for example `sleeper:6797`
- `tiber_player_id` — TIBER canonical player ID consumed by FORGE-aligned artifacts
- `player_name`, `position`, `team` — human-auditable descriptors
- `confidence` — mapping confidence; seeded rows are `exact`
- `match_method` — mapping method; seeded rows are `verified_manual_seed`
- `source` — provenance label
- `source_updated_at` — UTC timestamp for the source assertion

## Validation and deterministic generation

Build or refresh the artifact with:

```bash
python scripts/build_identity_crosswalk_v1.py
```

Validate the committed artifact without writing with:

```bash
python scripts/build_identity_crosswalk_v1.py --check
```

Validation fails closed on:

- missing required fields
- unsupported provider namespaces
- malformed `provider_canonical_id` values
- duplicate provider mappings
- conflicting TIBER IDs for the same provider
- missing provenance fields
- non-deterministic record ordering

The JSON Schema companion is:

```text
schemas/tiber_identity_crosswalk_v1.schema.json
```

## Downstream consumption guidance

A follow-up TIBER-Fantasy PR should load `TIBER_IDENTITY_CROSSWALK_V1`, index rows by `provider_canonical_id` or by `(provider, provider_player_id)`, and remove the temporary hardcoded Sleeper bridge once the bundled artifact is available in that runtime.

If Fantasy encounters a Sleeper roster player that is not present in the crosswalk, it should preserve the known provider identity but leave the TIBER/FORGE evidence linkage absent. It should not invent a TIBER player ID or perform fuzzy matching in production code.
