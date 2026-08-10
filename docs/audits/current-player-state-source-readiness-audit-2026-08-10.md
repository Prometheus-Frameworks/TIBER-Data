# Current player-state source readiness audit — 2026-08-10

> **Status:** exact-ref source/readiness audit; not a contract, ingest, artifact, or promotion  
> **Tracking issue:** TIBER-Data #246  
> **TIBER-Data ref:** `44296134a178f9d53fd7eda01a94548e76160d29`  
> **Evidence cutoff:** 2026-08-10

## Answer first

TIBER-Data does **not** have a governed, full-universe, current 2026 source for roster membership, ownership status, transactions, practice/injury reports, official game designations, or gameday inactives.

The existing contracts are useful foundations, but the live evidence lanes must remain separate:

- a roster snapshot asserts team membership or a source roster category at an as-of time;
- an ownership state is an interval-valued state supported by observations and events;
- a transaction is an event;
- practice participation and game designation are separate report observations;
- a gameday inactive is game-specific;
- injured reserve is a roster/status fact, not a synonym for an injury-report designation;
- inferred availability, injury probability, and replacement-role inheritance are downstream interpretations.

No audited source family is ready for a candidate build today. Official NFL and official-team web surfaces are authoritative for their narrow published assertions, but their current terms prohibit systematic retrieval or database compilation without express prior written consent. The nflverse roster lane is technically promising but mixes NGS/Shield source paths and has unresolved source-admission, rights, revision-clock, and status-semantic questions. nflverse documents that its injury source died after the 2024 season and that no 2025 data exists. Its trades dataset is historical PFR/Lee Sharpe trade history, not a full transaction wire.

Terminal decision:

```text
current_player_state_v0_requires_source_or_contract_followup
```

No source access, ingestion, or candidate state row is authorized by this audit.

## Task classification and boundary

This is a **provenance/source audit** plus an **external dataset audit** under `AGENTS.md`.

Allowed here:

- inspect existing TIBER contracts, artifacts, builders, and audit records;
- inspect exact public loader/producer code, dictionaries, schedules, and licenses at pinned refs;
- manually inspect official public pages and their terms to qualify assertion scope and access posture;
- define lane boundaries, clocks, missingness, conflicts, candidate decomposition, and the smallest next gate.

Not established here:

- permission to scrape, systematically retrieve, retain, mirror, or redistribute an official web surface;
- an admitted 2026 roster or injury source;
- a complete 32-team player universe;
- a current player-state artifact;
- a ranking, role-contingency claim, injury forecast, or consumer activation.

No external dataset bytes or player rows were downloaded or committed. Mutable web-page observations were inspected only for readiness and rights analysis; they are not frozen source receipts or candidate inputs.

## Pinned evidence ledger

### Repository refs

| Item | Exact ref | Inspected purpose |
| --- | --- | --- |
| TIBER-Data | `44296134a178f9d53fd7eda01a94548e76160d29` | Current contracts, promoted/candidate artifacts, active-detection spec, roster map, ownership event fixture, and governance. |
| nflreadpy | `66bb305e634ba815466749249d07b5c6e9268db3` (`0.1.6`) | `load_rosters`, `load_rosters_weekly`, `load_injuries`, `load_trades`, and `load_players` interfaces. |
| nflreadr | `d072c08492067b578f27e562b6cc9c9e3b8589c3` | Roster/injury/trade loaders, data schedule, roster-status dictionary, and roster dictionary. |
| nflverse-rosters | `644ead141e8c847da7771c513b980c21d9feba7b` | Roster source routing, injury producer, daily workflows, package source/license posture. |

### Official web observations

Observed manually on 2026-08-10; no page bytes were retained:

| Surface | Exact URL | Narrow assertion observed | Rights/access result |
| --- | --- | --- | --- |
| NFL league transactions | `https://www.nfl.com/transactions/` | Year/month/category-filtered transaction publication; an empty current view can occur. | NFL terms block systematic retrieval/database compilation absent express prior written consent. |
| NFL league injury reports | `https://www.nfl.com/injuries/` | Season/week/game/player practice and game-status publication; current offseason/week-zero can be empty or not yet published. | Same NFL terms blocker. |
| Historical NFL injury-report example | `https://www.nfl.com/injuries/league/2025/reg5` | Player, position, injury text, practice status, and game status grouped by game/team. | Schema/reference observation only; not an admitted feed. |
| NFL gameday-inactives example | `https://www.nfl.com/news/week-18-saturday-inactives-cleveland-browns-at-baltimore-ravens-cincinnati-bengals-at-pittsburgh-steelers` | Article-level published/updated clocks and game/team inactive lists. | No stable all-game registry or ingestion permission established. |
| NFL terms | `https://www.nfl.com/legal/terms/` | Updated 2024-05-16; individual informational use only; systematic retrieval/compilation prohibited without express written consent. | Rights blocked for an automated TIBER lane. |
| Cardinals roster | `https://www.azcardinals.com/team/players-roster/` | Official team roster page with source group headings such as Active and player display facts. | Cardinals terms independently block systematic retrieval/compilation without prior written consent. |
| Cardinals transactions | `https://www.azcardinals.com/team/transactions/2026` | Team-authored dated transaction statements. | Event evidence only; rights blocked for automated collection. |
| Cardinals injury report | `https://www.azcardinals.com/team/injury-report/` | Practice-status and game-status vocabularies; offseason page says reports begin before the regular-season opener. | Not-yet-published is distinct from no injury; rights blocked for automated collection. |
| Cardinals terms | `https://www.azcardinals.com/about-us/terms-conditions` | Revised 2024-10-22; individual non-commercial use only and systematic retrieval/compilation prohibited absent written consent. | Rights blocked for an automated TIBER lane. |

Official publication makes a statement authoritative within its scope. It does not, by itself, grant retention, redistribution, or automated collection rights.

## Existing TIBER inventory

| Item at pinned Data ref | Exact blob | Real population/freshness | Safe interpretation |
| --- | --- | --- | --- |
| `exports/promoted/player_ownership/player_ownership_latest.json` | `08ade3596a912df4a84cfa2872f5c9e4ad7bb3bb` | Generated 2026-05-24; 27 players. Twenty are provisional `active_roster` rows sourced from 2025 weekly-roster observations last verified 2026-01-05 through 2026-02-09. Seven are source-verified `unsigned_draft_pick` rows, not signed-roster facts. | Status vocabulary and stale/partial observations only; not a current or complete roster. |
| `data/processed/evidence/roster_player_team_map_2025.source_backed.json` | `af2d5ecc7095bc2a27cbaaad482a6e5952adb51a` | 14,348 player-week rows, 971 players, 2025 weeks 1–22; every `active_roster_status` is `unknown`. | Historical roster membership only; not active/inactive, IR, practice squad, or 2026 state. |
| `exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl` | `b2c23975a555411e9719e45e066468130be1ca70` | One provisional `fixture_demonstration_only` Tee Higgins team-change row. | Contract fixture only, despite its promoted directory; no current transaction truth. |
| `docs/specs/active-player-detection-v0-source-boundary.json` | `02b9cc890d6c856bfce78dd2c35054f925d4c92e` | Spec-only, explicitly not a schema, dataset, validator, or implementation-ready contract. | Provenance/enum foundation only. |
| `schemas/player_ownership_v0.schema.json` | `a460476259116056d6fa3c970429b12d7b773d73` | Governed ownership-state vocabulary and source-reference shape. | Validates shape; does not supply observations. |
| `schemas/player_ownership_change_event_v0.schema.json` | `c2e6f82b16550c0042b57ca1a5840dd264512dd5` | Governed event vocabulary and shape. | Validates event shape; does not supply transactions. |
| `docs/contracts/roster-snapshot-v0.md` | `8b1ed2d7e2402da63793c6a76d924ef32248c6c8` | Time-bounded roster contract scaffold; example rows are illustrative/unverified. | Suitable contract foundation; no current roster truth. |
| `exports/candidates/population_census/bounded_2026_population_census_v0.json` | `07cdc8fd6c855642091e96b4feb6382c4493b3b9` | Candidate-only bounded census: 610 2025 stat-bearing players plus 48 rookies. | Not a complete/current active roster universe; unseen zero-playing-time veterans can be absent. |

Issue #186 and PR #187 remain a contract foundation. They do not turn any row current, and their single proposed `active_status` axis must not be used to collapse the distinct lanes audited here.

## Source and rights matrix

The classification column uses the closed `AGENTS.md` external-source vocabulary.

| Source family | Classification | Assertion scope | Current readiness |
| --- | --- | --- | --- |
| NFL.com roster/transaction/injury/inactive publications | `external_candidate` | Official NFL publication within the page's stated league/game/report scope. | `rights_blocked`: public access exists, but systematic retrieval/compilation is prohibited absent written consent; no immutable API or correction contract identified. |
| Official-team roster/transaction/injury publications | `external_candidate` | Official club assertion for that team/page/report. | `rights_blocked`: Arizona's terms independently prohibit systematic retrieval/compilation; all 32 team terms and page formats would require qualification. |
| nflverse 2016+ weekly/season roster releases | `external_candidate` | NGS weekly roster observations when available; Shield season-roster fallback; source status and identity fields. | Requires source/rights admission, exact 2026 byte receipt, fallback/source-family lineage, status semantics, revision clocks, and population audit. No 2026 rows were accessed here. |
| nflverse injury releases | `benchmark_reference_only` | Historical weekly injury/practice reports through 2024. | Rejected for current use: nflreadr documents that the source died after 2024, no 2025 data exists, and no replacement ETA is known. |
| nflverse trades / Lee Sharpe / PFR | `benchmark_reference_only` | Historical trades. | Not a complete current transaction wire; excludes signings, waivers, releases, reserve-list changes, and many status events. |
| nflverse player master | `schema_reference_only` | Identity and provider-ID candidates. | Identity support only; player-master presence/team/status is not current roster truth. |

The MIT licenses on loader/producer code do not automatically authorize the upstream data.

## nflverse roster source trace

At the pinned `nflverse-rosters` ref:

- seasons 2016+ first attempt weekly NGS roster data;
- if the NGS weekly result is empty, the producer falls back to a Shield season roster;
- roster rows can include `status`, `status_description_abbr`, `gsis_id`, team, position, week/game type, and provider IDs;
- a daily workflow runs at 07:00 UTC;
- the nflreadr schedule likewise says roster data updates daily at 07:00 UTC.

The source trace is useful but not sufficient for governance:

- NGS and Shield are different source assertions and cannot be silently coalesced under one source label;
- an empty NGS result may cause season-level fallback, so weekly completeness must be explicit;
- loader cadence is not a row-level publication/effective/correction clock;
- mutable release URLs require byte digests, retrieval receipts, and append-only supersession;
- raw status values need versioned mapping and non-mapping behavior;
- a current roster page or release can revise history, so current bytes cannot silently rewrite an earlier as-of state.

## Lane-by-lane contract boundary

| Lane | Required grain | Minimum source fields | Required clocks | Missing/conflict behavior |
| --- | --- | --- | --- | --- |
| Roster membership snapshot | player × team × source snapshot | source player ID/name, team, position, source roster group/code, source URL/ref | source effective/as-of if exposed, published/updated if exposed, retrieved, generated, valid window | Missing row is unknown; incomplete team/section coverage makes snapshot partial. |
| Ownership state | player × state interval | ownership enum, team, supporting observations/events, basis | `valid_from`, `valid_to`, last verified, retrieved/generated | May be derived only from governed evidence; event alone cannot create an indefinite state. |
| Transaction event | one source assertion about one event | raw event text/type, player(s), from/to team where stated, source event date/time, source ref | effective date/time, published/updated, retrieved, detected/generated | Preserve duplicate official receipts; unresolved effective time/conflict remains explicit. |
| Practice participation | player × team × game × practice date × report iteration | injury/body-part text, DNP/LP/FP, team/game, report version | practice date, report published/updated, retrieved/generated | Not listed is not FP; later report supersedes only the same report scope. |
| Official game designation | player × team × game × report iteration | Out/Doubtful/Questionable or explicit blank/not-listed state | game, report published/updated, retrieved/generated | Blank is not active; keep each edition and supersession. |
| Gameday inactive | player × team × game × official publication | inactive listing, emergency-third-QB marker if stated, game/team | game kickoff, published/updated, retrieved/generated | Absence can support active only after complete roster and complete official inactive list are both proven; otherwise unknown. |
| Reserve/IR/PUP/NFI status | player × roster-state interval and/or transaction event | exact raw source category and supporting event | effective, published/updated, retrieved/generated, validity interval | Do not infer from body-part or game designation. |
| Inferred availability | downstream interpretation, not a Data source lane | governed inputs plus declared deterministic rule | inference as-of and input cutoffs | Must be labeled derived; absent here. |
| Forecast injury probability | future distribution | approved historical/current inputs | forecast origin/cutoff | Forecast-owned; absent here. |
| Conditional replacement role | scenario/role interpretation | roster, injury, deployment, depth/role evidence | scenario origin/cutoff | Role-and-opportunity-owned; absent here. |

## Status compatibility and non-mappings

### nflverse roster-status codes

| Raw code | Source dictionary meaning | `player_ownership_v0` compatibility | Required handling |
| --- | --- | --- | --- |
| `ACT` | On active roster | `active_roster` | Direct for ownership membership only; does not prove gameday active. |
| `DEV` | Practice squad | `practice_squad` | Direct when source/as-of is current. |
| `RET` | Retired list | `retired` | Direct when current/source-backed. |
| `SUS` | Suspended | `suspended` | Direct ownership status; game availability remains separate. |
| `UFA` | Released / unrestricted free agent | approximate `free_agent` | Preserve release event; resulting current state requires current observation. |
| `CUT` | Cut from roster | approximate `free_agent` | Release is an event; do not create timeless free-agent state without as-of evidence. |
| `RFA` | Rarely used; tends to indicate cut restricted free agent | no safe direct map | Preserve raw code; ownership `unknown` pending semantics/current evidence. |
| `PUP` | Physically Unable to Perform list | no exact governed value | Do not map to `injured_reserve`; preserve distinct raw roster state. |
| `RES` | Reserve list | no safe direct map | Reserve is too broad; require exact subtype. |
| `RSN` | Tends to indicate non-football injured reserve | no exact governed value | Preserve as NFI/reserve observation; do not collapse to IR. |
| `INA` | Under contract but not on active roster, inactive | no direct ownership or gameday map | Preserve raw status; it is not automatically a game-specific inactive. |
| `EXE` | Commissioner's exempt list | no exact governed value | Preserve raw state; ownership `unknown` or future enum extension. |
| `E14` | Exempt international player | no exact governed value | Preserve raw state; do not call active roster without source proof. |
| `NWT` | Rare/waived tendency | no safe direct map | Unknown. |
| `RSR` | Released from injured-reserve list tendency | event-like, no direct map | Preserve event observation; current state unknown. |
| `TRC`, `TRD`, `TRT` | Released from practice squad | event-like, no direct map | Do not interpret `TRD` as “traded”; emit a release event only if exact semantics/effective clock are proven. |
| `TRL` | Historical/undetermined | no map | Unknown. |

### Report and event vocabularies

| Observation | Lane | Must not populate |
| --- | --- | --- |
| DNP / LP / FP | practice participation | ownership, IR, gameday inactive, forecast probability |
| Out / Doubtful / Questionable | official game designation | roster membership, IR, gameday inactive |
| not listed / blank | report coverage state | active, healthy, zero injury |
| official gameday inactive list | gameday status for one game | released, IR, practice squad, future-game status |
| signing / waiver / release / trade / reserve placement | transaction event | indefinite current ownership without a state observation |
| injured reserve / PUP / NFI | roster/reserve state | generic “injured,” game designation, replacement share |

The proposed `active_status` vocabulary from #186 is therefore a compatibility view, not an adequate source record. `active`, `inactive`, `ir`, `practice_squad`, `released`, and `traded` mix gameday, roster, ownership, and event semantics. A future implementation should preserve the separate fields above and derive any compatibility view explicitly, with unsupported cases left `unknown`.

## 32-team and current-universe requirements

A future current-facing lane cannot claim league coverage until it proves:

1. a versioned registry for all 32 franchises and each enabled lane;
2. exact official/source URLs, source owner, terms URL/revision, page/feed format, expected cadence, and active-season window;
3. source sections/groups expected for each roster page (active, reserve, practice squad, exempt, or explicitly unavailable);
4. per-team retrieval/parse/semantic status, last successful observation, last source update, and last content digest;
5. identity resolution counts by canonical GSIS ID and visible unresolved rows;
6. no missing franchise, team relocation/abbreviation ambiguity, or silently skipped source format;
7. an explicit universe statement: observed source rows only, not “all NFL players” unless the source coverage proves it;
8. separate `not_applicable`, `not_yet_published`, `source_unavailable`, `parse_failed`, `partial`, `stale`, and `conflict_unresolved` states;
9. completeness checks against source-declared row/group totals when available;
10. a bounded source-as-of time. A fresh retrieval of an old page is still stale.

The 658-row bounded 2026 census cannot fill roster gaps. Players with zero prior stats or no promoted identity can be missing from it.

## Missing, stale, and conflicting evidence

Fail-closed rules:

- Missing status is `unknown`, never active or inactive.
- Missing player row is not evidence the player is out of the league.
- An empty official page may mean offseason, not-yet-published, filter mismatch, or source failure.
- Roster membership does not prove gameday participation.
- A transaction is an event, not a timeless ownership state.
- A stale snapshot cannot become current through a new retrieval or generation time.
- Injury-report absence does not mean healthy.
- Depth-chart presence/absence cannot populate roster, injury, or gameday status.
- Conflicting official assertions remain as separate receipts until effective/publication clocks establish supersession.
- Source priority alone cannot erase a conflict; compare assertion lane, effective time, publication/update time, scope, and completeness.
- Fixture, candidate, manually curated, or downstream-model rows never become source truth.
- No injury-contingency workload or target share can be emitted.

## Source registry and monitoring design

A future source registry needs, per source and lane:

- registry version, source owner, team/league scope, exact URL/template, terms URL and observed revision;
- external-source classification and admission decision;
- access method, authentication requirement, robots/terms posture, permitted retention/redistribution;
- expected format and parser version;
- expected publication window/cadence and seasonal applicability;
- source effective/published/updated/retrieval/generated clocks;
- last success, last semantic success, last digest, consecutive failures, and stale threshold;
- coverage sections and population expectation;
- correction/supersession method;
- alert states for access denial, terms change, format drift, stale source, empty-unexpected, partial coverage, identity failure, and conflict.

Monitoring cannot poll a rights-blocked source. A registry entry may remain `blocked` or `manual_reference_only` until authority changes.

## Candidate artifact decomposition

Do not force these lanes into one record or enum. A later program should consider separate artifacts:

1. `current_roster_membership_snapshot_v0` — source roster membership/group observations only;
2. `player_ownership_state_v1` — interval state derived from governed observations/events, preserving `unknown`;
3. `player_transaction_event_v0` — append-only event assertions with effective/publication clocks;
4. `official_practice_report_observation_v0` — practice participation and injury text;
5. `official_game_designation_observation_v0` — Out/Doubtful/Questionable reports;
6. `official_gameday_inactive_observation_v0` — game-specific official inactive publications;
7. a separate compatibility view only if consumers still require `active_player_detection_v0`.

Artifact names are recommendations, not authorized contracts.

## Smallest independently buildable next slice

The smallest honest next slice is **one full-league roster-membership snapshot from one admitted, immutable 2026 nflverse roster release**, not a combined “current state” table.

Before activation, an operator must:

1. accept or reject the nflverse NGS/Shield roster source and exact retention/redistribution envelope;
2. pin the exact loader/producer refs and one exact 2026 release URL/byte digest;
3. require row-level source-family/fallback lineage so NGS weekly and Shield season observations cannot be confused;
4. approve the raw-status mapping/non-mapping table and preserve unresolved statuses;
5. require 32-team coverage, identity, clock, missingness, correction, and determinism tests;
6. keep transactions, injuries, game designations, and inactives out of that slice;
7. keep the output candidate-only pending independent audit.

If the nflverse source cannot be admitted, the next action is source/rights procurement—not scraping NFL or team sites.

## Consumer and repository ownership

- **TIBER-Data:** observed roster, transaction, practice report, game designation, inactive, reserve-state, identity, clocks, provenance, conflicts, and promotion.
- **TIBER-Teamstate:** later team-level interpretation.
- **Role-and-opportunity-model:** conditional replacement hierarchy and inherited role/opportunity.
- **TIBER-Forecast:** future injury/availability distributions after governed inputs and validation.
- **TIBER-Fantasy:** supported/partial/unavailable display.
- **FORGE:** downstream grading/consumption only.

No new repository is needed or authorized. Raw age/DOB remains a TIBER-Data identity fact; Age-Curve Intelligence is relevant only to separately validated lifecycle context, not these current-state sources.

## True, missing, and prohibited

True at the audited refs:

- TIBER has useful state/event/roster contract scaffolds;
- current promoted ownership is 27-row partial/stale evidence, not a roster universe;
- the 2025 roster map is historical membership with all active status unknown;
- official pages expose narrow source assertions but current terms block systematic retrieval;
- nflverse roster production uses NGS with Shield fallback and a daily cadence;
- nflverse current injury data is unavailable after its source died;
- no current 2026 gameday or practice-report lane is governed.

Still missing:

- an admitted current roster source and immutable 2026 bytes;
- current 32-team population and identity coverage;
- official-source automated-use/retention/redistribution authority;
- a current transaction wire;
- a replacement injury/practice-report source;
- stable inactives registry;
- full effective/publication/revision/supersession clocks;
- separately versioned lane contracts and validators.

Prohibited:

- treating stale/partial rows as current;
- scraping rights-blocked web pages;
- treating missing as inactive or healthy;
- collapsing events, roster state, reports, and gameday status;
- using depth charts as roster/injury truth;
- emitting role inheritance, injury probability, rankings, or advice;
- promotion, consumer wiring, merge, or deployment from this audit.

## Terminal decision

```text
current_player_state_v0_requires_source_or_contract_followup
```

This decision permits only a later operator choice on source/rights follow-up or the separately scoped roster-membership candidate slice described above. It does not authorize source access or implementation.
