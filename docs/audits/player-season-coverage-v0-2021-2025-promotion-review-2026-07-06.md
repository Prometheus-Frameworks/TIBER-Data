# Audit: `player_season_coverage_v0` 2021-2025 Promotion Review (TIBER-Data #202)

- **Date:** 2026-07-06
- **Scope:** TIBER-Data only. Read-only audit of the change introduced for TIBER-Data #202: a new merged candidate/generated artifact plus a (currently blocked) promotion script.
- **Tracking issues:** [TIBER-Data #198](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/198), [TIBER-Data #200](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/200), [TIBER-Data #202](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/202)
- **Type:** Audit-only. No promotion occurred (see finding below). No Forecast/Teamstate/FORGE work.
- **Audit trigger:** per `AGENTS.md` § Audit triggers — this change "touches ... candidate/generated artifacts" (the new merged `player_season_coverage_2021_2025.source_backed.json`) and "adds large generated JSON artifacts."

---

## 1. Executive verdict

The 2021 data, and its structural merge with the existing 2022-2025 candidate, are sound: schema-valid, validator-clean, and exactly reconciled against prior evidence (#198, #200/#201). **No contradiction was found in the data itself.**

A genuine contradiction *was* found in the **promoted contract**, not the data: `schemas/player_season_coverage_v0_promoted.schema.json` hardcodes `promotion_review` to `const: "TIBER-Data#192"`. Attempting the real promotion run against the real, sha-pinned, validator-clean merged candidate correctly failed closed on this schema mismatch — proof the fail-closed gate works, and proof this defect is real (not a theoretical read of the schema file). No promoted artifact was written or modified as a result; `exports/promoted/nfl/player_season_coverage_v0.json` and its manifest were independently re-hashed after the attempt and confirmed byte-identical to their pre-attempt state.

**This audit's conclusion: safe to merge the new candidate/tooling/reports as evidence; promotion itself must wait on a separate, narrowly-scoped contract-task issue.**

---

## 2. Files inspected

| file | role |
|---|---|
| `scripts/build_player_season_coverage_2021_2025_merged_candidate.py` | new merge script (this change) |
| `data/processed/evidence/player_season_coverage_2021_2025.source_backed.json` | new merged candidate (this change) |
| `scripts/promote_player_season_coverage_v0_2021_2025.py` | new promotion script (this change) — run, and fails closed as designed |
| `docs/reports/player-season-coverage-v0-2021-promotion-review.{md,json}` | new promotion-review report (this change) |
| `data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json` | upstream input (#200/#201), confirmed unmodified, sha re-verified |
| `data/processed/evidence/player_season_coverage_2022_2025.source_backed.json` | upstream input (#190-#192), confirmed unmodified, sha re-verified against the #192 manifest pin |
| `exports/promoted/nfl/player_season_coverage_v0.json` | confirmed **unmodified** (byte-identical before/after the promotion attempt) |
| `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` | confirmed **unmodified** |
| `schemas/player_season_coverage_v0_promoted.schema.json` | confirmed **unmodified** — the blocking `const` is a pre-existing defect, not something this change introduced or attempted to route around |
| `schemas/player_season_coverage_v0.schema.json` | candidate schema — confirmed unmodified, reused as-is |
| `scripts/validate_player_season_coverage_v0.py` | candidate validator — confirmed unmodified, reused as-is |
| `scripts/promote_player_season_coverage_v0.py` | original #192 promotion script — confirmed unmodified; remains the reproducible record of that original event |
| `AGENTS.md` | governing operating contract — checked for audit-trigger applicability and task-classification boundaries |

---

## 3. Scope-drift check

| question | finding |
|---|---|
| Was `exports/promoted/nfl/player_season_coverage_v0.json` modified? | **No** — re-hashed after the promotion attempt; byte-identical to before. |
| Was `PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` modified? | **No.** |
| Was `schemas/player_season_coverage_v0_promoted.schema.json` modified to work around the blocker? | **No** — the defect is reported, not silently patched. Fixing it is explicitly deferred to a follow-up Contract-task issue, since this promotion-review issue's hard boundary does not authorize schema changes. |
| Was the original `scripts/promote_player_season_coverage_v0.py` (the #192 script) modified? | **No** — a separate script was written instead, preserving that script as the unmodified, reproducible record of the original promotion event. |
| Was TIBER-Forecast touched? | **No.** |
| Was any ranking/advice/UI/export/product behavior introduced? | **No.** |

## 4. False-support-claim check

- The merged candidate's `status` is `candidate_evidence_artifact_not_promoted` and its `non_goals` explicitly disclaim promotion and Forecast use.
- No availability/ownership/roster-status field is present on any of the 3016 merged records (validator's `check_no_availability_assertion`, 0 hits).
- The (unrun, blocked) intended promoted payload was unit-tested to carry the *same* `consumer_safety`/`forecast_compatibility_note` posture as the current live promoted artifact — no weakening of consumer-safety language was introduced or attempted.

## 5. Provenance check

- Both upstream candidates were re-verified against their previously-recorded, known-good sha256 pins before merging (2021: `55618590...`, matching PR#201's report; 2022-2025: `39b6e71e...`, matching the live #192 manifest exactly) — **zero drift detected**.
- `scripts/validate_player_season_coverage_v0.py` against the merged 3016-record candidate: **0 errors**.
- Merge script rerun against unchanged inputs: **byte-identical output** (verified, not assumed).
- Grain (`player_id + season + season_type`) has zero duplicates across the full 3016-record merged set.

## 6. Identity / crosswalk risk

- No new identity scheme introduced; the merge is a pure structural concatenation and re-sort of two already-identity-resolved candidates. No `player_id`/`gsis_id` values were altered, generated, or reconciled across the merge (each record retains exactly its original identity fields from its source candidate).

## 7. Downstream / upstream recursion check

- Nothing downstream consumes the new merged candidate file (it is evidence only, not wired to any consumer).
- No product/model output was read back in as upstream evidence.

## 8. Cross-validation against #198 and #200/#201

| position | #198 source-availability | #200/#201 candidate build | merged 2021 slice (this change) |
|---|---|---|---|
| QB | 81 | 81 | 81 |
| RB | 165 | 165 | 165 |
| WR | 256 | 256 | 256 |
| TE | 131 | 131 | 131 |
| **total** | **633** | **633** | **633** |

Three independently-produced counts (an inspection script, a standalone builder, and now a merge of the builder's own committed output) agree exactly.

---

## 9. Decision

This audit emits **no promotion decision** — that authority belongs to the promotion-review report, not to this audit:

```text
player_season_coverage_2021_promotion_blocked_requires_source_boundary_redesign
```

(already recorded in `docs/reports/player-season-coverage-v0-2021-promotion-review.json`, unchanged by this audit)

**Audit conclusion: no contradiction found in the 2021 data or its merge. A real, precisely-diagnosed contract defect blocks promotion; it is out of scope for this issue and is not routed around.** The new candidate/merge tooling and reports are safe to merge as evidence; the promoted artifact remains untouched.

### Explicitly NOT authorized by this audit

- promotion of any artifact
- modification of `schemas/player_season_coverage_v0_promoted.schema.json` or any other contract
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- player-history threshold acceptance, leakage audit, or production-readiness claim
- ranking/advice/UI/export/product behavior
