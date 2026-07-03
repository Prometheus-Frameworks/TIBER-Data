# Promotion review: player_season_coverage_v0 (#192)

_2026-07-03 • record `player-season-coverage-v0-promotion-review-2026-07-03` • **Decision: `promote_player_season_coverage_v0`**_

Governance review of the candidate artifact `data/processed/evidence/player_season_coverage_2022_2025.source_backed.json`, motivated by the Forecast player-history chain (Forecast #99–#116) and executed per the #192 gates. Promotion is earned here by source quality, reproducibility, provenance, and consumer-safety — not by downstream model performance. **No decision in this review authorizes Forecast production binding**; that remains a separate downstream issue.

JSON companion: `player-season-coverage-v0-promotion-review-2026-07-03.json`.

## 1. Source and artifact identity — **verified**

All values re-verified from the artifact itself (not assumed from the issue text):

| Property | Verified value |
|---|---|
| Path | `data/processed/evidence/player_season_coverage_2022_2025.source_backed.json` |
| sha256 | `39b6e71e36d667509221137f2b712143fe5fdccf5423f50e81b5c7a138c0072b` (matches the Forecast pin exactly) |
| Status before review | `candidate_evidence_artifact_not_promoted` |
| Records | 2,383 (2022: 609, 2023: 576, 2024: 588, 2025: 610) |
| season_type | REG only (2,383/2,383) |
| Positions | QB 323, RB 606, WR 935, TE 519 — QB/RB/WR/TE only |
| Row grain | `player_id + season + season_type`; **0 duplicate grains** |
| Ordering | deterministic — sorted by (season, player_id) |
| Source names | exactly 3, all approved: `nflreadpy.load_player_stats(summary_level='reg')`, `…(summary_level='week')`, `nflreadpy.load_players()` |
| Fixture/scaffold markers | **none** across all 7,149 source refs |
| Identity confidence | `source_verified` on 2,383/2,383 records |

The existing validator passes the artifact with zero errors (2,383 records).

## 2. Schema and contract readiness — **ready; promotion does not weaken the contract**

- `schemas/player_season_coverage_v0.schema.json` requires the full record contract (identity, position, season, explicit `season_type` enum REG/POST/REG+POST, `source_refs` with `source_name`/`observed_at`/`confidence`, teams, coverage fields, missing_fields) and pins envelope `status` as a const — the candidate schema **cannot** describe a promoted artifact, which is correct.
- Promotion therefore adds `schemas/player_season_coverage_v0_promoted.schema.json`: the per-record `$defs` contract is **identical** (generated from the candidate schema, not re-typed); only the envelope changes (status const `promoted_governed_artifact`; `promoted_at`, `promotion_review`, `source_candidate` with sha, `approved_source_allowlist`, and `consumer_safety` become required). The candidate schema is untouched.
- Business rules (validator): duplicate grain, REG+POST overlap ambiguity, explicit season_type, multi-team `primary_team_rule`, forbidden availability/ownership/status fields, source_refs presence + fixture rejection, age/career fabrication guards, zero-vs-null distinction — all already enforced and all pass.

## 3. Source provenance allow-list — **gap found and fixed in this PR; artifact passes the strict standard**

The validator previously rejected fixture markers and missing refs but never required sources to be **approved** — the same gap Forecast closed downstream in #110 (gate) and #112 (run boundary). Fixed here: `APPROVED_SOURCE_NAME_PREFIXES` (`nflreadpy.load_player_stats(`, `nflreadpy.load_players(`) with the **all-source standard**, matched as prefixes — every `source_ref` on every record must START with an approved call-shape, so a record carrying an approved source plus an unapproved extra (e.g. `manual_override_or_unknown_source`) fails closed, and so does free text that merely embeds an approved token (e.g. `manual_override:nflreadpy.load_players()`). Regression tests cover mixed-source, unapproved-only, embedded-token, fixture-marked, and missing provenance. The real artifact passes: 0 unapproved refs across 2,383 records × 3 refs each.

## 4. Reproducibility — **promotion is deterministic; fresh source rebuild documented honestly**

Two distinct reproducibility claims, kept separate:

- **Promotion (this PR)**: `python scripts/promote_player_season_coverage_v0.py` is deterministic and network-free — a pure transformation of the sha256-pinned candidate (fail-closed on sha mismatch, validator errors, or scope violations), with a fixed `promoted_at`. Verified byte-identical across repeated runs; the manifest pins the promoted file's own sha256 (`29f8e378127fa5426e5897ac4522b6187941312edabab357d8a427fb20511035`).
- **Candidate rebuild**: `python scripts/build_player_season_coverage_2022_2025.py` (network: nflreadpy; Python ≥ the repo's pyproject environment). Content-reproducible against unchanged upstream data, but **not byte-identical across runs** — the artifact embeds `observed_at`/`generated_at` timestamps, and upstream nflreadpy data is mutable (stat corrections land upstream). **Policy recorded**: a rebuilt candidate gets a NEW sha, fails the promotion pin closed, and requires a NEW governance review before re-promotion. If upstream `nflreadpy` behavior changes (schema or semantics), the build script and spec must be re-reviewed before any rebuild is trusted.

This satisfies the gate: the promoted artifact is deterministically regenerable and sha-verifiable from the recorded, pinned input; the path from live sources is documented with its real limitations rather than overclaimed.

## 5. Null and unavailable-field semantics — **preserved and verified over all rows**

- Unavailable usage fields (`snap_share`, `routes_run`, `route_participation`, `red_zone_targets`, `red_zone_carries`): **0** zero-coercions across all 2,383 records; all remain null.
- Real zeros preserved: 174 records carry a genuine `season_ppr` of 0 — distinct from unavailability.
- `games_missed` remains in `missing_fields` (documented absence), never fabricated.
- Age/career fabrication: **0** records with `season_age` despite null `birth_date`; **0** with `career_year` despite null `rookie_year`.
- Forbidden availability/ownership/status fields: **0** occurrences.

## 6. Consumer-safety boundary — embedded in the promoted envelope

**Allowed** (after promotion): source-backed player-season production/history evidence (REG, QB/RB/WR/TE, 2022–2025); row-level `source_refs`/`identity_confidence`/provenance; team-of-record context as production-row context only.

**Not allowed**: current active roster status; player availability or injury status; depth chart role; ownership/team membership; product advice or fantasy rankings/start-sit/trade/draft output; **Forecast production binding without a separate Forecast issue and gate**.

These lists ship inside the promoted artifact and manifest (`consumer_safety`), not only in this report.

Note on the pre-existing `exports/promoted/nfl/` contents: the older exports there are offline-fixture-sourced scaffolds (some carrying `active_roster_status` fields). This promotion does **not** inherit that pattern — it establishes the stricter standard above — and reviewing/retiring those legacy exports is flagged as follow-up work outside this issue's scope.

## 7. Forecast compatibility note — recorded, no Forecast change here

If/when Forecast consumes the promoted artifact, it must do so via a **separate Forecast-side gate** that re-verifies sha/provenance against this promotion's manifest, enforces target-season leakage splits structurally (the #104/#110/#112 pattern), and weighs a **production-only feature contract** given the Forecast #116 attribution finding (the production family carries essentially all of the candidate signal). No product-facing claim is authorized until a Forecast production-binding review passes. This note ships inside the promoted envelope (`forecast_compatibility_note`). This PR modifies nothing in Forecast.

## Decision

**`promote_player_season_coverage_v0`** — all seven gates pass, with the provenance allow-list strengthened as part of this review. Promoted outputs created:

- `exports/promoted/nfl/player_season_coverage_v0.json` (2,383 records, envelope per section 2; sha256 `29f8e378…1035`)
- `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json` (envelope + promoted-file sha, no records)
- `schemas/player_season_coverage_v0_promoted.schema.json`

The candidate artifact remains in place, byte-identical, still `candidate_evidence_artifact_not_promoted` — existing Forecast pins and historical reports stay valid.

## Non-goals confirmed

- No TIBER-Forecast modification; no player-history feature binding; no Forecast mirrors created.
- No fantasy advice, rankings, start/sit, trade, draft, or product output.
- No active/inactive/IR/practice-squad/ownership inference; no fabricated missing/unavailable fields.
- Forecast #116 is treated as motivation for this review, not production proof.
- No decision here authorizes Forecast production binding — that requires a separate downstream Forecast issue.
