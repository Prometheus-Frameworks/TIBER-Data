# Data #276 — bounded Week 3 candidate execution

Implementation: `e1e92078c626b9e2e502e927ba0de79afd26f451`. Intake/builders unchanged.
Player/team and schedule support commit: `2b58e2c22ccd2430041afcfbd143b057830878f0`.
Candidate SHA-256: `f3366ac1c2192641c6e94ba7c756ed2e12ba73b37550619ae143deaeab9f9902`.

Status: `candidate_needs_review`; `consumer_admitted=false`; `game_finality=unknown`; `full_week_final=false`.

Observed and scheduled game IDs match across 16 games; missing and unexpected lists are empty. 1,113 resolved player rows, 32 team rows and one separate unattributed ATL observation. 24 receiving-air-yard conflicts are preserved; other supported metric reconciliation matches. No missing required columns or null supported observed metric values.

## Exact game membership

- `2026_03_ARI_SF`
- `2026_03_ATL_GB`
- `2026_03_BAL_DAL`
- `2026_03_CAR_CLE`
- `2026_03_CIN_PIT`
- `2026_03_HOU_IND`
- `2026_03_KC_MIA`
- `2026_03_LAC_BUF`
- `2026_03_LA_DEN`
- `2026_03_LV_NO`
- `2026_03_MIN_TB`
- `2026_03_NE_JAX`
- `2026_03_NYJ_DET`
- `2026_03_PHI_CHI`
- `2026_03_SEA_WAS`
- `2026_03_TEN_NYG`

## Source-ID-bound player coverage

| Player | nflverse player_id | Raw team | Game | CSV row | Carries | Targets | Receptions | Receiving yards |
|---|---|---|---|---:|---:|---:|---:|---:|
| Josh Downs | 00-0038997 | IND | 2026_03_HOU_IND | 2880 | 0 | 11 | 5 | 77 |
| Braelon Allen | 00-0039794 | NYJ | 2026_03_NYJ_DET | 3004 | 4 | 3 | 3 | 3 |
| DK Metcalf | 00-0035640 | PIT | 2026_03_CIN_PIT | 2475 | 0 | 5 | 3 | 31 |
| Chase Brown | 00-0038597 | CIN | 2026_03_CIN_PIT | 2843 | 13 | 2 | 2 | 8 |
| Tre Harris | 00-0040727 | LAC | 2026_03_LAC_BUF | 3202 | 0 | 7 | 6 | 76 |
| Kalif Raymond | 00-0032464 | CHI | 2026_03_PHI_CHI | 2286 | 0 | 7 | 6 | 90 |

Names label exact source-ID records; no canonical identity admission or current-team rewrite is implied.

## Verification and limitations

40 existing focused tests passed (22 publication, 18 facts), using unittest. Exact committed-support replay equals candidate bytes; digest and terminal flags match; repeat publication is unchanged. The negative missing-Git-object test emits an expected fatal diagnostic and passes. pytest is unavailable; no dependency was installed. Full suite not run.

Raw source receipts, exact asset identities, timestamps, implementation blobs, all conflicts and missingness counts are in the paired JSON. The existing master license URL returned HTTP 200 and matched the audited hash. Source intake used fresh before/after metadata and actual size/digest checks.

Independent exact-head review is pending; a request is not a completed review. No source admission, promotion, merge, deployment, runtime change or downstream execution. Routes, snaps and charting remain unavailable; these weekly rows do not establish Allen post-Hall snaps/routes.

Active task: Data artifact/provenance/downstream handoff. Files touched: additive raw snapshots, Week 3 candidate revision/index, this paired audit and HANDOFF.md. What is now true: the exact candidate is reproducible and bounded. Missing: independent exact-head review and any separately governed admission/consumer decisions. Must not assume: matched schedule membership certifies finality or player absence means zero. Audit-trigger status: builder mechanical checks complete; independent review pending.

CLI push had no HTTPS credentials. Authenticated GitHub publication reproduced the validated support tree exactly, then the candidate was rebuilt against the published support commit. Earlier local support/candidate commits remain on the original local branch; their bytes were not overwritten. Published candidate identity is the one above.
