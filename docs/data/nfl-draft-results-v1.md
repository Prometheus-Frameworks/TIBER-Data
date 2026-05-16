# NFL Draft Results v1 (canonical result facts)

Canonical promoted artifact target:

- `exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json`

## Current implementation status

This is a first-pass contract, validation, and documentation foundation only.

- Contract: `src/contracts/v1/nflDraftResults.ts`
- Validation fixture: `test/fixtures/nfl_draft_results_2026.contract_fixture.json`
- Validation test: `test/nflDraftResults.v1.test.ts`
- Promoted artifact committed in this PR: none

The committed validation fixture is marked `fixture_only` and is not an official NFL Draft result row. TIBER-Data does not currently hold source-truth draft result files with clear provenance, so this PR does not backfill historical draft results and does not create a promoted export artifact.

## Ownership boundary

- **TIBER-Data owns official draft result facts and provenance** once source-truth draft results are committed with clear provenance.
- **TIBER-Rookies owns draft capital proxy scoring and prospect interpretation.** Draft slot facts may inform TIBER-Rookies, but scoring formulas, prospect ranks, and model interpretation do not live in TIBER-Data.
- **FORGE may later consume promoted TIBER-Rookies prospect interpretation, not raw draft facts directly.** This PR does not wire FORGE to any draft result artifact.

## Row fields

Each draft result row must contain:

- `draft_year` — integer NFL Draft year; the v1 contract rejects years before the 1936 NFL Draft.
- `player_id` — stable player identifier when resolved; may be `null` only when `provenance_status` explicitly makes unresolved identity acceptable.
- `player_name` — non-empty player display name.
- `position` — non-empty position label as sourced.
- `team` — non-empty drafting team label or abbreviation as sourced.
- `round` — positive integer draft round.
- `pick_in_round` — positive integer pick number within the round.
- `overall_pick` — positive integer overall pick number.
- `source` — non-empty provenance/source label.
- `source_url` — source URL when held; nullable when no URL is committed. Do not fabricate URLs.
- `generated_at` — ISO-8601 timestamp for artifact generation.
- `provenance_status` — one of:
  - `source_verified`
  - `source_verified_player_id_unresolved`
  - `needs_verification`
  - `fixture_only`

## Validation and fail-closed behavior

- Artifact payloads must be non-empty arrays of strict row objects.
- `draft_year` must be an integer year and must be at least `1936`.
- `round`, `pick_in_round`, and `overall_pick` must be positive integers.
- `player_name`, `position`, `team`, `source`, `generated_at`, and `provenance_status` must be present and non-empty.
- `generated_at` must parse as an ISO-8601 datetime with offset.
- `source_url` must be either a valid URL or `null`.
- `player_id=null` is rejected for `source_verified`; use `source_verified_player_id_unresolved`, `needs_verification`, or `fixture_only` only when the unresolved identity state is intentional and visible.
- `source_verified_player_id_unresolved` is rejected when `player_id` is non-null.

## Audit-trigger status

Audit trigger is active for this change because it adds a contract under `src/contracts/v1/` and documents promoted export semantics. No promoted artifact is committed, no raw source data is touched, and no supported historical coverage window is expanded.

## Not included in this PR

- Historical draft result backfill.
- Fabricated player IDs.
- Fabricated source URLs.
- Draft capital proxy scoring.
- Prospect interpretation.
- FORGE consumption wiring.
