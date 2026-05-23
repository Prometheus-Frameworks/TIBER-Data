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

## Ingestion and promotion

`scripts/ingest_player_ownership.py` reads a repo-held source roster or ownership fixture, normalizes rows into the `player_ownership_v0` latest-state shape, validates the normalized payload, compares it with a previous latest artifact, and prints a JSON dry-run report.

Dry-run is the default behavior and does not write promoted artifacts or event ledgers. Operators can pass `--dry-run` explicitly for clarity:

```bash
python scripts/ingest_player_ownership.py \
  --source data/fixtures/player_ownership/source_roster_fixture.json \
  --previous exports/promoted/player_ownership/player_ownership_latest.json \
  --dry-run
```

Operators should inspect the report before any future promotion path exists. In particular:

- `team_changes`, `status_changes`, and `football_level_changes` are candidates only; they are not promoted by this command.
- `identity_unresolved` means the source row is not safe to match to existing ownership truth.
- `source_conflicts` means multiple source rows disagree for the same player identity.
- `removed_or_missing_from_source` is uncertainty, not a release or free-agent claim.
- `validation_errors` must be resolved before treating any dry-run output as reliable.

The dry-run command never writes `player_ownership_latest.json`, never appends ownership change events, and never writes a run manifest.

Promotion mode is available through `--write`:

```bash
python scripts/ingest_player_ownership.py \
  --source data/raw/player_ownership/source_roster_input.json \
  --previous exports/promoted/player_ownership/player_ownership_latest.json \
  --write
```

Promotion mode remains fail-closed:

- no-change runs write only `exports/promoted/player_ownership/manifests/player_ownership_ingestion_runs.json`;
- verified team and status changes write an updated latest-state artifact and append JSONL events under `exports/promoted/player_ownership/events/`;
- schema errors, invalid timestamps, invalid status values, unresolved identity, source conflicts, unverified changes, new players, and football-level changes block promotion and are reported in the run manifest;
- source rows missing from a run are preserved from the previous latest artifact and are not interpreted as releases or free-agent claims.

The latest-state artifact is written only after the normalized source, previous latest state, merged promoted latest state, and candidate event records validate. Promoted latest-state players are ordered deterministically by `player_id` and `player_name`.
