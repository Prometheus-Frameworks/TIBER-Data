# NFL Draft Results v1 (canonical result facts)

Canonical promoted artifact target:

- `exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json`

## Current implementation status

The v1 contract now has its first official promoted artifact for the 2026 NFL Draft.

- Contract: `src/contracts/v1/nflDraftResults.ts`
- Validation fixture: `test/fixtures/nfl_draft_results_2026.contract_fixture.json`
- Promoted artifact: `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json`
- Validation test: `test/nflDraftResults.v1.test.ts`

The committed validation fixture remains marked `fixture_only` and is not an official NFL Draft result row. The promoted 2026 artifact contains 257 source-backed rows sourced from NBC Sports ProFootballTalk's published 2026 NFL Draft picks tracker. TIBER-Rookies-relevant QB/RB/WR/TE rows are resolved through the committed overall-pick keyed TIBER-Rookies identity reference at `data/raw/rookies/2026/2026_tiber_rookies_draft_result_id_reference_v0.json`; rows outside that confirmed reference remain `player_id=null` with `provenance_status=source_verified_player_id_unresolved`. No historical draft results are backfilled without repo-held source truth and provenance.

## Ownership boundary

- **TIBER-Data owns official promoted draft result facts and provenance.** Promotion requires source-backed rows with explicit provenance status; missing stable player IDs must remain visibly unresolved rather than fabricated.
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

## Promoted 2026 artifact

The official 2026 promoted artifact is:

- `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json`

Promotion boundaries:

- Coverage is limited to the 2026 NFL Draft only.
- The artifact contains no fabricated player IDs; confirmed QB/RB/WR/TE IDs are applied only through the TIBER-Rookies overall-pick keyed reference, and unresolved IDs are represented as `player_id=null` with `source_verified_player_id_unresolved`.
- Every row carries the same non-empty source label and source URL for the published draft tracker used to build the artifact.
- Rows are draft facts plus confirmed TIBER player identity where available: player name, position, drafting team label as sourced, round, pick in round, overall pick, and `player_id` when resolved.
- The 2026 TIBER-Rookies identity reference uses `overall_pick` as its join key. Player names in that reference are audit context only and must not be used as the sole mapping key because known name variants can exist between draft result sources and TIBER-Rookies records.
- The current resolved coverage is 81 QB/RB/WR/TE rows; the remaining 176 rows stay visibly unresolved.

## Audit-trigger status

Audit trigger is active for this change because it adds a promoted artifact under `exports/promoted/**`, documents promoted export semantics, and updates validation coverage. The change touches the committed raw TIBER-Rookies identity reference used for the overall-pick join, the promoted 2026 artifact, and validation coverage; no historical coverage window is expanded beyond the single 2026 artifact.

## Not included in this PR

- Historical draft result backfill.
- Fabricated player IDs.
- Fabricated source URLs.
- Draft capital proxy scoring.
- Prospect interpretation.
- FORGE consumption wiring.
