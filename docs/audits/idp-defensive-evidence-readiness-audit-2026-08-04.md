# IDP defensive evidence readiness audit — 2026-08-04

> **Status:** exact-ref source/readiness audit; not a contract, ingest, artifact, or
> promotion
> **Tracking issue:** TIBER-Data #232
> **Program record:** TIBER-Ops #59
> **Defensive profile design record:** Role-and-opportunity-model #22
> **TIBER-Data ref:**
> `3393a8f0b7f4ffa640f63d712768beb1c52b917a`

## Answer first

TIBER-Data does **not** have a governed IDP player universe or a defensive
Role-and-opportunity input today. Its admitted player identity, weekly usage,
player-season, roster-map, PPR, and bounded-population lanes are explicitly
QB/RB/WR/TE-oriented.

The upstream evidence path is nevertheless viable. A frozen 2025 nflverse
player-week snapshot contains 10,416 regular-season DL/LB/DB rows covering
1,035 GSIS players and 15 defensive box-stat fields. Separate weekly roster,
player-master, and snap-count snapshots provide materially useful identity and
participation candidates. Travis Hunter appears under one GSIS identity with
both offensive and defensive facts and with conflicting source-position
observations, which is a direct proof that TIBER needs independent evidence
lanes rather than one destructive `position` field.

The path is not ready for implementation as governed truth yet. TIBER has not
admitted the source snapshots, pinned the loader dependency, resolved the
GSIS-to-PFR snap bridge, defined source-position observation semantics, proven
play-level event bundles and corrections, or sourced player alignment and
phase exposure. The correct next step is a bounded source-qualification and
contract-design follow-up, not a fantasy-points table and not a live IDP
profile.

## Task classification and boundary

This is a **provenance/source audit** plus an **external dataset audit** under
`AGENTS.md`.

Per-source `AGENTS.md` classification is recorded in the rights ledger below.
It is independent of both the issue capability status and TIBER-Data admission.

Allowed here:

- inspect committed TIBER contracts, artifacts, builders, and audit records;
- inspect exact public source code and hash-addressed temporary copies of
  public release assets under #232's explicit read-only probe allowance;
- inventory fields, population, identity, grain, rights, and failure modes;
- propose the smallest next contract family.

Not established here:

- source admission or redistribution approval;
- a complete/current defender population;
- canonical defensive roles or alignments;
- a player-event ledger;
- fantasy platform eligibility or league scoring;
- a model, projection, ranking, or downstream activation.

No downloaded source bytes are committed, mirrored, admitted, or promoted by
this audit. Temporary probe files remained outside the repository and are not
an authorized future input merely because they were inspected.

## Pinned evidence ledger

### Repository and source-code refs

| Item | Exact ref | What was inspected |
| --- | --- | --- |
| TIBER-Data | `3393a8f0b7f4ffa640f63d712768beb1c52b917a` | Current contracts, artifacts, builders, tests, identity crosswalk, and governance. |
| nflreadpy | `66bb305e634ba815466749249d07b5c6e9268db3` (`0.1.6`) | Loader paths for player stats, weekly rosters, players, and snap counts. |
| nflfastR | `0489133d85c5f11682572d9436c4a7b371a789aa` | Player-stat production and play-level defensive participant/bundle candidates. |
| `docs/reports/player-season-coverage-v0-2015-2020-source-availability.json` | current Data ref; generated with nflreadpy `0.1.5` | Existing schema inventory, which observed defensive columns but scoped population analysis to QB/RB/WR/TE. |

TIBER currently declares `nflreadpy>=0.1.0` in `pyproject.toml`; it does not pin
the `0.1.5` used by an earlier committed audit or the `0.1.6` loader inspected
here. That version drift must be closed before a reproducible build.

### Exact inspected-path ledger

The repository-ref summary above is not a substitute for the inspected paths.
At the pinned TIBER-Data ref this audit read:

- authority and source policy: `AGENTS.md`, `TRUTH_SOURCES.md`,
  `docs/repo-boundaries-and-feedback-loops.md`,
  `docs/governance/cross-repo-governance-v0.md`, and
  `docs/governance/evidence-layer-v0.md`;
- dependency and contract boundary: `pyproject.toml`,
  `src/contracts/v1/enums.ts`, and `src/contracts/v1/roleOpportunity.ts`;
- existing builders and probes:
  `scripts/build_roster_player_team_map_source_backed_2025.py`,
  `scripts/build_player_weekly_ppr_outcomes_source_backed_2025.py`,
  `scripts/build_player_weekly_usage_source_backed_2025.py`,
  `scripts/build_identity_crosswalk_v1.py`, and
  `scripts/inspect_participation_columns_2025.py`;
- existing tests: `test/rosterPlayerTeamMapArtifact.export.test.ts`,
  `test/playerWeeklyPprOutcomesArtifact.export.test.ts`, and
  `test/playerWeeklyUsageArtifact.export.test.ts`;
- existing audits and population evidence:
  `docs/data/nflverse-participation-route-proxy-audit.md`,
  `docs/reports/player-season-coverage-v0-2015-2020-source-availability.json`,
  `docs/reports/bounded-2026-population-census-v0-coverage.md`, and
  `exports/candidates/population_census/bounded_2026_population_census_v0.json`;
- existing promoted/processed evidence:
  `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json`,
  `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json`,
  `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json`,
  and `data/processed/evidence/roster_player_team_map_2025.source_backed.json`.

At nflreadpy `66bb305e634ba815466749249d07b5c6e9268db3`, this audit read
`src/nflreadpy/load_stats.py`, `src/nflreadpy/load_snap_counts.py`,
`src/nflreadpy/load_players.py`, `src/nflreadpy/load_rosters_weekly.py`,
`src/nflreadpy/downloader.py`, `pyproject.toml`, and `LICENSE.md`. At nflfastR
`0489133d85c5f11682572d9436c4a7b371a789aa`, it read
`R/helper_tidy_play_stats.R`, `R/aggregate_game_stats_def.R`,
`R/top-level_scraper.R`, and `LICENSE.md`. No unlisted provider SDK or private
source was inspected.

### Frozen public-source probes

Retrieved on 2026-08-04 using the exact CSV paths constructed by the pinned
nflreadpy loader. These mutable release URLs are evidence locations, not frozen
source revisions by themselves; byte hashes are therefore mandatory.

| Candidate source | Exact URL | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| 2025 player-week stats | `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv` | 8,461,830 | `40b67b296fda02c7f628741d4aa471208352dd42fb670d4854e7ba95295af1a6` |
| 2025 snap counts | `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv` | 2,401,193 | `80b02a6e511aa20283551cae622b29ba4d0a6f006c489a2d91591fcad33792e7` |
| player master/crosswalk | `https://github.com/nflverse/nflverse-data/releases/download/players/players.csv` | 7,326,939 | `a17c10b15c6624f82f0ef8b50a4fa57c8fbfc78912d1c2f825c07b25856a92b4` |
| 2025 weekly rosters | `https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_2025.csv` | 15,385,661 | `c2f7a1ffebe06058400af1989d1cd2900cc5c9659f084623708a06d4e28de35b` |

Reproduction filters:

- player stats: `season_type == REG` and `position_group in {DL, LB, DB}`;
- snap counts: `game_type == REG` and `defense_snaps > 0`;
- weekly rosters: `game_type == REG` and `position in {DL, LB, DB}`;
- identity joins: exact IDs only; no name normalization or fuzzy matching.

## What TIBER-Data currently supports

The following are properties of the pinned repository, not inferences from its
name:

1. `src/contracts/v1/enums.ts` restricts the current canonical position enum to
   `QB/RB/WR/TE` and its role enum is offensive.
2. `scripts/build_roster_player_team_map_source_backed_2025.py` explicitly
   filters weekly roster rows to `QB/RB/WR/TE`. The existing export test has no
   negative defensive-position input fixture, so the builder's filter behavior
   is asserted only through output-position properties, and only when raw
   sources are present.
3. Player-week PPR and usage builders apply the same offensive filter. Their
   current fixtures are offensive; they do not prove defensive rows fail closed.
4. The bounded 2026 population census declares
   `idp_full_universe_available: false`, and its coverage report explicitly
   excludes IDP.
5. The promoted Sleeper identity crosswalk stores Travis Hunter once as `WR`;
   it has no multi-domain position-observation or eligibility structure.
6. The processed 2025 weekly PPR artifact stores Hunter as `WR`. A rebuild from
   the live snapshot audited here would see the same GSIS row labeled `CB/DB`,
   demonstrating why source position must not be used as a destructive lane
   filter.
7. No committed governed defensive population, snap, alignment, phase-exposure,
   event-bundle, correction-ledger, or player-week defensive evidence artifact
   exists.
8. The existing participation audit could not verify live columns and correctly
   leaves participation-derived claims blocked. Team-published depth-chart work
   is context, not observed deployment.

Therefore an upstream column being visible does not make IDP supported in
TIBER-Data.

## Source probe results

### Player-week defensive box evidence

The frozen player-week asset contains:

- 19,421 total rows and 145 columns;
- 18,539 regular-season rows;
- 10,416 regular-season rows in defensive position groups;
- 1,035 unique nonblank GSIS player IDs;
- all regular-season weeks 1–18;
- group counts: DB 4,070, LB 3,213, DL 3,133;
- zero duplicate rows at `(player_id, season, week, team)` in the bounded
  defender slice;
- nonblank `player_id`, `game_id`, `team`, `position`, and `position_group` on
  every bounded defender row.

Detailed source-position values are heterogeneous:

| Group | Observed detailed positions and row counts |
| --- | --- |
| DB | `CB` 1,992; `SAF` 1,468; `DB` 403; `FS` 141; `S` 66 |
| LB | `LB` 2,859; `OLB` 224; `MLB` 77; `ILB` 53 |
| DL | `DT` 1,540; `DE` 1,462; `NT` 79; `DL` 52 |

The generic `LB` majority is not enough to classify off-ball versus edge.
Source-listed position remains a provider observation, not canonical role.

Observed weekly aggregate defensive columns:

```text
def_tackles_solo
def_tackles_with_assist
def_tackle_assists
def_tackles_for_loss
def_tackles_for_loss_yards
def_fumbles_forced
def_sacks
def_sack_yards
def_qb_hits
def_interceptions
def_interception_yards
def_pass_defended
def_tds
def_fumbles
def_safeties
```

Recovery/return fields outside the `def_` prefix are also present:

```text
fumble_recovery_own
fumble_recovery_yards_own
fumble_recovery_opp
fumble_recovery_yards_opp
fumble_recovery_tds
```

All of these numeric cells are populated on emitted rows, often with source
zeroes. That does **not** authorize zero-filled missing player-weeks: a defender
who is absent from the file has unknown participation/evidence until another
source proves a zero.

The grain is a player-game/week aggregate. `game_id` survives, but `play_id`
does not. These rows cannot reconstruct which tackle, TFL, sack, QB hit, forced
fumble, recovery, return, and touchdown belonged to the same play.

### Weekly roster membership

The frozen weekly roster asset contains 44,697 regular-season rows. Its broad
DL/LB/DB slice contains:

- 21,087 rows;
- 1,483 unique nonblank GSIS IDs;
- 19 rows with no GSIS ID;
- DB 8,538, DL 6,547, LB 6,002;
- weeks 1–18;
- no duplicate nonblank `(gsis_id, season, week, team)` keys in the slice.

It carries source status and provider IDs, including GSIS, PFR, ESPN, PFF, and
Sleeper IDs. TIBER's current builder reads this source family but discards every
defensive row before producing its roster-map artifact.

Roster status may support a later membership/status observation contract. It
does not prove a player took a defensive snap, and absence does not prove
inactive.

### Snap participation and exact identity bridge

The snap-count asset contains 26,612 rows, including 25,395 regular-season rows
and 10,539 regular-season player-games with `defense_snaps > 0`. Those rows cover
1,015 unique PFR IDs across weeks 1–18.

It supplies:

```text
game_id, pfr_game_id, season, game_type, week,
player, pfr_player_id, position, team, opponent,
offense_snaps, offense_pct, defense_snaps, defense_pct,
st_snaps, st_pct
```

The player key is PFR, not GSIS. An exact join through the frozen player master
maps 1,012 of the 1,015 defensive-snap PFR IDs to nonblank GSIS IDs (10,524 of
10,539 rows). `HallGa01`, `JohnIs03`, and `OkoyCJ00` do not resolve to GSIS in
that snapshot. A governed builder must preserve these as unresolved, never use
names as a fallback, and pin the master snapshot with the snap bytes.

The source-provided percentages are useful participation candidates, but their
team-play denominator and revision behavior still need a semantic audit.
Special-teams snaps remain a separate lane.

### Play-level event-bundle feasibility

The pinned nflfastR producer/source exposes candidate play identity and
participant slots for:

- `game_id`, `play_id`, and drive;
- solo tackle participants;
- tackle-assist and tackle-with-assist participants;
- TFL participants;
- full sack and two half-sack participants;
- QB-hit participants, with producer logic distinct from sacks;
- pass-defense participants;
- interception and lateral-interception participants;
- forced-fumble participants;
- up to two fumble-recovery participants and return yards;
- blocker, safety, touchdown, and return participants.

This makes a scoring-neutral event bundle plausible. It does not make one
admitted. TIBER currently aggregates play-level defensive relationships away,
has no event ID or credit-fraction contract, and has not audited complete
population, lateral, penalty/null-play, correction, or stat-provider semantics.

### Candidate-field semantics, keys, and clocks

This ledger supplies the field-level metadata behind the capability decisions.
Exact source URLs, code refs, and rights dispositions are in the pinned and
rights ledgers. “Unavailable” is intentional when a source did not expose the
required semantic clock or denominator; it must not be repaired with a default.

| Source family/ref | Candidate fields and meaning | Units, scope/grain, identity key | Clocks/corrections | Primary failure state |
| --- | --- | --- | --- | --- |
| 2025 player-week stats asset (`40b67b...`) | `def_tackles_solo`, `def_tackles_with_assist`, `def_tackle_assists`, `def_tackles_for_loss`, `def_tackles_for_loss_yards`, `def_fumbles_forced`, `def_sacks`, `def_sack_yards`, `def_qb_hits`, `def_interceptions`, `def_interception_yards`, `def_pass_defended`, `def_tds`, `def_fumbles`, `def_safeties`, plus own/opponent fumble-recovery counts/yards/TDs; provider-credited weekly defensive outcomes | Counts are nonnegative numeric credits (fractional credit must survive); yards are signed numeric values. 2025 REG player-game/week aggregate keyed by GSIS `player_id`, `game_id`, season/week/team. | Occurrence game/week exists; exact publication, retrieval timestamp, correction revision, and supersession clock are unavailable. The URL is mutable. | No `play_id`; emitted zero cannot prove an absent player-week zero; provider category/bundle relationships cannot be reconstructed. |
| 2025 weekly-roster asset (`c2f7a1...`) | Raw `status`, `position`, `depth_chart_position`, `ngs_position`, team, and provider IDs are source membership/label observations only | Categorical observations at 2025 REG `(gsis_id, season, week, team)`; 19 bounded rows have no GSIS key. | Season/week exists; transaction/gameday effective time, publication time, correction revision, and supersession interval are unavailable. | Status cannot prove active/inactive/IR/DNP semantics; label filtering omits Hunter-like defenders; missing row is not inactivity. |
| 2025 snap-count asset (`80b02a...`) | `offense_snaps`, `defense_snaps`, `st_snaps` are phase counts; `offense_pct`, `defense_pct`, `st_pct` are raw source percentages, not governed shares | Counts are nonnegative integers and percentages are decimals `[0,1]`; 2025 REG PFR-keyed player-game `(pfr_player_id, game_id)` with season/week/team. | Game/week exists; source publication, underlying team-play denominator definition, correction revision, and supersession clock are unavailable. | Three PFR IDs/15 positive-defense-snap rows do not bridge to GSIS; percentages may drift with an unproven denominator; rights unresolved. |
| Player master asset (`a17c10...`) | GSIS/PFR/ESPN/PFF and other IDs plus source position/team/status fields are identity candidates and observations, not canonical role | Current-snapshot player row keyed by unique nonblank GSIS ID; PFR is unique when present in the probed snapshot. Categorical values have no unit. | Snapshot retrieval date/hash exists; field-level effective dates, historical predecessor, publication, and correction clocks are unavailable. | Current snapshot can rewrite history; provider IDs carry separate rights; exact unmatched IDs stay unresolved and names cannot repair them. |
| nflfastR producer code (`0489133d...`) | Candidate game/play IDs, sack/hit/tackle/interception/fumble/block/safety/TD participant slots, fractional credit, yards, lateral and bundle relationships | No source rows were inspected, so no admitted grain/key/unit claim exists beyond code-path feasibility. Proposed grain is participant-event within play. | No dataset retrieval, publication, or correction revision was frozen. | Producer code is not evidence; participant completeness, penalties/null plays, laterals, corrections, and data rights remain unverified. |
| FTN participation lane documented by current Data audit | Candidate team/personnel/participation fields only; no exact 2025 player-alignment field was observed in this audit | No frozen rows, supported population, key, grain, or units were verified. | The existing audit proves no publication, retrieval, correction, or supersession clock for this use. | `absent`: cannot support pass-rush/run/coverage exposure, defensive personnel, or individual alignment at this ref. |

For issue-required candidates with status `absent`, the exact source/ref is
`none proven at the audited refs`; their desired meaning, scope, and failure
risk are recorded in the capability matrix. Units and identity/clock semantics
remain deliberately undefined until source qualification supplies them.

## Capability matrix

The status column uses exactly the issue vocabulary and describes end-to-end
readiness at the audited ref:

- `source_backed`: exact frozen rows, identity/grain, and usable field semantics
  were observed in the bounded source probe;
- `derived_with_declared_rule`: a deterministic rule over source-backed inputs
  is fully declared here;
- `fixture_only`: only a non-production example exists;
- `absent`: no exact frozen row/population/semantics was proven, even if source
  code or a planned lane suggests a future candidate;
- `provider_or_license_blocked`: a known access, attribution, redistribution, or
  proprietary-semantics gate prevents admission.

`Current Data state` separately states whether TIBER has admitted the evidence.
This keeps a real upstream candidate distinct from a governed TIBER artifact.
The matrix is the only assignment of the issue's capability-status vocabulary.
The later rights ledger separately applies the closed `AGENTS.md`
external-source classification vocabulary and records admission facts; neither
is a second capability status.

Shared provenance rule for every source-backed row below: exact URL/source-code
ref, retrieval time, byte hash, source key, season/game/week scope, and
supersession state must accompany any later artifact. Until then, current Data
state is absent even when an upstream source candidate is strong.

| Candidate input | Status | Field/grain and denominator | Current Data state; v0 disposition; failure risk |
| --- | --- | --- | --- |
| Bounded weekly DL/LB/DB source-position membership | `source_backed` | Weekly roster, GSIS/team/week/status; 1,483 IDs in the 2025 `position in {DL,LB,DB}` slice. | Absent. **Minimum-required input but incomplete alone**: the filter excludes two-way Hunter because that source says WR. Preserve 19 unresolved-ID rows; absence is unknown. |
| Full weekly defender universe independent of one position label | `absent` | No audited population rule unions roster, defensive stats, and defensive snaps without destructive position filtering. | **Required**. Must include two-way/position-conflict cases and publish coverage reconciliation. |
| Canonical/source ID bridge | `source_backed` | Player master: GSIS, PFR, ESPN, PFF and other IDs; snapshot grain one player row. | Partial offense-only crosswalk today. **Required**. Exact joins only; preserve collisions/unresolved. |
| Unresolved/conflicting PFR-to-GSIS identity state | `provider_or_license_blocked` | The exact probe preserves the original namespaced key and leaves 3 PFR IDs/15 positive-defensive-snap rows unresolved; no name matching. PFR snap-source admission rights are not cleared. | Absent. **Required** with collision counts and source receipts after source qualification. A failed bridge must not delete a player or assign another identity. |
| Dual-domain identity with independent evidence lanes | `derived_with_declared_rule` | Group only on exact canonical/source ID, retain offense/defense phase on each observation, and never blend lane-specific role evidence. Hunter proves the rule is necessary. | Absent. **Required for two-way players**. One person may link multiple profiles; one lossy position/role field is prohibited. |
| Player-game/week/team scope keys | `source_backed` | Stats expose GSIS plus `game_id`, season/week/team; snaps expose PFR plus game/season/week/team; roster exposes GSIS plus season/week/team. | Absent as defensive contracts. **Required at each native grain**; do not manufacture roster `game_id` or collapse multi-team weeks. |
| Raw weekly roster/status observation | `source_backed` | Weekly roster categorical fields at `(gsis_id, season, week, team)`; raw status is an observation, not proof of game availability. | Absent. **Minimum-required observation, insufficient alone**. Preserve original value and source clock; 19 rows lack GSIS ID. |
| Governed active/inactive/IR/gameday-availability semantics | `absent` | No audited mapping proves what each roster status means at transaction, practice, or game kickoff clocks. | **Required before availability claims**. Raw roster status, inactive list, IR transaction, bye, and DNP are not interchangeable. |
| Source-position observations | `source_backed` | Stats, roster, snap, and player-master positions at their own clocks. | Current single position is unsafe. **Required** as an observation array; never overwrite canonical role or eligibility. |
| Effective-dated position changes | `absent` | Sources expose position observations at different grains, but no governed `effective_from`/`effective_to` or supersession rule exists. | **Required for historical replay**. Preserve conflicts rather than selecting the newest label without a declared clock. |
| Platform eligibility / league-slot legality | `absent` | No audited effective-dated eligibility array in these sources. | **Prohibited in canonical football profile.** Fantasy owns versioned platform/league interpretation. |
| Defensive snaps | `provider_or_license_blocked` | Exact PFR-keyed player-game counts were observed, but source admission rights are not cleared; no denominator. | Absent. **Required** after rights qualification and exact GSIS bridge. Probe visibility alone cannot admit the field. |
| Raw source-provided defensive snap percentage | `provider_or_license_blocked` | Exact PFR-keyed player-game `defense_pct` observations were seen, decimal `[0,1]`, but source admission rights are not cleared and the denominator is not governed. | Absent. **Optional raw observation only** after rights/semantics qualification; do not label it canonical snap share. |
| Governed defensive snap share | `absent` | No admitted numerator/denominator pair or proven source-denominator definition and correction clock. | **Required for Role-and-opportunity use**. A raw percentage cannot satisfy this field. |
| Team defensive plays | `absent` | No admitted player/team denominator contract. | **Required** if recomputing shares; never use max individual snaps as team truth. |
| Defensive pass-play denominator | `absent` | No admitted team/game count of pass opportunities aligned to player participation. | **Required for pass-rush/coverage opportunity**. Dropbacks, attempts, and charted pass plays are not silently equivalent. |
| Defensive rush-play denominator | `absent` | No admitted team/game count of opponent designed rush opportunities aligned to player participation. | **Required for run-defense opportunity**. Scrambles, kneels, and aborted plays need declared handling. |
| Tackle-opportunity denominator | `absent` | No audited definition joins eligible defensive plays, player-on-field state, and tackle-credit semantics. | **Deferred**. Team plays, snaps, and ball-carrier contacts are not interchangeable tackle opportunities. |
| Special-teams snaps | `provider_or_license_blocked` | Exact PFR-keyed player-game counts/percentages were observed, but source admission rights are not cleared. | Absent. **Optional after rights qualification and separate**; never mix into defensive opportunity. |
| Pass-rush snaps | `absent` | No verified source field. | **Required for edge/interior role; defer** rather than infer from sacks/hits. |
| Run-defense snaps | `absent` | No verified source field. | **Required for phase role; defer**. |
| Coverage snaps | `absent` | Not present in the audited weekly stats/snaps, and no exact player-level charting source was inspected. | **Required for DB/LB coverage opportunity; unavailable at this ref**. Any later provider needs a separate semantics/rights review. |
| Targets in coverage | `absent` | Not present in the audited weekly stats/snaps, and no exact player-level target-assignment source was inspected. | **Optional only if source-backed; unavailable at this ref**. Target attribution must not be inferred from pass defenses or interceptions. |
| Defensive personnel/package observation | `absent` | No frozen player-level or team-play personnel/package row was verified; existing participation work is only a proposed source lane. | **Optional context, not deployment truth**. A team package cannot assign an individual alignment without participant evidence. |
| Interior/edge/box/slot/perimeter/deep alignment | `absent` | Per-player alignment was not proven in any exact frozen input. | **Required for broad defensive roles; unavailable at this ref**. Do not derive from fantasy tags or depth charts. |
| Solo tackle | `source_backed` | Weekly player-game count, GSIS. | Absent. **Required aggregate view**; event identity still required for bundle truth. |
| Assisted/tackle-with-assist credits | `source_backed` | Separate weekly player-game columns. | Absent. **Required**; do not collapse distinct provider credits without a rule. |
| Tackle for loss and yards | `source_backed` | Weekly player-game counts/yards. | Absent. **Required**; may stack with tackle/sack in the same play. |
| Full sack | `source_backed` | Weekly player-game numeric credit/yards. | Absent. **Required**. Preserve fractional values and bundle links later. |
| Partial-sack participant identity | `absent` | Candidate PBP participant slots exist; no admitted event record. | **Required for atomic ledger** before claiming player-event completeness. |
| QB hit | `source_backed` | Weekly player-game count. | Absent. **Optional/valuable**; source producer distinguishes its event logic from sacks. |
| Pressure/hurry | `absent` | No audited field or admitted definition in the inspected snapshots. | **Deferred**. Never synthesize from sack + hit; any later provider requires its own rights review. |
| Pass defended | `source_backed` | Weekly player-game count. | Absent. **Required** for coverage outcomes; event link needed for INT stacking. |
| Interception and return yards | `source_backed` | Weekly player-game count/yards. | Absent. **Required**; play link/lateral semantics unresolved. |
| Forced fumble | `source_backed` | Weekly player-game count. | Absent. **Required**; link to tackle/sack and recovery play. |
| Fumble recovery and return yards | `source_backed` | Own/opponent recovery counts/yards plus recovery TD aggregate. | Absent. **Required**, but own/opponent semantics and participant credits need explicit mapping. |
| Safety | `source_backed` | Weekly player-game count. | Absent. **Optional event in v0**, nullable only when source unsupported. |
| Blocked kick credited defender | `absent` | Candidate PBP blocker slot; no admitted player-week credit field. | **Deferred** until participant/event semantics are audited. |
| Defensive touchdown | `source_backed` | Weekly player-game count; recovery TD also separately present. | Absent. **Required outcome**, with type/bundle linkage to prevent ambiguity. |
| Atomic event identity / event bundle | `absent` | Candidate PBP keys/participants exist; no TIBER event record. | **Required before scoring adapter or atomic-event claim**. Weekly aggregates cannot reconstruct stacks. |
| Publication/retrieval clock | `absent` | This probe records retrieval date and byte hash, but no exact persisted retrieval timestamp, source publication time, or correction revision. | **Required**. A later receipt contract may derive fields only under a declared clock rule. |
| Correction/supersession ledger | `absent` | Mutable release assets; no frozen defensive revision chain. | **Required** for historical replay and Forecast cutoff integrity. |
| Missed-game/bye/no-row state | `absent` | No admitted schedule-plus-roster-plus-participation reconciliation distinguishes bye, inactive, IR, did-not-play, unsupported source, late correction, and genuinely missing row. | **Required before rolling windows**. A missing row must remain unknown until one explicit state is proven; never zero-fill it. |
| Team-published depth-chart context | `absent` | A separately scoped source lane is planned, but no governed defensive artifact exists at this ref. | **Optional context only** after admission. Never substitute for deployment. |
| Canonical defensive role | `absent` | No Data-owned role field should be inferred here. | **Prohibited in Data v0**. Role-and-opportunity owns the later interpretation after evidence admission. |
| Fantasy points | `absent` | League scoring is not a defender fact. | **Prohibited in all canonical Data evidence contracts.** |

## Temporal, correction, provenance, and rights findings

Every future record must distinguish:

1. game/play occurrence time;
2. source publication/availability time;
3. retrieval time and source-byte hash;
4. stat-correction time;
5. artifact build time;
6. superseded-by/effective time;
7. consumer cutoff or frozen-run time.

The audited release paths are mutable and may be refreshed after source/stat
corrections. Current TIBER player-season records can carry
`source_updated_at: null`, so they cannot establish which correction state
supplied an earlier run. A later qualification audit must pin and cite the
source's actual publication/correction policy rather than assume a weekday
cadence.

nflreadpy and nflfastR code licenses do not automatically license the
underlying NFL data. Internal operator approval can authorize TIBER work, but it
cannot grant third-party storage, derivation, redistribution, or attribution
rights. Those decisions require the applicable source terms and rights owner.

The closed `AGENTS.md` classification below is separate from capability status
and admission. `external_candidate` means only eligible for a later, separately
authorized governed experimental mirror after every listed rights and semantics
gate passes; it does not admit or authorize a source. `schema_reference_only`
permits code or schema vocabulary to inform design while source rows remain
unusable.

Classification states eligibility class, not clearance. `external_candidate`
never softens a blocked admission state: the PFR-sourced snap asset is
classified as a candidate because a proposed contract depends on its rows,
while its admission remains blocked until a PFR-specific rights and semantics
review passes.

| Candidate source | `AGENTS.md` classification | Owner/lineage and exact inspected terms ref | Access/storage/derivation/redistribution/attribution | Availability/correction evidence | Admission state |
| --- | --- | --- | --- | --- | --- |
| nflreadpy loader code | `schema_reference_only` | nflreadpy project at `66bb305e...`; `LICENSE.md` (MIT) and `pyproject.toml` | Public code access and MIT code use; **does not transfer rights to downloaded data**. | Loader version and constructed URLs are pinned; Data currently allows `>=0.1.0`, so build reproducibility is unresolved. | Code may inform a source adapter; no dataset admitted. |
| 2025 player-week stats asset | `external_candidate` | Public nflverse release path above, reached through pinned `src/nflreadpy/load_stats.py`; underlying NFL/stat-owner terms remain applicable and were not resolved here. | Public no-credential retrieval succeeded. Intended TIBER storage, derivation, redistribution, and required attribution remain unresolved. | Mutable release URL; retrieval date and byte hash recorded, but publication time and correction ledger absent. | Candidate only; rights and revision qualification required. |
| 2025 weekly-roster asset | `external_candidate` | Public nflverse release path above, reached through pinned `src/nflreadpy/load_rosters_weekly.py`; original roster lineage/owner terms not proven by this audit. | Public no-credential retrieval succeeded. Storage, derived membership publication, redistribution, and attribution remain unresolved. | Weekly grain observed; mutable release, publication/effective-time semantics, and correction policy unresolved. | Candidate only; no roster/status semantics admitted. |
| Player master/crosswalk asset | `external_candidate` | Public nflverse release path above, reached through pinned `src/nflreadpy/load_players.py`; aggregates multiple provider identifiers whose underlying terms were not separately resolved. | Public no-credential retrieval succeeded. Exact-ID analysis is allowed for this audit; persistent storage, republishing provider IDs, derivation, redistribution, and attribution remain unresolved. | Mutable current snapshot; no historical effective-date or correction chain proven. | Candidate bridge only; no fuzzy join or governed identity admission. |
| 2025 PFR snap-count asset | `external_candidate` | Public nflverse mirror reached through pinned `src/nflreadpy/load_snap_counts.py`; source is documented as Pro Football Reference, whose underlying terms control the data. | Public no-credential retrieval succeeded. PFR-derived storage, transformation, redistribution, and attribution have not been approved. | Mutable release; source denominator, publication clock, and revisions unresolved. | Admission is blocked pending explicit rights/semantics review; probe evidence remains non-governed. |
| nflfastR/PBP producer candidate | `schema_reference_only` | nflfastR at `0489133d...`; `LICENSE.md` (MIT), `R/helper_tidy_play_stats.R`, `R/aggregate_game_stats_def.R`, and `R/top-level_scraper.R`; underlying NFL play data terms are separate. | Only public code was inspected. No PBP bytes were downloaded or admitted; future storage/derivation/redistribution/attribution requires source review. | Producer logic exposes candidate participant relationships, not a frozen data revision or correction history. | Code-path candidate only; event evidence remains absent. |
| FTN participation candidate | `schema_reference_only` | Existing Data audit `docs/data/nflverse-participation-route-proxy-audit.md` documents FTN-via-nflverse lineage, attribution, and CC-BY-SA handling concerns. No exact 2025 snapshot or columns were verified here. | No new access occurred. Any use must satisfy FTN/nflverse attribution, share-alike, storage, and redistribution obligations identified by a dedicated rights review. | Exact publication, retrieval, availability, and correction clocks for this use are unverified. | Absent; not an admitted alignment or deployment source. |

This rights table is a stop condition, not legal clearance. The later source
qualification must attach the actual terms/version or owner approval for each
input and must record a per-input decision for access, local storage, derived
artifact publication, redistribution, and attribution.

## Event-bundle invariant

A single play may truthfully yield all of the following:

```text
solo/assist tackle + TFL + sack/half-sack + forced fumble
provider-defined non-sack QB hit
recovery + return yards + defensive touchdown
pass defended + interception + lateral/return yards + defensive touchdown
```

The pinned nflfastR producer treats its QB-hit participant slots as non-sack
hits. Another provider or fantasy platform may use different stacking
semantics. Data must preserve the provider-defined facts, definitions, and
play/bundle relationships rather than assert that every sack also carries a QB
hit. A downstream league adapter may intentionally award several scoring
categories only when its exact scoring/stat contract does so. Neither Data nor
Role-and-opportunity may pre-collapse truthful events to a point total or
silently “deduplicate” them.

## Golden traces

### Travis Hunter — one person, multiple lanes and position observations

The evidence is unusually diagnostic:

- live player-week stats: GSIS `00-0040718`, `CB`/`DB`, JAX, seven regular-season
  rows (weeks 1–7), with both receiving and defensive fields on the same row;
- observed defensive aggregate over those rows: 10 solo tackles, 4 tackle
  assists, 1 tackle-with-assist credit, and 3 passes defended;
- player master: the same GSIS ID, PFR `HuntTr00`, `CB`/`DB`, while another
  source-position field (`pff_position`) says `WR`;
- snap counts: PFR `HuntTr00`, position `WR`, with both offensive and defensive
  snaps in every week 1–7;
- weekly roster primary `position` and `depth_chart_position`, plus current
  TIBER roster/PPR evidence: `WR`; the raw roster's separate `ngs_position`
  observations include `CB`, `SLOT_WR`, and blank values;
- current TIBER Sleeper crosswalk: one canonical seed labeled `WR`.

Selected snap proof:

| Week | Offensive snaps/share | Defensive snaps/share | Special teams |
| ---: | ---: | ---: | ---: |
| 1 | 42 / .64 | 6 / .09 | 0 |
| 2 | 42 / .59 | 43 / .62 | 0 |
| 3 | 37 / .53 | 43 / .68 | 3 / .11 |
| 4 | 38 / .56 | 9 / .14 | 0 |
| 5 | 39 / .67 | 25 / .39 | 0 |
| 6 | 59 / .78 | 22 / .40 | 0 |
| 7 | 67 / .87 | 14 / .20 | 0 |

No one source-position label can represent this truth. The next identity
contract needs one canonical person plus independently scoped football evidence
lanes and source-position observations. Platform WR/DB eligibility remains a
separate, effective-dated Fantasy/provider fact. A defensive role profile and
an offensive role profile may link to the same person; their bytes and scores
must not be blended.

### Caleb Downs — source-backed draft fact, unresolved identity, no NFL role

The promoted 2026 draft-results artifact contains Caleb Downs as `S`, Dallas,
round 1 / overall pick 11, with `player_id: null` and
`source_verified_player_id_unresolved`. That is a useful draft fact. It is not
NFL participation, alignment, opportunity, or a defensive rookie profile.
Its embedded source citation says the draft tracker was published 2026-04-25;
the committed row says `generated_at: 2026-05-17T00:00:00Z`. No source
retrieval timestamp or correction/supersession history is present.

The frozen player master independently contains a 2026 candidate identity for
Caleb Downs: GSIS `00-0040865`, PFR `DownCa00`, `SAF`/`DB`, Dallas, and raw
`status=ACT`. That status is a source observation, not governed active/gameday
availability. The master snapshot was retrieved and hashed on 2026-08-04, but
its source publication, field-effective, correction, and supersession clocks
are unavailable. The promoted draft row has no source ID, while the master
row's draft fields are blank. Under this audit's exact-ID-only rule the two rows
cannot be joined by display name. No Downs row exists in the bounded 2025
stats, snap, or weekly-roster probes. No college evidence source or
college-evidence availability clock was inspected. The draft fact therefore
remains exact-ID-unlinked and unadmitted even though an upstream identity
candidate now exists.

Until a canonical identity and NFL observations exist, Downs must remain
unresolved for the governed draft linkage and unsupported for NFL
Role-and-opportunity. “Kyle Hamilton-lite” is an operator hypothesis or future
inspectable comparison, not Data truth. A later comparison must emerge from
source-backed box/deep/slot/rush/coverage deployment fingerprints without
leaking future NFL outcomes into predraft evidence.

## Bounded off-ball-linebacker pilot

**Decision at this ref: rejected for implementation; retained as the preferred
source-qualification cohort.** The current labels cannot select the cohort
honestly.

Why it remains the preferred first population:

- weekly membership, GSIS identity, snaps, tackle/TFL/sack/hit/coverage outcome
  aggregates, and correction concerns are all visible in one tractable cohort;
- three-down versus rotational participation can be tested without fantasy
  points;
- Role-and-opportunity can begin with observed participation and explicit
  unknown alignment rather than pretending all defensive positions are solved.

Why implementation is rejected now:

- 2,859 of 3,213 LB-group rows use generic `LB`; only 53 say `ILB`, 77 `MLB`,
  and 224 `OLB`;
- generic `LB` and `OLB` cannot be silently mapped to off-ball versus edge;
- snap evidence requires the exact PFR-to-GSIS bridge and unresolved-ID policy;
- no audited rush/run/coverage or box/slot alignment denominator exists;
- event corrections and bundle semantics are not frozen.

The follow-up may admit a historical pilot only after declaring seasons/weeks,
an exact population rule independent of fantasy points, explicit exclusions,
minimum participation, and unresolved-role behavior. It must include players
with varied snap stability and deployment; selecting only high scorers would
invalidate the role/opportunity test.

## Smallest honest next contract family — proposal only

Do not widen the current offensive `positionSchema` or
`roleOpportunityRecord` in place. The evidence has different semantics and
failure modes. The recommendation is **four separate additive contracts** plus
a small manifest that pins their compatible versions and source receipts. Do
not use one all-purpose envelope: identity/membership, participation, events,
and derived weekly evidence revise on different clocks and must be independently
replaceable.

| Candidate contract | Candidate paths | Minimum semantics |
| --- | --- | --- |
| Defensive identity/membership v0 | `src/contracts/v1/defensiveIdentityMembershipV0.ts`; `schemas/defensive_identity_membership_v0.schema.json`; `exports/candidates/idp/defensive_identity_membership_2025_v0.json` | Canonical/source IDs, exact bridge evidence, team/week/status observations, source-position observations with source clock, conflicts/unresolved state. No role or eligibility assignment. |
| Defensive participation v0 | `src/contracts/v1/defensiveParticipationV0.ts`; `schemas/defensive_participation_v0.schema.json`; `exports/candidates/idp/defensive_participation_2025_v0.json` | GSIS plus original PFR ID, game/week/team, offense/defense/ST snaps and source percentages, denominator provenance, zero-vs-missing state, source receipt. |
| Defensive event bundle v0 | `src/contracts/v1/defensiveEventBundleV0.ts`; `schemas/defensive_event_bundle_v0.schema.json`; `exports/candidates/idp/defensive_event_bundle_2025_v0.json` | Game/play/event IDs, event type, participant ID, credit fraction, yards, lateral/return linkage, nullified-play state, bundle ID, provider revision. No fantasy points. |
| Defensive player-week evidence v0 | `src/contracts/v1/defensivePlayerWeekEvidenceV0.ts`; `schemas/defensive_player_week_evidence_v0.schema.json`; `exports/candidates/idp/defensive_player_week_evidence_2025_v0.json` | Deterministic view over admitted membership/participation/events; explicit aggregates, denominators, missingness, source/bundle hashes, correction cutoff. |
| Defensive evidence compatibility/receipt manifest v0 | `src/contracts/v1/defensiveEvidenceManifestV0.ts`; `schemas/defensive_evidence_manifest_v0.schema.json`; `exports/candidates/idp/DEFENSIVE_EVIDENCE_V0_MANIFEST.json` | Exact contract/artifact versions and hashes, source receipts, population declaration, correction cutoff, validation results, and explicit no-promotion/no-downstream-activation flags. |

### Required, nullable, enum, and unit decisions

| Contract | Required fields | Nullable/blocked fields | Enums and units |
| --- | --- | --- | --- |
| Identity/membership | `schema_version`, `membership_observation_id`, `season`, `week`, `team`, at least one namespaced `source_id`, `source_position_observations`, `identity_state`, `source_receipt_id` | `tiber_player_id`, `gsis_id`, `pfr_id`, normalized roster status, source effective interval when unavailable | `identity_state = resolved \| unresolved \| conflicted`; raw position retained plus `source_position_group = DL \| LB \| DB \| other \| unknown`; week is integer; no role/eligibility enum |
| Participation | `schema_version`, `game_id`, `season`, `week`, `team`, original namespaced player key, `participation_state`, `source_receipt_id` | resolved GSIS/TIBER ID, `defense_snaps`, `defense_snap_fraction`, offense/ST counts/fractions, denominator ID | snap count is a nonnegative integer; fraction is decimal `[0,1]`; `observed` requires positive `defense_snaps`, `explicit_zero` requires exactly `0`, and `unavailable` requires `null`; phase fields remain separate |
| Event bundle | `schema_version`, deterministic `event_id`, `bundle_id`, `game_id`, `play_id`, event ordinal, namespaced participant key, `event_type`, `credit`, `play_validity`, `revision_state`, `source_receipt_id` | resolved canonical ID, event yards, return yards, linked/lateral event ID, forced/recovered target ID, predecessor event/revision ID, provider correction/effective timestamps | `event_type = solo_tackle \| tackle_with_assist \| tackle_assist \| tackle_for_loss \| sack \| quarterback_hit \| pass_defended \| interception \| forced_fumble \| fumble_recovery \| safety \| blocked_kick \| defensive_touchdown`; the two assist-related provider credits remain distinct; partial sacks use decimal credit `(0,1]`; yards are signed integers; `play_validity = valid \| nullified \| no_play \| unknown`; orthogonal `revision_state = original \| corrected \| superseded \| unknown`; unknown revision state fails closed for corrected-history rollups |
| Player-week evidence | `schema_version`, season/week/team/player key, `evidence_cutoff`, exact input contract versions/hashes, `availability_state`, scoring-neutral aggregate block, `source_receipt_ids` | canonical ID and every unsupported aggregate/denominator | counts are nonnegative numbers preserving fractions; yards are signed; `availability_state = observed \| explicit_zero \| partial \| unavailable`; null never coerces to zero |
| Compatibility/receipt manifest | manifest/schema version, all artifact paths/hashes, all source-receipt IDs, supported population/window, build/validation commands and results, correction cutoff, authority flags | source publication revision only when the source exposes none; nullable value must carry reason | `validation_status = passed \| failed`; all authority flags are booleans and must remain false for promotion, Forecast use, and production use in the candidate |

The initial provider mapping must also be exact and lossless:

| Pinned nflfastR participant slot | Defensive event type | Source-native weekly reconciliation field |
| --- | --- | --- |
| `tackle_with_assist_1_player_id` or `tackle_with_assist_2_player_id` | `tackle_with_assist` | `def_tackles_with_assist` |
| `assist_tackle_1_player_id`, `assist_tackle_2_player_id`, `assist_tackle_3_player_id`, or `assist_tackle_4_player_id` | `tackle_assist` | `def_tackle_assists` |

This is a proposed mapping to validate against frozen PBP, not an admitted
event source. The pinned nflfastR top-level schema exposes both
`tackle_with_assist` slots and all four `assist_tackle` slots, while the pinned
weekly aggregation code's `tackle_vars` currently selects only
`tackle_with_assist_1_player_id` and `assist_tackle_1_player_id` through
`assist_tackle_2_player_id`. Therefore the weekly aggregate is not presumed to
be a complete checksum for the omitted participant slots; the follow-up must
test and reconcile that producer limitation explicitly. The event validator
must reject any transform that drops an exposed slot or folds these two
participant-credit types into one generic assisted-tackle event.

The contract source receipt must itself require source URL/family, source-code
ref or dataset revision when available, exact byte hash, retrieval timestamp,
artifact build timestamp, correction/supersession fields, rights/attribution
state, and supported population declaration.

Source-native weekly aggregates and play-derived rollups must remain separately
identified observations. The builder may reconcile them, but it must not force
equality or overwrite one with the other: scorer/provider credit rules,
correction clocks, and play parsing can differ. Any mismatch belongs in an
explicit reconciliation ledger with both source receipts intact.

### Supported population and migration boundary

The first candidate, if the follow-up gates pass, is limited to frozen 2025
regular-season source rows and exact-ID joins. It is **not** a full current NFL
universe. Membership coverage must reconcile the position-filtered roster,
defensive-stat, and positive-defensive-snap populations so Hunter-like players
remain visible. The off-ball-LB validation cohort is a declared subset of that
candidate, not the contract's whole supported population.

Migration is additive:

- leave `src/contracts/v1/enums.ts`, existing offensive artifacts, and their
  validators byte-for-byte unchanged;
- write only candidate artifacts under `exports/candidates/idp/` until a later
  independent promotion decision;
- retain original provider keys alongside any resolved canonical ID so a bridge
  correction does not rewrite source facts;
- require downstream consumers to opt into exact defensive contract versions
  and fail closed on unsupported/missing blocks;
- do not let Role-and-opportunity consume the weekly view until Data's
  membership, participation, event, and cutoff receipts validate;
- do not use Fantasy's legacy IDP ingest as upstream evidence or silently swap
  it to the candidate;
- keep platform eligibility and league scoring outside these contracts.

Candidate tests for a separately activated implementation:

- `test/defensiveIdentityMembershipV0.contract.test.ts`;
- `test/defensiveParticipationV0.contract.test.ts`;
- `test/defensiveEventBundleV0.contract.test.ts`;
- `test/defensivePlayerWeekEvidenceV0.contract.test.ts`;
- `test/defensiveEvidenceManifestV0.contract.test.ts`;
- deterministic Python source/build tests under `tests/`;
- negative fixtures for missing IDs, the three unresolved PFR IDs, conflicting
  source positions, duplicate player-game rows, half sacks, multi-participant
  tackles/recoveries, lateral returns, nullified plays, stat corrections,
  missing player-weeks, and Hunter's two-way lanes;
- `test/fixtures/idp/defensive_event_bundle.collapsed_tackle_credits.json`,
  which must fail because the two provider tackle-credit types were collapsed;
- exact manifest negatives:
  `test/fixtures/idp/defensive_evidence_manifest.bad_receipt.json`,
  `test/fixtures/idp/defensive_evidence_manifest.bad_hash.json`, and
  `test/fixtures/idp/defensive_evidence_manifest.authority_enabled.json`.

Proposed deterministic command surface for that later issue (the named scripts
do not exist and are not authorized by this audit):

```bash
python scripts/audit_defensive_source_availability_2025.py --receipts docs/receipts/idp-2025.json
python scripts/build_defensive_evidence_v0.py --season 2025 --receipts docs/receipts/idp-2025.json
python scripts/validate_defensive_evidence_v0.py --season 2025
python scripts/validate_defensive_evidence_manifest_v0.py --manifest exports/candidates/idp/DEFENSIVE_EVIDENCE_V0_MANIFEST.json
npm test -- test/defensiveIdentityMembershipV0.contract.test.ts test/defensiveParticipationV0.contract.test.ts test/defensiveEventBundleV0.contract.test.ts test/defensivePlayerWeekEvidenceV0.contract.test.ts test/defensiveEvidenceManifestV0.contract.test.ts
python -m pytest tests/test_defensive_evidence_v0.py
sha256sum exports/candidates/idp/*.json
```

The source audit must fail on a receipt/hash mismatch before parsing rows. Two
independent builds from the same frozen inputs must produce byte-identical
candidate artifacts.

Exact names remain proposals until the operator reviews this audit. The design
decision proposed here is separate versioned artifacts joined by exact keys and
one compatibility/source-receipt manifest; a later contract issue may rename
paths but must not collapse the independent revision clocks without new
evidence.

## Required follow-up gates

Before Data contract implementation:

1. pin the nflreadpy/source-code version and freeze exact source receipts;
2. complete source-rights/attribution review for player stats, rosters, player
   master, PFR snaps, play-by-play, and any FTN participation use;
3. audit multi-season defensive row coverage, detailed positions, duplicates,
   corrections, and wrong-season/postseason behavior;
4. formalize the GSIS/PFR bridge, collision checks, and unresolved-ID policy;
5. define source-position observations without assigning canonical role or
   platform eligibility;
6. run a play-level participant/event audit covering credit fractions, stacked
   events, laterals, penalties/nullified plays, and revisions;
7. decide whether open evidence can support pass-rush/run/coverage and player
   alignment; otherwise make those capabilities explicitly unavailable;
8. define zero/null/missing and missed-game behavior;
9. obtain operator approval for the smallest contract and bounded cohort;
10. decide and separately authorize the typical machine-readable companion at
    `docs/audits/idp-defensive-evidence-readiness-audit-2026-08-04.json`; D0
    intentionally defers it because #232 authorized exactly one Markdown
    deliverable.

If any gate requires a paid/private provider, new credentials, redistribution
rights, or spending, stop for separate operator authority.

## Acceptance review

- Exact repository/source-code refs and source-byte hashes are recorded.
- Current offense-only filters and IDP population exclusion are proven.
- Identity, membership, snaps, deployment, weekly events, atomic bundles,
  corrections, provenance, and rights are assessed separately.
- Every issue-required candidate field has a source/ref, field meaning, units,
  scope/grain, clock, identity key, correction state, rights disposition,
  failure risk, and exactly one allowed capability status recorded across the
  path/source ledgers and capability matrix.
- Source position, canonical football role, platform eligibility, league-slot
  legality, and fantasy value remain separate.
- Source zero, missing player-week, unsupported field, and unresolved identity
  are not collapsed.
- Hunter proves one identity with independent evidence/profile lanes.
- Downs remains an unresolved defensive rookie trace, not an invented NFL role.
- The off-ball-LB pilot is rejected for implementation at this ref and retained
  only as the preferred source-qualification cohort; that decision uses
  evidence, not scoring.
- No existing contract/artifact changed; no source bytes were admitted or
  promoted; no downstream consumer was activated.

## Terminal decision

```text
idp_data_foundation_requires_source_followup
```
