# Promotion Review: `player_season_coverage_v0` — 2021-2025 Extension

- **Generated at:** 2026-07-06T00:00:00Z
- **Tracking issue:** TIBER-Data#202
- **Inputs:** TIBER-Data#198 (source feasibility), #200/PR#201 (2021 candidate build)
- **Status:** promotion-review report. This is evidence/review only — it is not itself a promoted artifact and does not modify `exports/promoted/**`.
- **Scope:** TIBER-Data promotion review only. Does not authorize Forecast mirror refresh, Forecast validation, threshold acceptance, leakage audit, production readiness, or model/product behavior.

## Summary

The 2021 candidate extension (TIBER-Data#200/PR#201) is source-sound, schema-valid, and reconciles exactly with prior evidence. A merged 2021-2025 candidate was built and validated cleanly. **However, promotion itself is blocked** by a narrow, pre-existing contract defect unrelated to the 2021 data: `schemas/player_season_coverage_v0_promoted.schema.json` hardcodes `promotion_review` to `const: "TIBER-Data#192"`, which structurally prevents *any* subsequent promotion event — not specific to this one — from validating under an honest new review reference. Fixing that is a contract-task change this promotion-review issue does not authorize.

## Required review questions

### 1. Should 2021 be appended to the existing promoted artifact, or should a successor artifact/version be created instead?

**Appended** (same `artifact_id: player_season_coverage_v0`, same file path, same schema). The 2021 candidate was built with byte-for-byte identical methodology to the 2022-2025 candidate (same builder logic, same column resolution, same `coverage_status` rule — confirmed by the #198/#200 audits and the exact count reconciliation below). There is no basis for a separate artifact family or a new schema version; this is a season-window extension of an existing, structurally-unchanged contract.

### 2. Does adding 2021 preserve the existing schema, source boundary, row grain, provenance semantics, and validation behavior?

Yes, for the **candidate** schema/grain/provenance: the merged 2021-2025 candidate (`data/processed/evidence/player_season_coverage_2021_2025.source_backed.json`) validates cleanly against the unchanged `schemas/player_season_coverage_v0.schema.json` and `scripts/validate_player_season_coverage_v0.py` (0 errors, 3016 records). Row grain (`player_id + season + season_type`) is unchanged and has zero duplicates across the combined set.

**No**, for the **promoted** schema: see finding under Q7. This is a pre-existing contract narrowness, not something introduced by the 2021 data.

### 3. Do the 2021 candidate counts reconcile with the candidate-build report and #198 source-availability report?

Yes, exactly:

| position | #198 source-availability | #200/#201 candidate build | merged 2021-2025 (2021 slice) |
|---|---|---|---|
| QB | 81 | 81 | 81 |
| RB | 165 | 165 | 165 |
| WR | 256 | 256 | 256 |
| TE | 131 | 131 | 131 |
| **total** | **633** | **633** | **633** |

Combined 2021-2025 totals: 3016 records (2021: 633, 2022: 609, 2023: 576, 2024: 588, 2025: 610); by position QB 404, RB 771, TE 650, WR 1191 — each exactly the sum of the corresponding 2021 and 2022-2025 counts.

### 4. Does the combined promoted/successor artifact preserve deterministic ordering and machine-readable provenance?

Yes. The merge script (`scripts/build_player_season_coverage_2021_2025_merged_candidate.py`) concatenates the two already-validated candidates and re-sorts by `(season, player_id)`, the same convention both source builders already use. Every record's original `source_refs` are carried through unmodified (no row was recomputed, filtered, or fabricated). Re-running the merge script against the unchanged, sha256-pinned inputs was verified to produce **byte-identical output**.

### 5. Does the combined artifact avoid any false support claim, especially around active/inactive/IR/practice-squad status, roster membership, Fantasy readiness, or Forecast consumption?

Yes. The merged candidate's `status` remains `candidate_evidence_artifact_not_promoted` (until promotion actually succeeds), and its `non_goals` explicitly disclaim Forecast use and promotion. No record carries an availability/ownership/roster-status field (validator's `check_no_availability_assertion` passes on the combined set). The intended promoted payload (see `build_promoted_payload` in the promotion script, fully unit-tested) carries the identical `consumer_safety`/`forecast_compatibility_note` posture as the current promoted artifact — no weakening.

### 6. Are all generated hashes/manifests computed from the committed bytes and reproducible from the committed scripts?

Yes.

- Merged candidate sha256: `c92404a1b519a62ee9f4b75f74662157fc8dd02b883648d4cdae694d0e021424` — computed from the actual committed file bytes, verified reproducible (rerun produced byte-identical output).
- Both upstream candidate shas were re-verified against their known-good pins before merging (`39b6e71e...` for 2022-2025, matching the #192 manifest exactly; `55618590...` for 2021, matching PR#201's report exactly) — no drift detected.
- The promotion script (`scripts/promote_player_season_coverage_v0_2021_2025.py`) is network-free and pins the merged candidate's sha; its `build_promoted_payload` function is fully unit-tested (8 tests) against fake data, independent of the schema gate discussed in Q7.

### 7. Does the promotion review require any source-boundary amendment before promotion?

**Yes — a narrow contract amendment, not a source-boundary amendment in the `nflreadpy`-source sense.** Running the promotion script against the real, validated, sha-pinned merged candidate fails closed with:

```text
FAIL CLOSED: promoted payload fails its schema; first: promotion_review: 'TIBER-Data#192' was expected
```

Inspection of `schemas/player_season_coverage_v0_promoted.schema.json` confirms `promotion_review` is defined as `{"type": "string", "const": "TIBER-Data#192"}` — a literal constant pinned to the *first* promotion event. This means the promoted schema, as currently written, can **never** validate a second promotion event under an honest `promotion_review` value, regardless of season, data quality, or review rigor. (The schema's other two `const` fields — `status` and `row_grain` — are correctly invariant and are not implicated.)

This is a genuine defect independent of the 2021 data itself, and fixing it (e.g., relaxing to a pattern like `^TIBER-Data#\d+$`, or to a plain `type: string`) is a **Contract task** per `AGENTS.md`'s task-classification gate (`schemas/**`), which this promotion-review issue's hard boundary does not authorize — the issue lists only data/evidence/manifest/audit surfaces as in scope. A properly-scoped follow-up contract-task issue must relax this constant before any promotion (this one or any future one) can proceed. No promoted artifact was modified while working around this; the fail-closed gate did its job (verified: `exports/promoted/nfl/player_season_coverage_v0.json` and its manifest are byte-identical to their pre-review state).

### 8. Does the promotion trigger a required audit artifact under `docs/audits/**`, and is that audit committed?

Yes. This change adds a new candidate/generated artifact (`data/processed/evidence/player_season_coverage_2021_2025.source_backed.json`, 3016 records), which fires `AGENTS.md`'s audit trigger regardless of whether promotion itself proceeds. The required audit is committed at `docs/audits/player-season-coverage-v0-2021-2025-promotion-review-2026-07-06.{md,json}`.

## What was built (all committed, none promoted)

- `scripts/build_player_season_coverage_2021_2025_merged_candidate.py` — deterministic, network-free merge of the two already-validated candidates. Fails closed on sha drift of either input, overlapping seasons, duplicate grain, or validator errors in either input.
- `data/processed/evidence/player_season_coverage_2021_2025.source_backed.json` — the merged candidate. 3016 records, validator-clean, `status: candidate_evidence_artifact_not_promoted`.
- `scripts/promote_player_season_coverage_v0_2021_2025.py` — the promotion script, structurally identical in its gates to the original `promote_player_season_coverage_v0.py` (which is unmodified), plus explicit lineage fields (`source_candidate_lineage`, `prior_promoted_artifact`) documenting continuity back to TIBER-Data#192. Its `build_promoted_payload` function is fully unit-tested and ready to run the moment the schema blocker in Q7 is resolved. Running it today correctly fails closed (see Q7) and writes nothing.
- 18 new offline unit tests across both scripts, plus a regression test tying the merged candidate's committed counts back to the known-good #198/#200 figures.

## Decision

```text
player_season_coverage_2021_promotion_blocked_requires_source_boundary_redesign
```

- **Basis:** the 2021 data and its merge into a combined 2021-2025 candidate are fully sound (schema-valid, validator-clean, exactly reconciled, deterministically reproducible). Promotion is blocked solely by a pre-existing, narrowly-scoped contract defect (`promotion_review` hardcoded via `const` to the first promotion event's issue number) that this issue's hard boundary does not authorize fixing. A follow-up contract-task issue must relax that schema field before this (or any future) promotion can proceed.

### Explicitly NOT emitted / NOT authorized by this report

- `may_open_forecast_player_history_2021_2023_mirror_refresh_issue`
- `player_season_coverage_2021_promotion_blocked_requires_candidate_rebuild` (the candidate itself needs no rebuild — it is sound)
- `player_season_coverage_2021_promotion_review_inconclusive_requires_followup` (the blocker is precisely diagnosed, not inconclusive)
- promotion of any artifact
- modification of `exports/promoted/nfl/player_season_coverage_v0.json` or its manifest (both confirmed byte-identical to their pre-review state)
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- player-history threshold acceptance, leakage audit, or production-readiness claim
- ranking/advice/UI/export/product behavior

## Recommended next issue (separate, not started here)

A narrowly-scoped **Contract task**: relax `schemas/player_season_coverage_v0_promoted.schema.json`'s `promotion_review` field from `const: "TIBER-Data#192"` to a pattern (e.g. `^TIBER-Data#\d+$`) or plain `type: string`, with its own review of whether any other promoted-schema field needs similar generalization before a second promotion event of *any* kind can occur. Once that lands, re-running `scripts/promote_player_season_coverage_v0_2021_2025.py` (already written and tested) is the mechanical next step — not a re-review of the 2021 data itself.
