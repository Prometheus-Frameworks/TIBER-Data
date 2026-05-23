# Player Ownership v0 Contracts

This change introduces a player-centric ownership truth layer that complements team/window-shaped `roster_snapshot_v0` artifacts.

- Latest-state contract schema: `schemas/player_ownership_v0.schema.json`
- Change-event contract schema: `schemas/player_ownership_change_event_v0.schema.json`
- Latest-state fixture artifact: `exports/promoted/player_ownership/player_ownership_latest.json`
- Change-event fixture artifact: `exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl`

## Responsibility boundaries

- **TIBER-Data** owns canonical ownership truth, identity lookup, and source-linkable change facts.
- **TIBER-Teamstate** interprets team impact from ownership and roster facts.
- **TIBER-Fantasy** interprets fantasy impact from ownership and teamstate context.

## Layer relationship

- `roster_snapshot_v0` remains team/window-shaped roster truth.
- `player_ownership_v0` is player-centric latest lookup state.
- `player_ownership_change_event_v0` captures meaningful ownership deltas over time.

Latest state and change events are intentionally separate artifacts: one answers current lookup, the other preserves auditable transition history.

## Fixture safety note

The included artifacts under `exports/promoted/player_ownership/**` are **contract-validation scaffolds only** in this PR:

- they use provisional verification/confidence status;
- they include `source_name: fixture_demonstration_only`; and
- they must not be interpreted as source-backed promoted ownership truth.

## Contract rules

- Do not invent player IDs.
- Do not invent team IDs.
- Unknown values must be `null`.
- Every ownership claim must include `source_refs` with source metadata.
- Invalid timestamps, invalid status values, malformed event records, or missing source metadata should fail validation.
