# Current player-state source readiness audit — 2026-08-10

> Status: corrected exact-ref source/readiness audit; not a contract, ingest, artifact, or promotion  
> Tracking issue: TIBER-Data #246  
> TIBER-Data ref: 44296134a178f9d53fd7eda01a94548e76160d29  
> Evidence cutoff: 2026-08-10

## Answer first

TIBER-Data does not have a governed, full-universe, current 2026 source for roster membership, ownership status, transactions, practice participation, official game designations, or gameday inactives.

The existing contracts and artifacts are foundations, not current truth. Roster membership, ownership state, transaction events, practice participation, game designations, gameday inactives, and reserve states must remain separate lanes. Downstream availability, injury forecasts, and conditional replacement roles must not be written back as source evidence.

No audited source is ready for a candidate build. Official NFL and Arizona Cardinals surfaces are authoritative only for their narrow published assertions, while their current terms do not grant automated collection for a TIBER database. The nflverse roster path remains a possible later candidate only after source rights, immutable bytes, clocks, population, identity, and correction lineage are admitted. The nflverse injury and trades paths are rejected for current 2026 use.

This audit authorizes no source access, collection, ingestion, candidate row, recommendation execution, promotion, or consumer activation.

## Task class and boundary

This is a provenance/source audit plus an external-dataset audit under AGENTS.md. It inspected existing TIBER artifacts and pinned public code, dictionaries, schedules, official pages, and terms. No external dataset bytes or player rows were downloaded or committed. Mutable page observations were manual readiness observations only and are not source receipts.

Qualification terms used below:

- unprobed: the audit did not inspect source row bytes or field population.
- unavailable: the source or field does not exist for the current scope.
- unbound: a field or behavior may exist, but no governed contract binds it.
- not applicable: the concept does not apply to the audit-only observation.

## Pinned evidence

| Repository | Exact ref | Inspected purpose |
| --- | --- | --- |
| Prometheus-Frameworks/TIBER-Data | 44296134a178f9d53fd7eda01a94548e76160d29 | current artifacts, contracts, and governance |
| nflverse/nflreadpy | 66bb305e634ba815466749249d07b5c6e9268db3 | ["src/nflreadpy/load_rosters.py","src/nflreadpy/load_rosters_weekly.py","src/nflreadpy/load_injuries.py","src/nflreadpy/load_trades.py","src/nflreadpy/load_players.py","pyproject.toml","LICENSE.md"] |
| nflverse/nflreadr | d072c08492067b578f27e562b6cc9c9e3b8589c3 | ["R/load_rosters.R","R/load_rosters_weekly.R","R/load_injuries.R","R/load_trades.R","vignettes/articles/nflverse_data_schedule.Rmd","data-raw/dictionary_roster_status.csv","data-raw/dictionary_rosters.csv","DESCRIPTION"] |
| nflverse/nflverse-rosters | 644ead141e8c847da7771c513b980c21d9feba7b | ["R/rosters.R","exec/update-injuries.R",".github/workflows/update_rosters.yaml",".github/workflows/update_injuries.yaml","README.md","DESCRIPTION","LICENSE"] |

## Corrected existing TIBER inventory

| Artifact | Exact blob | Machine-checked population and clocks | Safe interpretation |
| --- | --- | --- | --- |
| exports/promoted/player_ownership/player_ownership_latest.json | 08ade3596a912df4a84cfa2872f5c9e4ad7bb3bb | Generated 2026-05-24T14:10:55Z; 27 rows total. Source breakdown is 19 nflreadpy weekly-roster active rows observed/verified 2026-01-05 through 2026-02-09; 1 Tee Higgins fixture-only active row observed/verified 2026-05-23T13:00:00Z; and 7 unsigned-draft-pick rows observed/verified 2026-04-25. All 27 source_updated_at values are null. | The 19 weekly rows are stale partial observations; the Tee row is a fixture; the seven draft rows are not signed-roster facts. The file is not a current roster universe. |
| data/processed/evidence/roster_player_team_map_2025.source_backed.json | af2d5ecc7095bc2a27cbaaad482a6e5952adb51a | 14,348 player-week rows, 971 players, 2025 weeks 1–22; all 14,348 active_roster_status values are unknown. | Historical team membership only. |
| exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl | b2c23975a555411e9719e45e066468130be1ca70 | One provisional Tee Higgins team-change event with source fixture_demonstration_only. | Contract fixture only, not current transaction truth. |
| docs/specs/active-player-detection-v0-source-boundary.json | 02b9cc890d6c856bfce78dd2c35054f925d4c92e | Spec only. | Not a schema, dataset, validator, or implementation-ready contract. |
| schemas/player_ownership_v0.schema.json | a460476259116056d6fa3c970429b12d7b773d73 | Shape and vocabulary only. | Does not supply observations. |
| schemas/player_ownership_change_event_v0.schema.json | c2e6f82b16550c0042b57ca1a5840dd264512dd5 | Event shape only. | Does not supply transactions. |
| docs/contracts/roster-snapshot-v0.md | 8b1ed2d7e2402da63793c6a76d924ef32248c6c8 | Contract scaffold with illustrative examples. | No current roster truth. |
| exports/candidates/population_census/bounded_2026_population_census_v0.json | 07cdc8fd6c855642091e96b4feb6382c4493b3b9 | 658 rows: 610 2025 stat-bearing players plus 48 rookies. | Bounded candidate population, not a complete current active-roster universe. |

The ownership totals above were derived from the pinned machine artifact itself. The previous prose incorrectly grouped the Tee fixture with the 19 weekly-roster observations; that error is corrected here and in the JSON companion.

## Exact official-page and terms observations

- NFL transactions: https://www.nfl.com/transactions/
- NFL injuries: https://www.nfl.com/injuries/
- Historical NFL injury-report schema example: https://www.nfl.com/injuries/league/2025/reg5
- NFL gameday-inactives article example: https://www.nfl.com/news/week-18-saturday-inactives-cleveland-browns-at-baltimore-ravens-cincinnati-bengals-at-pittsburgh-steelers
- Arizona Cardinals roster: https://www.azcardinals.com/team/players-roster/
- Arizona Cardinals 2026 transactions: https://www.azcardinals.com/team/transactions/2026
- Arizona Cardinals injury report: https://www.azcardinals.com/team/injury-report/
- Pinned Arizona Cardinals offseason observation: https://www.azcardinals.com/team/injury-report/offseason (observed “See You Next Season” and a statement that the first 2026 report will be released before the regular-season opener).

No NFL.com Arizona roster URL was inspected or asserted. The roster observation is limited to the exact Arizona Cardinals URL above.

The NFL terms page at https://www.nfl.com/legal/terms/ names NFL Enterprises, LLC as the service operator and is marked updated May 16, 2024. Its material use phrases are “individual non-commercial and informational purposes only” and “express prior written consent.” The Arizona terms page at https://www.azcardinals.com/about-us/terms-conditions names Arizona Cardinals Football Club LLC and is marked revised October 22, 2024; it uses the same material phrases. In both cases, systematic retrieval for a collection, database, or directory is outside the observed permission. This is a rights blocker, not legal advice.

## Complete source qualification matrix

Every source row below explicitly records identity keys, team keys, five clocks, cadence, revision behavior, population, missing semantics, and correction lineage. A documented field is not a governed binding; values remain unprobed, unavailable, or unbound where this audit did not establish them.

| Source | Class / scope | Identity and team keys | Clocks: effective; published; updated; retrieved; generated | Cadence / revisions | Population / missing semantics / correction lineage | Readiness |
| --- | --- | --- | --- | --- | --- | --- |
| nfl_transactions_page | external_candidate / league_transaction_publication_filtered_by_year_month_category | identity={"observed":"player_display_identity_present_on_surface","canonical_binding":"unprobed"}; team={"observed":"transaction_team_labels_present_when_published","canonical_binding":"unprobed"} | event_date_visible_but_machine_contract_unbound; unavailable_on_index_observation; unavailable_on_index_observation; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | unpublished_or_unprobed / unbound | population=unprobed_current_view_can_be_empty; missing=empty_view_ambiguous_filter_offseason_no_events_or_failure; correction=unbound_no_immutable_receipt_or_supersession_key | rights_and_contract_blocked; authorized=false |
| nfl_injury_reports_page | external_candidate / league_practice_participation_and_game_designation_publication | identity={"observed":"player_display_name_and_position","canonical_binding":"unprobed"}; team={"observed":"team_grouping","canonical_binding":"unprobed"} | practice_date_or_game_week_visible_but_machine_contract_unbound; unavailable_in_inspected_interface; unavailable_in_inspected_interface; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | seasonal_report_schedule_unbound / unbound | population=unprobed_not_yet_published_is_possible; missing=not_listed_is_not_full_participation_healthy_or_active; correction=unbound_no_report_iteration_or_supersession_contract | rights_and_contract_blocked; authorized=false |
| nfl_gameday_inactives_articles | external_candidate / article_scoped_official_inactive_lists_for_named_games | identity={"observed":"player_display_names","canonical_binding":"unprobed"}; team={"observed":"article_team_labels","canonical_binding":"unprobed"} | game_scope_and_kickoff_external_to_article_machine_contract_unbound; article_clock_observed; article_updated_clock_observed; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | game_day_article_cadence_unbound / article_can_update_but_supersession_contract_unbound | population=no_stable_all_game_registry_proven; missing=absence_not_active_without_complete_roster_and_complete_official_list; correction=unbound_no_registry_receipt_or_article_revision_chain | rights_registry_and_contract_blocked; authorized=false |
| cardinals_roster_page | external_candidate / Arizona_team_roster_page_and_source_group_labels | identity={"observed":"player_display_identity","canonical_binding":"unprobed"}; team={"observed":"Arizona_Cardinals_fixed_page_scope","canonical_binding":"unbound"} | unavailable_no_source_as_of_observed; unavailable_in_inspected_interface; unavailable_in_inspected_interface; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | unpublished_or_unprobed / mutable_page_revision_behavior_unbound | population=one_team_only_group_completeness_unprobed; missing=missing_player_or_group_is_unknown_not_released; correction=unbound_no_immutable_snapshot_or_supersession_key | rights_clock_population_and_identity_blocked; authorized=false |
| cardinals_transactions_page | external_candidate / Arizona_team_authored_dated_transaction_statements | identity={"observed":"player_display_identity_in_statement","canonical_binding":"unprobed"}; team={"observed":"Arizona_Cardinals_fixed_page_scope_and_named_counterparty_when_stated","canonical_binding":"unbound"} | transaction_date_visible_but_time_semantics_unbound; unavailable_in_inspected_interface; unavailable_in_inspected_interface; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | event_driven_but_publication_sla_unbound / mutable_page_revision_behavior_unbound | population=one_team_only_event_completeness_unprobed; missing=no_statement_is_not_no_transaction; correction=unbound_no_event_revision_or_retraction_contract | rights_clock_population_and_identity_blocked; authorized=false |
| cardinals_injury_report_page | external_candidate / Arizona_practice_participation_and_game_designation_publication_when_applicable | identity={"observed":"player_display_identity_when_report_published","canonical_binding":"unprobed"}; team={"observed":"Arizona_Cardinals_fixed_page_scope","canonical_binding":"unbound"} | practice_date_or_game_scope_unavailable_in_offseason_observation; unavailable_in_offseason_observation; unavailable_in_offseason_observation; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | seasonal_reports_not_yet_published_currently_publication_sla_unbound / report_iteration_and_revision_behavior_unbound | population=one_team_only_current_offseason_population_unavailable; missing=not_yet_published_is_not_no_injury_not_listed_is_not_healthy; correction=unbound_no_report_iteration_or_supersession_contract | rights_clock_population_and_identity_blocked; authorized=false |
| nflverse_rosters_ngs_shield | external_candidate / weekly_NGS_roster_when_available_with_Shield_season_roster_fallback | identity={"documented":["gsis_id","provider_ids"],"population_2026":"unprobed","canonical_binding":"unbound"}; team={"documented":["team"],"population_2026":"unprobed","canonical_binding":"unbound"} | season_week_and_game_type_documented_but_2026_bytes_unprobed; unavailable_or_unbound; unavailable_or_unbound; unavailable_no_2026_source_bytes_retrieved; producer_clock_unbound_at_row_level | daily_0700_utc_loader_schedule / mutable_release_revision_and_replacement_behavior_unbound | population=2026_rows_teams_groups_duplicates_and_fallback_population_unprobed; missing=empty_NGS_can_trigger_Shield_fallback_so_empty_and_missing_require_row_visible_source_lineage; correction=unbound_requires_byte_digest_receipt_append_only_supersession_and_row_source_family | source_rights_contract_population_identity_and_clock_followup; authorized=false |
| nflverse_injuries | rejected / historical_weekly_injury_and_practice_reports_through_2024_only | identity={"historical_documentation":"unprobed_for_current_contract","current_2026":"unavailable"}; team={"historical_documentation":"unprobed_for_current_contract","current_2026":"unavailable"} | unavailable_current_2026; unavailable_current_2026; unavailable_current_2026; unavailable_no_source_bytes_retrieved; unavailable_current_2026 | unavailable_current_2026_source_died_after_2024 / unavailable_current_2026 | population=zero_current_2026_by_documented_source_end; missing=absence_after_2024_is_source_unavailable_not_no_injury; correction=unavailable_current_2026 | rejected_no_current_source; authorized=false |
| nflverse_trades_lee_sharpe_pfr | rejected / historical_trades_only_not_full_transaction_wire | identity={"documented":"unprobed","canonical_binding":"unbound"}; team={"documented":"unprobed","canonical_binding":"unbound"} | historical_trade_date_field_expected_but_unprobed; unavailable_or_unbound; unavailable_or_unbound; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | unprobed_and_not_current_wire / unbound | population=trades_only_excludes_signings_waivers_releases_reserve_and_practice_squad_changes; missing=missing_event_cannot_mean_no_transaction; correction=unbound | rejected_for_current_transaction_lane; authorized=false |
| nflverse_player_master | schema_reference_only / identity_and_provider_id_vocabulary_only | identity={"documented":"provider_identity_candidates","population":"unprobed","canonical_binding":"unbound"}; team={"documented":"possible_team_or_status_fields_not_admitted_as_current","canonical_binding":"prohibited_for_current_state"} | unprobed; unprobed; unprobed; unavailable_no_source_bytes_retrieved; not_applicable_audit_only | unprobed / unbound | population=unprobed; missing=player_master_presence_or_absence_is_not_roster_membership; correction=unbound | schema_reference_only_not_current_truth; authorized=false |

The nflverse injury source is classified rejected because the documented upstream ended after 2024 and therefore supplies no current 2026 injury evidence. The nflverse trades source is classified rejected for the current transaction lane because it is historical trades only, not a complete current transaction wire. Neither is an evaluation benchmark, so benchmark_reference_only would be misleading. nflverse player master remains schema_reference_only for identity vocabulary and cannot supply current membership.

The MIT licenses on loader and producer code do not grant rights to the upstream data. For nflverse injuries and nflverse player master, upstream-data retention and redistribution permissions are explicitly unbound and therefore fail closed.

## Lane contracts, identity, and unresolved behavior

| Lane | Grain and clocks | Identity contract | Unresolved behavior |
| --- | --- | --- | --- |
| roster_membership_snapshot | grain=player_team_source_snapshot; clocks=["source_effective_or_as_of_if_exposed","published_or_updated_if_exposed","retrieved_at","generated_at","valid_window"] | target=gsis_id; source_keys=["source_player_key","source_team_key","source_ref"]; team=versioned_source_team_to_canonical_team_mapping | retain_source_row_with_resolution_status_unresolved; do_not_join_or_promote_as_canonical |
| ownership_state | grain=player_state_interval; clocks=["valid_from","valid_to","last_verified_at","retrieved_at","generated_at"] | target=gsis_id; source_keys=["supporting_observation_player_key","supporting_team_key"]; team=canonical_team_required_when_team_bearing | do_not_create_or_extend_canonical_state_interval; preserve_supporting_record_separately |
| transaction_event | grain=one_source_assertion_about_one_event; clocks=["effective_at_or_date","published_at","updated_at","retrieved_at","detected_or_generated_at"] | target=gsis_id_per_participant; source_keys=["raw_player_identity","raw_from_team_if_stated","raw_to_team_if_stated"]; team=resolve_each_team_independently | preserve_raw_event_and_participant_resolution_failures; do_not_merge_events_or_mutate_ownership |
| practice_participation | grain=player_team_game_practice_date_report_iteration; clocks=["practice_date","published_at","updated_at","retrieved_at","generated_at"] | target=gsis_id; source_keys=["raw_player_identity","raw_team_identity","source_game_key"]; team=canonical_team_and_game_mapping_required | preserve_source_observation_as_unresolved; no_availability_or_health_inference |
| official_game_designation | grain=player_team_game_report_iteration; clocks=["published_at","updated_at","retrieved_at","generated_at"] | target=gsis_id; source_keys=["raw_player_identity","raw_team_identity","source_game_key"]; team=canonical_team_and_game_mapping_required | preserve_source_observation_as_unresolved; no_active_or_inactive_inference |
| gameday_inactive | grain=player_team_game_official_publication; clocks=["kickoff","published_at","updated_at","retrieved_at","generated_at"] | target=gsis_id; source_keys=["raw_player_identity","raw_team_identity","source_game_key"]; team=canonical_team_and_game_mapping_required | preserve_source_listing_as_unresolved; no_absence_based_active_inference |
| reserve_ir_pup_nfi_state | grain=player_roster_state_interval_and_or_transaction_event; clocks=["effective_at","published_at","updated_at","retrieved_at","generated_at","validity_interval"] | target=gsis_id; source_keys=["raw_player_identity","raw_team_identity","raw_roster_state"]; team=canonical_team_mapping_required_for_team_bound_state | preserve_raw_state_or_event; no_ownership_enum_collapse |
| inferred_availability | grain=derived_interpretation; clocks=["inference_as_of","input_cutoffs"] | target=gsis_id; source_keys=["all_governed_input_identity_keys"]; team=inherits_resolved_source_inputs | emit_no_derived_availability_for_unresolved_input_identity |
| forecast_injury_probability | grain=future_distribution; clocks=["forecast_origin","input_cutoff"] | target=gsis_id; source_keys=["all_approved_input_identity_keys"]; team=inherits_validated_forecast_inputs | emit_no_player_forecast_for_unresolved_identity |
| conditional_replacement_role | grain=scenario_role_interpretation; clocks=["scenario_origin","input_cutoff"] | target=gsis_id_for_subject_and_replacement; source_keys=["all_role_roster_injury_and_deployment_identity_keys"]; team=canonical_team_and_scenario_scope_required | emit_no_replacement_assignment_or_inherited_share |

Across all source lanes, raw source identity and team strings remain visible. Name-only matching may not silently create a canonical player, merge two events, extend an ownership interval, or emit an availability, forecast, or replacement-role result. Candidate and promotion gates require explicit identity-resolution counts and visible unresolved rows.

## nflverse roster-status compatibility

| Raw code | Mapping type | Ownership value | Required handling |
| --- | --- | --- | --- |
| ACT | direct | active_roster | direct_membership_only_not_gameday_active |
| DEV | direct | practice_squad | direct_when_current |
| RET | direct | retired | direct_when_current |
| SUS | direct | suspended | direct_ownership_game_availability_separate |
| UFA | approximate_requires_current_state_evidence | free_agent | approximate_preserve_release_event_and_require_current_state |
| CUT | approximate_requires_current_state_evidence | free_agent | approximate_event_not_timeless_state |
| RFA | prohibited_no_direct_mapping | null | no_safe_direct_map |
| PUP | prohibited_no_direct_mapping | null | distinct_from_injured_reserve |
| RES | prohibited_no_direct_mapping | null | reserve_too_broad_requires_subtype |
| RSN | prohibited_no_direct_mapping | null | nfi_reserve_distinct_from_ir |
| INA | prohibited_no_direct_mapping | null | not_automatically_game_specific_inactive |
| EXE | prohibited_no_direct_mapping | null | commissioners_exempt_no_governed_value |
| E14 | prohibited_no_direct_mapping | null | international_exempt_no_governed_value |
| NWT | prohibited_no_direct_mapping | null | rare_waived_tendency_unknown |
| RSR | prohibited_no_direct_mapping | null | event_like_release_from_ir_current_state_unknown |
| TRC | prohibited_no_direct_mapping | null | practice_squad_release_event_if_semantics_proven |
| TRD | prohibited_no_direct_mapping | null | practice_squad_release_not_trade |
| TRT | prohibited_no_direct_mapping | null | practice_squad_release_event_if_semantics_proven |
| TRL | prohibited_no_direct_mapping | null | historical_undetermined_unknown |

Direct means compatible only with the ownership-membership lane at a proven source as-of time. Approximate mappings require both the event and a current state observation. Prohibited means preserve the raw source status and emit no ownership enum. In particular, TRD is a practice-squad release code in the pinned dictionary, not a trade.

Practice DNP/LP/FP values cannot populate ownership, reserve, gameday-inactive, or forecast fields. Out/Doubtful/Questionable cannot populate roster membership or gameday inactive. A blank or not-listed report state cannot mean active or healthy. Transaction events cannot create indefinite ownership without a later state observation.

## Coverage, clocks, and corrections required before any candidate

A current-facing source must prove all 32 franchises and every enabled lane through a versioned registry. Each entry needs exact URL or release, owner, terms revision, format, expected cadence, seasonal window, expected groups, retrieval and semantic status, last source update, byte digest, identity counts, unresolved rows, and explicit not_applicable, not_yet_published, source_unavailable, parse_failed, partial, stale, and conflict states.

All five clocks must be represented without substitution: source effective/as-of, published, updated, retrieved, and generated. A fresh retrieval or generation time cannot make old source evidence current. Mutable releases require immutable byte digests, append-only receipts, correction detection, and supersession links. Conflicting official assertions remain separate until their scoped clocks establish supersession.

## Fail-closed behavior

- Missing status is unknown, never active or inactive.
- A missing player row is not evidence that the player is out of the league.
- An empty page may mean offseason, not yet published, filter mismatch, or failure.
- Roster membership does not prove gameday participation.
- An injury-report absence does not mean healthy.
- A transaction is an event, not a timeless state.
- A fixture, manual row, candidate, or model output never becomes source truth.
- Depth-chart presence or absence cannot populate roster, injury, or gameday status.
- No injury-contingency workload or share is emitted by this audit.

## Candidate decomposition and ownership

Future source artifacts remain separate: roster membership snapshot, ownership state, transaction event, practice report observation, game designation observation, gameday inactive observation, and only then an explicit compatibility view if still required.

TIBER-Data owns observed state, identity, clocks, provenance, conflicts, and promotion. Team-state interpretation belongs downstream. Conditional replacement roles belong to Role-and-opportunity-model. Future injury distributions belong to TIBER-Forecast. FORGE may consume approved outputs but is not a source-of-truth owner. Age-Curve intelligence may contribute separately validated lifecycle context, never current roster or injury truth.

## Unauthorized next steps

All recommendations below have authorized=false in the machine companion:

- A single immutable 2026 nflverse full-league roster-membership release may be audited later only after upstream rights, exact bytes, row-level NGS/Shield lineage, identity, clocks, missingness, correction, and determinism gates are approved.
- Official web work requires written permission or a licensed feed; this audit does not authorize scraping.
- A replacement current practice/injury source requires a new audit issue before any access or ingestion.

## Current blockers

- official_web_systematic_retrieval_rights_blocked
- nflverse_ngs_shield_upstream_data_rights_not_admitted
- no_immutable_2026_roster_bytes_or_receipt
- no_current_32_team_population_or_identity_coverage
- no_current_full_transaction_wire
- nflverse_injury_source_unavailable_after_2024
- no_replacement_practice_or_injury_source
- no_stable_current_gameday_inactives_registry
- source_effective_publication_update_retrieval_generation_revision_and_supersession_contracts_unbound
- lane_contracts_identity_resolution_and_validators_not_implemented

## Terminal decision

current_player_state_v0_requires_source_or_contract_followup

Independent audit is required before merge consideration. This draft remains documentation-only and authorizes no implementation or promotion.
