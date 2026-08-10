# Offensive participation evidence readiness audit — 2026-08-10

> **Status:** exact-ref source/readiness audit; not a contract, ingest, artifact, or promotion  
> **Tracking issue:** TIBER-Data #245  
> **TIBER-Data ref:** `44296134a178f9d53fd7eda01a94548e76160d29`  
> **Evidence cutoff:** 2026-08-10

## Answer first

TIBER-Data does **not** currently have governed true routes, routes run, route participation, YPRR, TPRR, or offensive snap share.

Two upstream lanes are worth separating:

1. nflverse snap-count releases expose PFR-sourced game-level `offense_snaps` and `offense_pct`. They are a plausible offensive-snap source, but source/redistribution authority, percentage-denominator semantics, revision clocks, and the PFR-to-GSIS identity bridge are not admitted for this use.
2. nflverse participation releases expose GSIS player lists for each play. For 2023 onward they are provided by FTN only after the postseason and are published under CC-BY-SA 4.0 with required attribution. They can support a carefully named historical **pass-play participation proxy** after admission and validation. They do not prove that a player ran a route and cannot support a live 2026 watch during the season.

The six-row `exports/promoted/nfl/player_weekly_usage_v1.json` file is an offline fixture, not production coverage. The real promoted season and source-backed weekly artifacts have zero non-null route/snap fields.

Terminal decision:

```text
offensive_participation_v0_requires_source_or_rights_followup
```

No source is admitted and no builder is authorized by this audit.

## Task classification and boundary

This is a **provenance/source audit** plus an **external dataset audit** under `AGENTS.md`.

Allowed here:

- inspect committed TIBER artifacts, code, contracts, and prior frozen-source receipts;
- inspect exact public loader, dictionary, production, and license code at pinned refs;
- inventory fields, grain, identity, timing, rights, denominators, and failure states;
- sketch the smallest candidate contract and required tests.

Not established here:

- source admission, source access, mirroring, retention, or redistribution authority;
- a 2026 current-season participation feed;
- route-running truth;
- player-level role or injury-contingency interpretation;
- a score, ranking, forecast input, promoted artifact, or runtime activation.

No external data bytes were downloaded or committed in this audit. The exact 2025 snap-count byte receipt below was already frozen by the 2026-08-04 IDP readiness audit and is reused as evidence; it does not constitute admission for offensive use.

## Pinned evidence ledger

### Repository and source-code refs

| Item | Exact ref | Inspected paths / purpose |
| --- | --- | --- |
| TIBER-Data | `44296134a178f9d53fd7eda01a94548e76160d29` | Current promoted/research coverage, fixture export, route-proxy scaffold, governance, and the prior IDP source receipt. |
| nflreadpy | `66bb305e634ba815466749249d07b5c6e9268db3` (`0.1.6`) | `src/nflreadpy/load_snap_counts.py`, `src/nflreadpy/load_participation.py`, `pyproject.toml`, `LICENSE.md`. |
| nflreadr | `d072c08492067b578f27e562b6cc9c9e3b8589c3` | `R/load_snap_counts.R`, `R/load_participation.R`, `data-raw/dictionary_participation.csv`, `DESCRIPTION`. |
| nflverse-ftn | `6aef85fc2475120ce56b67ebedd623cf8e44a1d2` | `R/participation.R`, `exec/update_ftn_participation.R`, `DESCRIPTION`, `LICENSE`. |
| nflverse-pfr | `0bb27918ed5d3f74d916f8fe232f2d15db53b1ad` | `README.md`, `DESCRIPTION`; confirms the snap pipeline is PFR scraping code. |

The loader package's MIT license governs its software, not automatically the upstream data. The participation documentation separately declares CC-BY-SA 4.0 and required attribution. The snap data's underlying PFR source remains a separate admission/rights question.

### Existing TIBER evidence

| Artifact at the pinned Data ref | Exact repository blob | Observed bounded result |
| --- | --- | --- |
| `exports/promoted/nfl/player_season_coverage_v0.json` | `f7b2918b978d842cd8753a7f3dedd3836934859b`; byte SHA-256 `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` | 3,016 REG player-season rows for 2021–2025; 1,191 WR rows; `routes_run`, `route_participation`, and `snap_share` have 0 non-null WR values. |
| `data/processed/evidence/player_weekly_usage_2025.source_backed.json` | `df638e8c1c6b3c3aeadf597f1a637ce12402955a` | 6,326 source-backed player-week rows; target-share evidence exists, but route/snap fields have 0 non-null values. |
| `exports/promoted/nfl/player_weekly_usage_v1.json` | `3c18796bb7ac6938100f72bfe6e269d453fffcab` | Only 6 rows, all labeled `offline_fixture`; no production claim is allowed. |
| `docs/data/receiving-role-integrity-route-participation-proxy.md` | `b0e2680a76692f21ed733a31c408eb01ae5870df` | Existing semantic scaffold correctly distinguishes a pass-play proxy from true routes. |
| `src/research/receivingRoleIntegrityProxyReadiness.ts` | `99d9613141b61eae274b00fd39dc722729cc4af1` | Candidate schema/readiness vocabulary only; no admitted player truth. |

The row-level `offline_fixture` source labels govern. Any older issue wording that described the six-row export as real route/snap coverage is superseded by this audit.

### Reused frozen snap-count receipt

The prior IDP audit retrieved this mutable release URL on 2026-08-04 using the path constructed by the pinned nflreadpy loader:

| Exact URL | Bytes | SHA-256 |
| --- | ---: | --- |
| `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv` | 2,401,193 | `80b02a6e511aa20283551cae622b29ba4d0a6f006c489a2d91591fcad33792e7` |

Observed fields were:

```text
game_id,pfr_game_id,season,game_type,week,player,pfr_player_id,
position,team,opponent,offense_snaps,offense_pct,
defense_snaps,defense_pct,st_snaps,st_pct
```

This audit did not execute an offense-specific population or identity census against those bytes. Defensive join rates from the earlier audit must not be reused as offensive results.

## Current capability matrix

| Capability | Current TIBER state | Upstream candidate state | Decision |
| --- | --- | --- | --- |
| Game-level offensive snap count | absent | PFR/nflverse `offense_snaps`; exact 2025 bytes frozen previously | `external_candidate`; provider/rights, identity, clock, and correction follow-up required |
| Source-reported offensive percentage | absent | PFR/nflverse `offense_pct` | `external_candidate`; retain only as a raw observation until denominator semantics are proven |
| Governed offensive snap share | absent | deterministically possible only after a proven team denominator | unavailable; do not relabel `offense_pct` |
| Play-level offensive on-field participation | absent | FTN/NGS `offense_players` GSIS list | `external_candidate` for completed-season history, conditional on CC-BY-SA admission and attribution |
| Historical pass-play participation proxy | absent | potentially derivable by joining declared eligible pass plays to `offense_players` | contract and validation required; must be named `pass_play_participation_proxy` |
| Live/current-season participation | absent | FTN lane is released after all postseason games | unavailable for the 2026 in-season watch |
| True routes / routes run | absent | no admitted source | unavailable |
| Route participation | absent | on-field presence is insufficient | unavailable |
| YPRR / TPRR | absent | requires true route denominator | unavailable |
| Alignment / slot / wide deployment | absent | no admitted player-alignment source | unavailable |

## Source qualification

### 1. PFR-derived nflverse snap counts

Pinned nflreadpy and nflreadr loaders both identify Pro Football Reference as the source and construct per-season nflverse release paths. The source is game-level and PFR-keyed. It includes raw phase counts and percentages.

Useful facts:

- available from 2012 in the loader contract;
- carries game, season, week, team, opponent, position, PFR player ID, raw offensive snaps, and raw offensive percentage;
- a previously frozen 2025 byte receipt exists;
- the existing TIBER player-master path demonstrates a possible exact PFR-to-GSIS bridge mechanism.

Blocking facts:

- loader/software licensing is not upstream-data permission;
- TIBER has no recorded acceptance of PFR-derived retention or redistribution for this lane;
- publication, retrieval, revision, and supersession clocks are not embedded in the source rows;
- the release URL is mutable, so every accepted input would require immutable bytes, SHA-256, retrieval time, and a correction policy;
- `offense_pct` denominator semantics have not been proven against team offensive snaps;
- offense-specific PFR-to-GSIS coverage, one-to-one constraints, and unresolved IDs have not been measured;
- missing rows cannot be converted to zero snaps.

Classification: `external_candidate`, currently provider/rights and contract blocked.

### 2. FTN/NGS nflverse participation

The pinned nflreadr source says:

- participation data before 2023 is from NFL NGS;
- 2023 onward is courtesy of FTN;
- data is made available after all postseason games are complete;
- the data is CC-BY-SA 4.0;
- required attribution is **FTN Data via nflverse** for 2023 onward and **NFL NextGenStats via nflverse** for 2022 and earlier.

The pinned dictionary exposes play-grain `nflverse_game_id`, `play_id`, `possession_team`, `offense_players`, `offense_positions`, `n_offense`, and `route`. The pinned FTN producer shows that `offense_players` is a semicolon-delimited list of GSIS IDs for players whose team equals the possession team on that play. The dictionary defines `route` only for the primary receiver on the play; it is not an all-player route ledger and cannot count every player's routes.

This is materially stronger identity evidence than the snap lane, but it still does not prove a route. A WR can be on the field for a pass play without running a route; sacks, scrambles, spikes, penalties, and nullified plays require an explicit eligibility policy.

Blocking facts:

- no 2025 participation release bytes or row coverage were frozen in this audit;
- CC-BY-SA retention, transformation, attribution, and share-alike obligations need an explicit TIBER admission decision;
- exact completed-season availability and late corrections need receipts, not a loader default;
- play eligibility, team denominator, malformed player lists, duplicate IDs, fewer/more-than-11 personnel, penalties, and missing participation rows need tests;
- it cannot answer an in-season 2026 opportunity question.

Classification: `external_candidate` for historical pass-play participation only; not current-facing and not routes.

### 3. Named true-route provider reference

Issue #71 specifically names Fantasy Points Data as a manual/provider reference for route-related claims. Under #245, no Fantasy Points Data agreement, terms, definitions, source bytes, schema, population, clocks, identity bridge, or retention/redistribution posture was inspected.

Classification: `schema_reference_only`. The named provider establishes the kind of evidence a future contract would need; it supplies no admissible row or current claim here. No true-route field may be populated from the two candidates above.

## Metric dictionary and naming guardrails

The participation source's play-level `route` label describes only the primary receiver's route. It cannot be summed into all-player `routes_run` or used as the denominator for route participation, YPRR, or TPRR without a separately admitted all-player route source.

| Field | Allowed meaning | Required evidence | Must not mean |
| --- | --- | --- | --- |
| `offense_snaps_raw` | source-reported player offensive snap count for one game | admitted frozen snap row and resolved identity | routes run |
| `offense_pct_raw` | source-reported percentage preserved unchanged | admitted frozen snap row plus source receipt | governed snap share |
| `snap_share` | player offensive snaps divided by a proven team offensive-snap denominator under a versioned rule | admitted player count, admitted denominator, reconciliation tests | copied `offense_pct_raw` without proof |
| `pass_play_on_field_count` | eligible team pass plays where player GSIS ID appears in `offense_players` | admitted participation plus a frozen pass-play predicate | routes run |
| `pass_play_participation_proxy` | `pass_play_on_field_count / eligible_team_pass_plays` under a versioned rule | both governed counts and missingness policy | route participation |
| `routes_run` | number of actual routes run | admitted true-route provider | on-field pass plays |
| `route_participation` | actual routes divided by declared dropback/pass-play denominator | admitted true-route numerator and denominator | participation proxy |
| `yprr` / `tprr` | receiving yards or targets per actual route run | admitted route denominator | division by on-field proxy |

Null, absent, unresolved, and not-yet-published are distinct from observed zero.

## Candidate contract sketch — not authorized

A future separately activated candidate build could emit a versioned `offensive_participation_evidence_v0` at player-game-source grain with:

- canonical GSIS player ID plus source player ID and identity status;
- season, week, game ID, team, opponent, and season type;
- source family, source URL, exact input SHA-256, retrieval time, source effective/occurrence time, and correction/supersession status;
- raw source fields (`offense_snaps_raw`, `offense_pct_raw`) without semantic upgrading;
- declared denominator counts and rule version for any derived snap share;
- eligible pass-play count, on-field count, proxy value, predicate version, and missingness status;
- field-level evidence status: `supported`, `partial`, `unavailable`, or `unresolved_identity`;
- explicit `routes_run_status: unavailable` and `route_participation_status: unavailable` unless a separately admitted true-route source is bound;
- attribution text and license receipt for participation-derived rows.

It must remain candidate-only until an independent audit verifies source, rights, identity, denominator, clocks, and deterministic reproduction.

## Required negative and reconciliation tests

A future build is not reviewable without tests that prove:

1. input SHA-256 and source provenance are verified before parsing;
2. mutable or post-cutoff bytes fail closed and never overwrite a prior snapshot;
3. PFR-to-GSIS joins are exact, one-to-one where asserted, and unresolved IDs remain visible;
4. blank IDs and names never trigger fuzzy or normalized-name fallback;
5. missing player-games/plays remain unavailable and are never zero-filled;
6. source `offense_pct` is preserved raw and cannot populate governed `snap_share` without denominator reconciliation;
7. player and team snap totals reconcile under a declared tolerance and declared denominator rule;
8. semicolon-delimited GSIS lists handle blanks, duplicates, malformed IDs, and non-11-player plays explicitly;
9. the pass-play predicate handles sacks, scrambles, spikes, kneels, penalties, no-plays, and missing play-by-play fields under frozen rules;
10. on-field participation never populates `routes_run`, `route_participation`, YPRR, or TPRR;
11. CC-BY-SA source rows carry required attribution and license lineage;
12. 2026 in-season participation returns `not_yet_published`, not an empty success;
13. source corrections produce append-only supersession receipts;
14. repeated builds with reordered inputs produce byte-identical candidate artifacts and receipts;
15. zero supported rows ends in a blocked terminal state.

## Case-study trace

For the 2026 late-veteran WR pilot, TIBER currently has no governed route/snap evidence for any of these comparison rows:

| Player | Snap evidence | Pass-play participation | True routes | Current interpretation |
| --- | --- | --- | --- | --- |
| Roman Wilson | unavailable | unavailable | unavailable | unknown |
| Jordan Whittington | unavailable | unavailable | unavailable | unknown |
| Luke McCaffrey | unavailable | unavailable | unavailable | unknown |
| Jacob Cowing | unavailable | unavailable | unavailable | unknown |
| Devontez Walker | unavailable | unavailable | unavailable | unknown |
| Tyquan Thornton | unavailable | unavailable | unavailable | unknown |
| Ryan Flournoy | unavailable | unavailable | unavailable | unknown |

This trace is deliberately unordered and is not a candidate ranking.

## Ownership

- **TIBER-Data:** source qualification/admission, immutable raw receipts, identity bridge, raw counts, denominators, field missingness, provenance, and promotion.
- **Role-and-opportunity-model:** deployment and role-change interpretation after Data evidence is governed.
- **Signal-Validation-Model:** historical hypothesis tests and no-leakage validation.
- **TIBER-Fantasy:** honest display of supported/partial/unavailable evidence.
- **TIBER-Teamstate:** team-level environment interpretation only.
- **FORGE:** downstream consumer of approved interpretations; not the source owner.

## True, missing, and prohibited

True at the audited refs:

- real promoted/research TIBER route/snap coverage is zero;
- the six-row weekly export is fixture-only;
- a frozen PFR-derived snap-count candidate exists with raw offensive fields;
- completed-season participation exposes GSIS on-field lists;
- 2023+ participation has an explicit CC-BY-SA 4.0 attribution requirement;
- on-field participation is not a route.

Still missing:

- source/rights acceptance for both source families;
- an offense-specific snap population and identity census;
- denominator and correction semantics;
- frozen participation bytes and population coverage;
- a versioned pass-play predicate;
- current-season participation;
- any admitted true-route source.

Must not be assumed:

- absent row means zero;
- source percentage is governed snap share;
- on-field on a pass play means route run;
- completed-season participation is current 2026 evidence;
- software license authorizes upstream data redistribution;
- a fixture export is production coverage.

## Terminal decision and next activation gate

```text
offensive_participation_v0_requires_source_or_rights_followup
```

Before a candidate build can be activated, an operator must bind all of the following:

1. accept or reject Data ownership and the exact permitted use/retention/redistribution envelope for PFR-derived snap counts;
2. accept or reject the CC-BY-SA participation lane, including attribution and share-alike obligations;
3. name exact season/source URLs, retrieval cadence, cutoff, immutable-byte receipt format, and correction/supersession policy;
4. authorize bounded row probes for offense-specific population, identity, and denominator reconciliation;
5. choose whether the first slice is historical snap evidence, historical pass-play participation proxy, or both;
6. approve a candidate contract and tests that keep route fields unavailable;
7. keep live 2026 opportunity claims blocked unless a separate current-season source is admitted.

This audit authorizes none of those actions by itself.
