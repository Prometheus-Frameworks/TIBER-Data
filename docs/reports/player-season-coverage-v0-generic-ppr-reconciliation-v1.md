# `player_season_coverage_v0` generic PPR reconciliation v1

- **Generated at:** 2026-07-27T23:28:38Z
- **Tracking:** TIBER-Data #228
- **Terminal decision:** `scoring_reconciliation_evidence_ready`
- **Status:** candidate reconciliation evidence; not promoted and not a Forecast admission/run decision.
- **Profile:** `tiber-generic-full-ppr-v1` (`sha256:b1404afb1c7c6c9760b36090e5a84ef3fd2a29dfe8ba2e2fe0efb98d0ac6622e`)
- **Pinned source:** `exports/promoted/nfl/player_season_coverage_v0.json` at `sha256:d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` from TIBER-Data `31c0c8e751816d262cf79ffef1a4ae9b6c9b70d5`.

## Decision

The exact issue-approved generic PPR total is computable from governed components for every one of the 3,016 promoted rows. That component-derived value is usable as candidate scoring-identity evidence, subject to a separate Forecast admission decision.

The promoted `production_summary.season_ppr` field is **not equivalent** to that profile for all rows: after independent cent-scale `ROUND_HALF_UP` normalization, 2,186 rows match exactly and 830 have a nonzero cent-scale difference. Raw serialization residue remains visible for diagnostics but does not create a semantic mismatch or tolerance pass. Differences are preserved, source totals are never overwritten, and omitted source-total component families are never inferred from the delta.

## Overall reconciliation

| Measure | Count / rate |
| --- | ---: |
| Source rows | 3016 |
| Exact matches | 2186 |
| Within tolerance | 0 |
| Scoring mismatches | 830 |
| Source-total conformance | 72.48% |
| Source-total mismatch | 27.52% |
| Missing profile components | 0 |
| Missing source totals | 0 |

## By season

| Season | Rows | Exact | Mismatch | Conformance |
| ---: | ---: | ---: | ---: | ---: |
| 2021 | 633 | 465 | 168 | 73.46% |
| 2022 | 609 | 444 | 165 | 72.91% |
| 2023 | 576 | 399 | 177 | 69.27% |
| 2024 | 588 | 428 | 160 | 72.79% |
| 2025 | 610 | 450 | 160 | 73.77% |

## By position

| Position | Rows | Exact | Mismatch | Conformance |
| --- | ---: | ---: | ---: | ---: |
| QB | 404 | 174 | 230 | 43.07% |
| RB | 771 | 533 | 238 | 69.13% |
| TE | 650 | 548 | 102 | 84.31% |
| WR | 1191 | 931 | 260 | 78.17% |

## Completeness and week scope

The pinned 2021–2025 population covers the season pairs needed to inspect 2022→2023, 2023→2024, and 2024→2025 candidate temporal origins. This is season-presence/scoring evidence only; it does not define or accept a Forecast split.

Every row carries one explicit completeness state. The source methodology defines `full_season` as 15–18 observed REG week numbers, `partial_season` as 2–14, and `single_week` as 1. Week 18 is included. A count of zero is `missing`; an invalid count or count/status conflict is `irreconcilable`.

The promoted rows expose only `weeks_observed`, not individual week numbers. This evidence therefore binds the promoted REG declaration and valid 0–18 count range without pretending to reconstruct weekly rows. Absence of a stat-line week is not interpreted as injury, inactivity, or a missed game.

| Completeness | Rows |
| --- | ---: |
| `full_season` | 855 |
| `partial_season` | 1907 |
| `single_week` | 254 |
| `missing` | 0 |
| `irreconcilable` | 0 |

## Source-total semantics

The promoted builder declares `season_ppr` to be a direct passthrough of `nflreadpy.load_player_stats(summary_level='reg').fantasy_points_ppr`. Current official nflfastR producer code corroborates that its PPR total includes the candidate profile plus special-teams touchdowns, passing/rushing/receiving two-point conversions, and sack/rushing/receiving fumbles lost. The producer code is pinned here only as semantic corroboration: [`R/aggregate_game_stats.R` at `0489133d85c5f11682572d9436c4a7b371a789aa`](https://github.com/nflverse/nflfastR/blob/0489133d85c5f11682572d9436c4a7b371a789aa/R/aggregate_game_stats.R), blob `c54e875f9898ef9a4bbd5e7dd879c6e3c2abbc0a`.

The promoted artifact did not pin the exact historical nflreadpy/nflverse release used for retrieval, so this report does not claim that the current producer commit is that historical release. The promoted source bytes, their promotion manifest, and their original source-candidate hash are the authoritative inputs to this reconciliation.

All 830 nonzero differences are integer multiples of two, with signed `derived - source` range `-12.00` to `14.00`. This is consistent with the corroborated out-of-profile families, but the promoted rows omit those families, so no per-row attribution is made.

## Aggregation, missingness, and numeric rules

- Component-derived season scoring has precedence for identifying the exact candidate profile.
- Promoted `season_ppr` remains a source comparator and is never rewritten.
- No weekly scoring rows are present in the promoted source; no weekly sum is fabricated or substituted.
- Decimal arithmetic is exact from JSON numeric text. Published values use two decimals and `ROUND_HALF_UP`; independently normalized totals must have a zero-cent delta to reconcile. The v1 tolerance is 0.00.
- Present numeric zero is genuine zero. Missing/null is unavailable and never zero-filled.

## Output packet

- Contract: `docs/contracts/player-season-coverage-v0-generic-ppr-reconciliation-v1.json`
- Per-row evidence: `exports/candidates/scoring_reconciliation/player_season_coverage_v0_generic_ppr_reconciliation_v1.json`
- Discrepancy ledger: `exports/candidates/scoring_reconciliation/player_season_coverage_v0_generic_ppr_discrepancies_v1.json`
- Missingness ledger: `exports/candidates/scoring_reconciliation/player_season_coverage_v0_generic_ppr_missingness_v1.json`
- Evidence manifest: `data/manifests/player_season_coverage_v0_generic_ppr_reconciliation_v1.manifest.json`

## Authority boundary

This packet does not promote any artifact, change the promoted source, authorize a Forecast target, select a cutoff, train/freeze a model, execute a forward run, or emit rankings/advice. Forecast admission and all downstream policy remain operator decisions.
