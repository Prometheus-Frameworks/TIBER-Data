# Promotion Resume: `player_season_coverage_v0` — 2021-2025

- **Generated at:** 2026-07-06
- **Tracking issue:** TIBER-Data#206
- **Prior chain:** #198/#199 (2021 source feasibility) → #200/#201 (2021 candidate build) → #202/#203 (promotion review, blocked on schema) → #204/#205 (schema generalized)
- **Status:** promotion-resume report. This is evidence, not a decision authority beyond what's stated below.

## What was run

```bash
python3 scripts/promote_player_season_coverage_v0_2021_2025.py
```

against `main` post-#205, with no code changes to the promotion script or the merged candidate.

## Gates confirmed passing (per #206's required work item 3)

| gate | result |
|---|---|
| merged candidate sha matches the pinned value (`c92404a1...`) | **pass** |
| candidate validator (schema + business rules) | **pass**, 0 errors |
| promoted schema validates with `promotion_review: TIBER-Data#202` | **pass** (unblocked by #205's generalized pattern) |
| prior promoted artifact lineage check (expected prior sha `29f8e378...`, the #192-era artifact) | **pass** |

## Result

- `exports/promoted/nfl/player_season_coverage_v0.json` and `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` were updated **only by the promotion script** — no hand edits.
- **Seasons:** `[2021, 2022, 2023, 2024, 2025]` (previously `[2022, 2023, 2024, 2025]`).
- **Records:** 3016 (previously 2383) — reconciles exactly with #203's merged-candidate finding.
- **Counts by season:** 2021: 633, 2022: 609, 2023: 576, 2024: 588, 2025: 610.
- **Counts by position:** QB 404, RB 771, TE 650, WR 1191.
- `promotion_review`: `"TIBER-Data#202"`. `promotion_decision`: `"promote_player_season_coverage_v0_2021_2025"`.
- `source_candidate`: the merged 2021-2025 candidate (`c92404a1b519a62ee9f4b75f74662157fc8dd02b883648d4cdae694d0e021424`).
- `source_candidate_lineage`: both upstream candidates recorded with path/sha/seasons/record_count (2021 candidate: 633 records; 2022-2025 candidate: 2383 records).
- `prior_promoted_artifact`: the #192-era promoted bytes (`29f8e378...`), with an explicit note that this event supersedes that output without invalidating #192's review, and that those bytes remain reconstructible by re-running the unmodified `scripts/promote_player_season_coverage_v0.py` against the unchanged, still-pinned 2022-2025 candidate.

## Verification performed

- **Manifest hash match:** `PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json`'s `promoted_artifact_sha256` recomputed independently from the committed promoted-artifact bytes and confirmed to match exactly.
- **Schema validation:** the promoted artifact validates against `schemas/player_season_coverage_v0_promoted.schema.json` with 0 errors.
- **Drift protection confirmed live:** a second run of the promotion script (after the first had already written the new artifact) correctly refused to proceed, since its lineage check compares against the pre-#206 prior sha and the live file had, by design, moved past that point. Both files were confirmed byte-identical before and after that refused second attempt — nothing was corrupted.
- **Full repo test suite:** 349 passed, 1 skipped (typecheck passed). The 1 skip is a pre-existing, self-designed regression guard (`test_current_pin_matches_committed_promoted_artifact`, from #203) that explicitly self-skips once the promoted artifact moves past the #192 lineage point it assumes -- exactly what happened here, by design.
- **Two pre-existing tests updated** (`tests/test_promote_player_season_coverage_v0.py::TestPromotedArtifact::test_promoted_records_match_pinned_candidate_verbatim` and `::test_promotion_is_deterministic`, plus `tests/test_player_season_coverage_v0_promoted_schema.py::test_pr203_promotion_helper_payload_now_passes_schema_without_writing_promoted_files`): these asserted the *live* promoted file still equaled the #192-only rebuild, an assumption #202-#206 intentionally broke by extending the same artifact in place. Decoupled them to test the pure `build_promoted_payload` function directly (comparing rebuilds against each other / against pinned constants) instead of against the live, now-superseded file. No governance property was weakened -- the #192-era candidate-to-promoted mapping and promotion determinism are both still verified, just no longer coupled to a stateful file path.

## Post-review fixes (PR #207)

A Codex review found two real defects in this promotion, both corrected before merge:

1. **Missing live-artifact rebuild check for the new lineage.** Decoupling the two tests above removed the only assertion that the *committed* promoted file matched a fresh rebuild, without adding an equivalent check for the 2021-2025 case -- and the existing `test_current_pin_matches_committed_promoted_artifact` guard now permanently skips (it only fires while `promotion_review == "TIBER-Data#192"`). A coherent drift (hand-editing the promoted JSON and recomputing a matching manifest hash) could have passed every other check undetected. Fixed by adding `test_committed_2021_2025_promoted_artifact_matches_rebuild` to `tests/test_promote_player_season_coverage_v0_2021_2025.py`, which proves the committed bytes equal a fresh `build_promoted_payload` rebuild from the pinned merged candidate and the pinned prior sha.
2. **Dangerous reconstruction note.** The manifest's `prior_promoted_artifact.note` told a reader the #192-era bytes were "reconstructible by running `scripts/promote_player_season_coverage_v0.py`" -- but that script writes to the same `exports/promoted/nfl/player_season_coverage_v0.json` / manifest path this promotion now uses, so following that note against a live, post-#206 checkout would silently overwrite the current 2021-2025 governed artifact with the stale 2022-2025-only content. Fixed the note text in `scripts/promote_player_season_coverage_v0_2021_2025.py` to warn explicitly against this and point to safe alternatives (git history, or a redirected scratch output), then applied that corrected note to the already-committed live artifact via a new, narrowly-scoped remediation script (`scripts/fix_2021_2025_promoted_lineage_note.py`) that fails closed unless the only difference from the current committed bytes is the note text itself. Verified via `diff`: exactly one field changed (the note string, and the manifest hash it feeds into) -- nothing else.

Full suite after these fixes: 353 passed, 1 skipped. Typecheck: passed.

## Decision

```text
may_open_forecast_player_history_2021_2023_mirror_refresh_issue
```

- **Basis:** all four promotion gates passed, the promoted artifact and manifest were updated only by the promotion script, hashes are self-consistent and match committed bytes, counts/season scope reconcile exactly with #203, and full lineage back to #192 and #203 is preserved and documented in the manifest.
- This decision authorizes only a **separate TIBER-Forecast issue** to consider refreshing non-production mirrors. It does not itself refresh mirrors, run validation, accept thresholds, or bind any model/product behavior.

### Explicitly NOT emitted / NOT authorized by this report

- `player_season_coverage_2021_2025_promotion_resume_blocked`
- `player_season_coverage_2021_2025_promotion_resume_requires_followup`
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- player-history threshold acceptance, leakage audit, or production-readiness claim
- ranking/advice/UI/export/product behavior
- candidate rebuilds or re-opening 2021 feasibility/promotion-review questions already resolved by #202/#203
