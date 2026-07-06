# Audit: `player_season_coverage_v0` 2021 Candidate Build (PR #201)

- **Date:** 2026-07-06
- **Scope:** TIBER-Data only. Read-only audit of the change introduced by PR #201 (TIBER-Data #200): a new candidate/generated data artifact plus its builder and report scripts.
- **Tracking issues:** [TIBER-Data #198](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/198) (source-feasibility), [TIBER-Data #200](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/200) (candidate build), PR #201 (this change)
- **Type:** Audit-only. No artifact promotion, no contract changes, no Forecast/Teamstate/FORGE work, no mutation of the artifact under audit.
- **Audit trigger:** per `AGENTS.md` § Audit triggers — PR #201 "touches ... candidate/generated artifacts" and "adds large generated JSON artifacts." This audit satisfies that trigger before merge.

---

## 1. Executive verdict

PR #201 is **narrowly scoped and does what it claims**: it adds one new candidate/evidence artifact (`data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json`, 633 rows, 2021 REG QB/RB/WR/TE) and two supporting scripts, and nothing else. No scope drift, no false support claim, and no provenance gap was found.

- **Scope drift:** none found. The change does not touch `exports/promoted/**`, does not modify `scripts/build_player_season_coverage_2022_2025.py` or its promoted output, does not touch TIBER-Forecast, and does not widen the *promoted* artifact's supported window (still `2022-2025`). The new file is additive and self-contained.
- **False support claim:** none found. The artifact's own `status` field is `candidate_evidence_artifact_not_promoted`; `non_goals` explicitly disclaims Forecast use, promotion, and any merge into the promoted 2022-2025 artifact. No active/inactive/roster-status field is present (checked against `AGENTS.md` §4.8-equivalent boundary in the source-boundary spec).
- **Provenance:** sound. Every record's `source_refs` start with an approved prefix (`nflreadpy.load_player_stats(`, `nflreadpy.load_players(`) — verified by `scripts/validate_player_season_coverage_v0.py`, 0 errors, 633/633 records. No fixture/scaffold marker present.
- **Identity/crosswalk risk:** low. Identity is joined by `gsis_id` against `nflreadpy.load_players()`, the same key used by the promoted 2022-2025 builder; no new ID scheme, no invented IDs. Join rate 633/633 (100%).
- **Downstream/upstream recursion risk:** none. Nothing downstream (Forecast, FORGE, product) consumes this artifact; it has no consumers wired to it in this change.
- **Independent cross-validation:** the candidate's row/position counts (QB 81, RB 165, WR 256, TE 131 — 633 total) match **exactly** the independently-built #198 source-availability inspection's counts for the same scope. Two separately-written scripts (an inspection tool and a builder) agree exactly on real 2021 source data, which is a meaningful positive provenance signal.

**Verdict: no contradiction found. This audit does not itself authorize promotion** — that remains gated behind the separate promotion-review issue that PR #201's own decision (`may_open_player_season_coverage_2021_promotion_review_issue`) already names as the required next step.

---

## 2. Files inspected

| file | role |
|---|---|
| `scripts/build_player_season_coverage_2021_candidate.py` | new builder (this PR) |
| `scripts/build_player_season_coverage_2021_candidate_report.py` | new report builder (this PR) |
| `data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json` | new candidate artifact (this PR) |
| `docs/reports/player-season-coverage-v0-2021-candidate-build.{md,json}` | new report (this PR) |
| `docs/reports/player-season-coverage-v0-2021-source-availability.{md,json}` | prior evidence (#198/#199), used for reconciliation |
| `scripts/build_player_season_coverage_2022_2025.py` | promoted builder — confirmed **unmodified** |
| `exports/promoted/nfl/player_season_coverage_v0.json` | promoted artifact — confirmed **unmodified** |
| `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` | promotion manifest — confirmed **unmodified** |
| `schemas/player_season_coverage_v0.schema.json` | candidate schema — confirmed **unmodified**, reused as-is |
| `scripts/validate_player_season_coverage_v0.py` | candidate validator — confirmed **unmodified**, reused as-is |
| `docs/specs/player-season-coverage-v0-source-boundary.md` | governing spec — checked for boundary compliance |
| `AGENTS.md` | governing operating contract — checked for audit-trigger applicability |

---

## 3. Scope-drift check

| question | finding |
|---|---|
| Does this PR modify the promoted 2022-2025 artifact or its manifest? | **No** — `git diff` against the PR #199 merge base shows zero changes under `exports/promoted/**`. |
| Does this PR modify `scripts/build_player_season_coverage_2022_2025.py`? | **No** — a new, separate script was written instead, specifically to avoid touching the file the promoted artifact's sha is pinned to. |
| Does this PR touch TIBER-Forecast? | **No** — confirmed no TIBER-Forecast files changed. |
| Does this PR claim the promoted artifact now spans 2021-2025? | **No** — the new candidate is a separate file (`player_season_coverage_2021_candidate.source_backed.json`) with its own `artifact_id`, `status: candidate_evidence_artifact_not_promoted`, and `seasons: [2021]`. It does not merge with or overwrite the promoted 2022-2025 file. |
| Does this PR introduce ranking/advice/UI/export/product behavior? | **No.** |

## 4. False-support-claim check

- `non_goals` on the new artifact explicitly lists: not promoted/governed Forecast-ready data, not a Forecast input today, no active/inactive/IR/practice-squad status asserted, POST out of scope, does not modify or merge into the promoted 2022-2025 artifact.
- No field resembling `active_status`, `ownership_status`, `roster_status`, or `active_roster_status` is present on any record (validator's `check_no_availability_assertion` passed, 0 hits).
- `identity_confidence` and per-record `missing_fields` are populated honestly; `draft_year` is null for ~33% of records (undrafted players — the same rate and reason as the promoted 2022-2025 artifact, not a new gap), and remains `null`, never fabricated as `0` or a guessed value (validator's `check_age_career_not_fabricated` and `check_zero_vs_null_distinct` both passed).

## 5. Provenance check

- `scripts/validate_player_season_coverage_v0.py data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json` → **`OK: ... passed all validation checks (633 records)`**.
- Every `source_ref.source_name` starts with an approved prefix (`nflreadpy.load_player_stats(`, `nflreadpy.load_players(`); no unapproved or fixture/scaffold source strings found.
- Grain (`player_id + season + season_type`) has zero duplicates (633 unique keys / 633 records).
- `sha256` of the committed candidate file was independently recomputed during PR review and matches the value recorded in the (corrected) report.

## 6. Identity / crosswalk risk

- Identity join key is `gsis_id`, matching `nflreadpy.load_players()` and the same key the promoted 2022-2025 builder already uses — no new or parallel ID scheme introduced.
- Join rate: 633/633 (100%), at or above the 0.95 floor established in #198.
- No `provider_ids` are invented; `espn_id` is passed through only when the source populates it, `sleeper_id` remains `None` (not exposed by `nflreadpy.load_players()` in this environment, consistent with the promoted 2022-2025 artifact's own note).

## 7. Downstream / upstream recursion check

- Nothing in TIBER-Data or TIBER-Forecast is wired to consume `player_season_coverage_2021_candidate.source_backed.json` as of this PR. It is a standalone evidence file under `data/processed/evidence/`, matching the same posture as the existing (also-unconsumed) 2022-2025 candidate file before its own promotion review.
- No downstream product/model output was read back in as if it were upstream evidence (no recursion).

## 8. Cross-validation against #198

| position | #198 source-availability inspection | #201 candidate build | match |
|---|---|---|---|
| QB | 81 | 81 | yes |
| RB | 165 | 165 | yes |
| WR | 256 | 256 | yes |
| TE | 131 | 131 | yes |
| **total** | **633** | **633** | **yes** |

Two independently written scripts (`scripts/inspect_player_season_coverage_2021_source_availability.py` from #198/#199, and `scripts/build_player_season_coverage_2021_candidate.py` from this PR) queried the same approved source family separately and produced identical counts. This is a meaningful cross-check against source drift or a build-time filtering bug.

---

## 9. Decision

This audit emits **no artifact-promotion decision** — that authority belongs to #200/PR #201's own decision, not to this audit:

```text
may_open_player_season_coverage_2021_promotion_review_issue
```

(already recorded in `docs/reports/player-season-coverage-v0-2021-candidate-build.json`, unchanged by this audit)

**Audit conclusion: no contradiction found; no scope-drift, false-claim, provenance, or recursion issue identified.** PR #201 is safe to merge as a candidate/evidence-only change.

### Explicitly NOT authorized by this audit

- promotion of any artifact
- modification of the promoted 2022-2025 `player_season_coverage_v0` artifact or its manifest
- Forecast mirror refresh, Forecast controlled rerun, or any Forecast behavior
- player-history threshold acceptance, leakage audit, or production-readiness claim
- ranking/advice/UI/export/product behavior
