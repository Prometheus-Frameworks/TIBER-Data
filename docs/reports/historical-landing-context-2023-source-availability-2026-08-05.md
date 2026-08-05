# Historical landing-context 2023 source availability and gap report

Status: design/evidence report only. It makes no ownership or terminal decision and authorizes no promotion.

## Answer first

The bounded repository audit found only two usable evidence lanes: the #237 exact-GSIS identity/draft projection and individual 2022 REG player-season usage rows. The latter remain unadmitted because their immutable lineage has no contemporaneous release or revision timestamp. Complete team distributions, returning/depth inventory, vacated opportunity, transactions, quarterback/coaching state, 2022 team environment, and injury/availability remain explicit gaps.

## Required source families

| Family | Bounded status | Admitted scope |
| --- | --- | --- |
| `prior_season_targets_shares_air_yards_and_receiving` | `player_rows_available_but_cutoff_timing_and_team_completeness_unproven` | none_in_this_design_evidence_candidate |
| `vacated_targets_and_receiving_opportunity` | `blocked_no_cutoff_transaction_feed_or_team_split_usage` | none_all_totals_null |
| `draft_day_roster_or_depth_chart` | `unavailable_no_april_2023_cutoff_historical_roster_artifact` | none |
| `offseason_arrivals_and_departures` | `unavailable_no_admissible_april_2023_cutoff_bounded_transaction_feed` | none |
| `quarterback_state` | `unavailable_production_does_not_establish_cutoff_state` | none |
| `coaching_and_play_caller_state` | `unavailable_no_cutoff_bounded_source` | none |
| `prior_season_offense_quality_volume_personnel_and_scoring` | `unavailable_no_2022_team_environment_artifact` | none |
| `injury_and_availability` | `unavailable_no_cutoff_bounded_availability_source` | none |
| `draft_results_and_team_assignment` | `bounded_candidate_available_via_issue_237_exact_gsis_projection` | three pilot identities, overall picks, and draft teams |

## Pilot evidence

The subtotals below are diagnostics over source rows whose full-season `teams` value contains exactly one team. They are not complete team totals and are not admitted to the reconstructed layer.

| Team | Raw 2022 code | Binding | Rows | Target subtotal | Target-share sum | Air-yards-share sum | Multi-team exclusions |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| BAL | `BAL` | `exact_code_match` | 15 | 447 | 0.9614 | 0.9398 | 2 |
| IND | `IND` | `exact_code_match` | 14 | 546 | 0.9430 | 0.9549 | 2 |
| LAR | `LA` | `blocked_2022_alias_outside_issue_237_supported_scope` | 17 | 516 | 0.9982 | 0.9868 | 0 |

`LA` is preserved for the 2022 Rams source rows. #237 authorizes its directed `LA → LAR` candidate rule only for source seasons 2023–2025, so the LAR prior-season team binding remains blocked here.

## Hindsight and aggregation firewall

- No #237 later-season team history or Forecast metadata is projected.
- No 2022 player-season row is treated as a returning roster/depth fact.
- Multi-team full-season rows are excluded from the diagnostic team subtotals.
- Complete team totals and vacated opportunity remain null; rows are never renormalized.
- The frozen Puka comparison reference's June 2023 Kupp source is explicitly excluded.
- End-of-day cutoffs are configured proxies; same-day external facts require sequence evidence and none are admitted by these pilots.

## Bounded negative inventory

| Claimed family | Path | Observed scope | April 2023 use | SHA-256 |
| --- | --- | --- | --- | --- |
| `draft_day_roster` | `exports/promoted/nfl/roster_player_team_map_v1.json` | 2025 offline fixture | `not_admissible_wrong_season_and_not_historical_as_of` | `bea7961e8319ae5928b22de0a04b9969c3d4685819d9306187215895ddc33a3c` |
| `draft_day_roster` | `data/processed/evidence/roster_player_team_map_2025.source_backed.json` | 2025 weekly source-backed roster rows | `not_admissible_wrong_season` | `6c0436a4da7b7d54ee58454ad912be2571f5695457d107ed37a467b79d0cb38a` |
| `prior_season_offense_quality` | `exports/promoted/nfl/team_offense_summary_v1.json` | 2025 offline fixture | `not_admissible_wrong_season` | `8850fb7e395a2115bf48d2946e97743536b5dacc338abb0fa432e988a1adfd1d` |
| `prior_season_pace_and_pass_environment` | `exports/promoted/nfl/team_pace_pass_environment_v1.json` | 2025 offline fixture | `not_admissible_wrong_season` | `e4f61b024c5dd53fadf1c943add73e57435724d5ff694b0ee0dfa402acc5fbcb` |
| `prior_season_weekly_team_context` | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json` | 2024 governed real data with explicit governed markers in candidate path | `not_admissible_wrong_season` | `2aed00e68c1620af10d2ea4350104f7e183ff6ee050f5d385a503ef027281de9` |
| `prior_season_personnel_usage` | `exports/candidates/formation_summary/formation_summary_v0_2024_real_source_candidate.json` | 2024 candidate | `not_admissible_wrong_season_and_not_promoted` | `7278133e4f0f65a7f35e76c686d33c750f8afd6f09bf50938b0eade78cc85def` |
| `injury_and_availability` | `exports/promoted/nfl/player_weekly_usage_v1.json` | 2025 usage fixture; no historical availability state | `not_admissible_wrong_season_and_wrong_semantics` | `425db119ed6b6d78bead9a638a4295703bf316547c4b76c0022b0de765804260` |
| `draft_results` | `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json` | 2026 only | `not_admissible_wrong_draft_class` | `c6ccb76085ae5726f92c543170f151a4d183920b6f61ec4de59a1883f7d7863a` |
| `offseason_arrivals_and_departures` | `exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl` | 2026 fixture-only ownership event scaffold in promoted path | `not_admissible_wrong_season_and_fixture_only` | `6aee8de0d174371b42c82d548353ded0475d9383493d79bb171fd2adb2ebd53e` |
| `draft_day_roster` | `exports/promoted/player_ownership/player_ownership_latest.json` | 2026 current-state provisional artifact sourced from 2025 roster weeks | `not_admissible_wrong_cutoff_and_not_historical_as_of` | `179a20410dac7d4b148966b2e577971ca4cad2da859cdaa397fde76461d5ccb7` |
| `offseason_arrivals_and_departures_contract_only` | `schemas/player_ownership_change_event_v0.schema.json` | contract only; no April 2023 event rows | `no_fact_rows_available` | `bb21ac41b8f965acc9205a136c63b24687034fca2e99431cd8a537775cb5c6da` |
| `draft_day_roster_contract_only` | `schemas/roster_snapshot_v0.schema.json` | contract only; no April 2023 artifact | `no_fact_rows_available` | `b19cde6d383a331c12eba154f9f9408e628dc99eb08591cac6c2cbf6ca12f22a` |
| `draft_day_roster_contract_only` | `docs/contracts/roster-snapshot-v0.md` | contract only; no April 2023 artifact | `no_fact_rows_available` | `ad92862c0908bb40f20dd2d37f514a428b38eda2e6c7346294facd097d748c93` |

## Open operator questions

- Which repository owns cutoff-bounded roster, quarterback, coaching, and opportunity interpretation?
- What immutable historical transaction, roster, coaching, and injury sources are admissible?
- Does a later-retrieved prior-season record with no source revision timestamp qualify as known by the April 2023 cutoff?
- Should a separately evidenced candidate-only 2022 LA-to-LAR rule be admitted?
- What source can allocate full-season usage across teams for multi-team players?
- Is an end-of-draft-day cutoff proxy sufficient, or must exact pick timestamps be sourced?
- What durable non-name edge will connect GSIS to the governed TIBER canonical player ID namespace?

The cross-repo ownership split and all terminal decisions are intentionally reserved for the operator.
