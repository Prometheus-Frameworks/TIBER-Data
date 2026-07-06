# Audit: `player_season_coverage_v0` 2021-2025 Promotion Resume (TIBER-Data #206)

- **Date:** 2026-07-06
- **Scope:** TIBER-Data only. Read-only audit of the change introduced for TIBER-Data #206: the real, live promotion of the 2021-2025 merged candidate.
- **Tracking issues:** [TIBER-Data #202](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/202), [PR #203](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/203), [TIBER-Data #204](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/204), [PR #205](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/205), [TIBER-Data #206](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/206)
- **Type:** Audit-only. No candidate rebuild, no Forecast/product work.
- **Audit trigger:** per `AGENTS.md` § Audit triggers — this change "touches ... `exports/promoted/**`."

---

## 1. Executive verdict

This is the mechanical promotion-resume step the entire #198→#206 chain built toward. It ran exactly as designed: the already-written, already-reviewed `scripts/promote_player_season_coverage_v0_2021_2025.py` was executed for real, all four gates passed, and `exports/promoted/nfl/player_season_coverage_v0.json` / its manifest were updated **only by that script** — no hand edits to either file. Counts, season scope, and lineage all reconcile exactly with what #202/#203 already reviewed. **No contradiction found.**

Two pre-existing tests and one #205-added test broke as a direct, anticipated consequence of this promotion (they hard-coded assumptions that the live promoted file would forever equal the #192-only content); they were updated to test the underlying pure functions instead of the now-superseded live file, with no weakening of what they originally protected.

## 2. Files inspected

| file | role |
|---|---|
| `exports/promoted/nfl/player_season_coverage_v0.json` | **updated by the promotion script** (this change) — 2022-2025 (2383 records) → 2021-2025 (3016 records) |
| `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` | **updated by the promotion script** (this change) |
| `docs/reports/player-season-coverage-v0-2021-2025-promotion-resume.{md,json}` | new (this change) — promotion-resume report |
| `tests/test_promote_player_season_coverage_v0.py` | **updated** (this change) — 2 tests decoupled from the live promoted-file path |
| `tests/test_player_season_coverage_v0_promoted_schema.py` | **updated** (this change) — 1 test decoupled from the live promoted-file path |
| `scripts/promote_player_season_coverage_v0_2021_2025.py` | read-only; run for real via its `main()`, unmodified from #203/#205 |
| `data/processed/evidence/player_season_coverage_2021_2025.source_backed.json` | read-only input, confirmed unmodified, sha re-verified against the pin |
| `scripts/promote_player_season_coverage_v0.py` | the original #192 script — confirmed **unmodified** |
| `schemas/player_season_coverage_v0_promoted.schema.json` | confirmed **unmodified** (already generalized in #205) |
| `AGENTS.md` | governing operating contract — checked for audit-trigger applicability |

## 3. Scope-drift check

| question | finding |
|---|---|
| Was the promoted artifact updated by anything other than the promotion script? | **No** — verified via `diff` against a pre-run backup; only the script's `main()` wrote to these paths. |
| Was the merged candidate rebuilt? | **No** — its sha was re-verified against the pin before promotion and matched exactly; the script only reads it. |
| Were 2021 feasibility or promotion-review questions re-opened? | **No** — this issue explicitly builds on #202/#203's conclusions without re-litigating them. |
| Was TIBER-Forecast touched? | **No.** |
| Was any threshold-acceptance, leakage-audit, production-readiness, or product claim made? | **No.** |
| Was any ranking/advice/UI/export/Fantasy behavior introduced? | **No.** |

## 4. Gate verification

All four gates required by #206 were independently confirmed:

1. **Merged candidate sha matches the pin** (`c92404a1...`) — confirmed via the script's own fail-closed check (it would have raised `PromotionGateError` otherwise) and independently re-hashed.
2. **Candidate validator passes** — 0 errors against `schemas/player_season_coverage_v0.schema.json` + business rules.
3. **Promoted schema validates with `promotion_review: TIBER-Data#202`** — confirmed both by the script's own internal schema check (which would have raised otherwise) and by an independent `jsonschema` validation pass against the committed output, 0 errors.
4. **Prior promoted artifact lineage check passes** — the script compared the pre-run live file's sha against its hardcoded expectation (`29f8e378...`, the #192-era artifact) and only proceeded because they matched.

## 5. Reproducibility / drift-protection check

- Re-hashing the committed promoted artifact and manifest confirms the manifest's `promoted_artifact_sha256` field matches the actual committed bytes exactly.
- A live-fire test of the drift-protection gate: running the promotion script a second time (after the first successful run) was independently attempted and correctly **refused**, since the lineage check now compares against a prior sha the live file no longer has (it has moved on to itself). Both files were confirmed byte-identical before and after that refused attempt — the failed second run wrote nothing.

## 6. Test-suite impact check

Two pre-existing tests (`test_promoted_records_match_pinned_candidate_verbatim`, `test_promotion_is_deterministic` in `tests/test_promote_player_season_coverage_v0.py`) and one test added in #205 (`test_pr203_promotion_helper_payload_now_passes_schema_without_writing_promoted_files` in `tests/test_player_season_coverage_v0_promoted_schema.py`) failed immediately after the real promotion ran, because all three asserted that the *live* file at `exports/promoted/nfl/player_season_coverage_v0.json` still equaled a rebuild from the #192-only 2022-2025 candidate. That assumption was never going to survive a second, in-place promotion event — which is exactly what #202 through #206 designed and repeatedly confirmed as the intended shape.

Each was updated to test the same underlying property (the #192-era candidate-to-promoted mapping is verbatim and lossless; `build_promoted_payload` is deterministic; the #203 payload passes the generalized schema) by calling `build_promoted_payload` directly and comparing rebuilds against each other or against pinned constants, instead of against the live file. **No governance property was weakened or removed** — each test still fails if the underlying function regresses; they simply no longer assume the live promoted file is frozen at its pre-#206 content.

Full suite after these fixes: 349 passed, 1 skipped. The one skip is a pre-existing, self-designed regression guard from #203 (`test_current_pin_matches_committed_promoted_artifact`) that explicitly self-skips once the promoted artifact moves past the #192 lineage point — exactly what happened here, by design, not a gap.

## 7. Cross-validation against #202/#203

| | #202/#203 (candidate review) | #206 (live promotion) | match |
|---|---|---|---|
| total records | 3016 | 3016 | yes |
| 2021 | 633 | 633 | yes |
| 2022 | 609 | 609 | yes |
| 2023 | 576 | 576 | yes |
| 2024 | 588 | 588 | yes |
| 2025 | 610 | 610 | yes |
| QB | 404 | 404 | yes |
| RB | 771 | 771 | yes |
| TE | 650 | 650 | yes |
| WR | 1191 | 1191 | yes |

---

## 8. Decision

This audit emits **no promotion decision** — that authority belongs to the promotion-resume report, not to this audit:

```text
may_open_forecast_player_history_2021_2023_mirror_refresh_issue
```

(already recorded in `docs/reports/player-season-coverage-v0-2021-2025-promotion-resume.json`, unchanged by this audit)

**Audit conclusion: no contradiction found. The promotion ran exactly as designed and reviewed; the resulting test breakage was anticipated, narrow, and fixed without weakening any governance property.**

### Explicitly NOT authorized by this audit

- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- player-history threshold acceptance, leakage audit, or production-readiness claim
- ranking/advice/UI/export/product behavior
- candidate rebuilds or re-opening 2021 feasibility/promotion-review questions already resolved by #202/#203
