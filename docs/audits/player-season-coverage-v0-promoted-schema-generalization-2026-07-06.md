# Audit: Promoted Schema Generalization for `promotion_review` (TIBER-Data #204)

- **Date:** 2026-07-06
- **Scope:** TIBER-Data only. Read-only audit of the contract change made for TIBER-Data #204: a narrow generalization of `schemas/player_season_coverage_v0_promoted.schema.json`.
- **Tracking issues:** [TIBER-Data #202](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/202), [PR #203](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/203), [TIBER-Data #204](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/204)
- **Type:** Audit-only. No promotion, no candidate rebuild, no Forecast/product work.
- **Audit trigger:** per `AGENTS.md` § Audit triggers — this change "adds or changes a contract under `src/contracts/**`, `schemas/**`, or `docs/contracts/**`."

---

## 1. Executive verdict

The change is exactly as narrow as #204 authorized: one schema field (`promotion_review`) generalized from a first-promotion-only `const` to a bounded pattern, plus a wording correction to the schema's own top-level description (which previously implied the whole contract was scoped to a single historical event). **No contradiction found.** The two genuine invariants (`status`, `row_grain`) were checked and confirmed untouched and still enforced. `exports/promoted/**` was not modified. The change was independently confirmed to unblock the real #203 promotion payload (via a pure, non-writing function call) without weakening validation for the original #192 artifact.

## 2. Files inspected

| file | role |
|---|---|
| `schemas/player_season_coverage_v0_promoted.schema.json` | changed (this issue) — `promotion_review` field + top-level `description` |
| `tests/test_player_season_coverage_v0_promoted_schema.py` | new (this issue) — 21 tests |
| `exports/promoted/nfl/player_season_coverage_v0.json` | confirmed **unmodified**; re-validated against the new schema as a regression check |
| `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` | confirmed **unmodified** |
| `data/processed/evidence/player_season_coverage_2021_2025.source_backed.json` | read-only input to the unblock-confirmation test (from #202/#203); confirmed **unmodified** |
| `scripts/promote_player_season_coverage_v0_2021_2025.py` | read-only; its `build_promoted_payload` function was called directly in a test, never its `main()` | 
| `schemas/player_season_coverage_v0.schema.json` | candidate schema — confirmed **unmodified** |
| `AGENTS.md` | governing operating contract — checked for audit-trigger applicability and task-classification boundaries |

## 3. Scope-drift check

| question | finding |
|---|---|
| Were any promoted artifacts or manifests modified? | **No** — `exports/promoted/**` shows no diff; re-hashed and confirmed byte-identical. |
| Was any candidate artifact built or rebuilt? | **No.** |
| Was any unrelated schema field broadened? | **No** — full scan of all `const` constraints in the file found exactly three (`status`, `row_grain`, `promotion_review`); only the one confirmed first-promotion-specific field was changed. |
| Was TIBER-Forecast touched? | **No.** |
| Was any ranking/advice/UI/export/product behavior introduced? | **No.** |
| Was a promotion attempted or a threshold/production claim made? | **No.** |

## 4. Invariant-protection check

- `status` remains `const: "promoted_governed_artifact"` in the schema; a test asserts a deviating payload (`status: "not_promoted"`) still fails validation.
- `row_grain` remains `const: "player_id + season + season_type"`; a test asserts a deviating payload still fails validation.
- Both invariants were independently confirmed present in the schema file itself (not just behaviorally), via direct inspection in `test_status_and_row_grain_remain_const_in_schema`.

## 5. Correctness / bounded-ness check

- New `promotion_review` pattern: `^TIBER-Data#[0-9]+$`. Tested against 4 valid references (`TIBER-Data#192`, `#202`, `#204`, `#1`) — all pass — and 11 malformed/adjacent references (bare numbers, wrong casing, missing/extra characters, whitespace, empty string, and a same-shape reference from a different repo, `TIBER-Forecast#134`) — all correctly fail.
- The pattern is still a required, non-empty, bounded string constraint — not an unconstrained free-form field. It does not accept arbitrary text; only well-formed TIBER-Data issue references.

## 6. Regression check

- The currently-committed, live promoted artifact (`exports/promoted/nfl/player_season_coverage_v0.json`, promoted under #192) still validates against the generalized schema with **zero errors**. The generalization did not narrow anything the original artifact relied on.

## 7. Unblock-confirmation check (TIBER-Data#202 review question 7)

- Calling `scripts/promote_player_season_coverage_v0_2021_2025.py`'s `build_promoted_payload` function directly (the pure, non-writing transformation — no `main()` call, no disk write, nothing under `exports/promoted/**` touched) against the real, already-committed 2021-2025 merged candidate now produces a payload that validates against the generalized schema with **zero errors**, and its `promotion_review` field reads `"TIBER-Data#202"` as expected.
- This confirms the schema was the *only* blocker identified in #202/PR#203 — no other defect surfaced once this field was fixed.

---

## 8. Decision

This audit emits **no promotion decision** — that authority belongs to the schema-generalization report, not to this audit:

```text
may_resume_player_season_coverage_2021_2025_promotion_attempt
```

(already recorded in `docs/reports/player-season-coverage-v0-promoted-schema-generalization-2026-07-06.json`, unchanged by this audit)

**Audit conclusion: no contradiction found. The contract change is narrow, tested, non-regressive, and independently confirmed to unblock the previously-diagnosed promotion defect without weakening any invariant.**

### Explicitly NOT authorized by this audit

- promotion of any artifact
- modification of `exports/promoted/nfl/player_season_coverage_v0.json` or its manifest
- candidate rebuilds
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- threshold decisions, model wiring, or production claims
- ranking/advice/UI/export/product behavior
