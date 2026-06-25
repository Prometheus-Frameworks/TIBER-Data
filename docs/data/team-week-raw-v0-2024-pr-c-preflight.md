# team_week_raw_v0 2024 PR C preflight: window and derivation rule gate

## Status

This is the PR C preflight for TIBER-Data issue #162, following PR A
(`docs/data/team-week-raw-v0-2024-source-artifact-spec.md`) and PR B
(`docs/data/team-week-raw-v0-2024-source-probe.md`).

This document does not ingest data, does not generate a real or candidate
artifact, does not emit a validation report, does not emit a lineage
manifest, does not promote any governance status, does not modify
TIBER-Teamstate, and does not change PPM behavior.

Its job is narrower than PR A/B: PR A specified the contract and field
inventory, PR B classified field availability against candidate sources.
This PR decides or explicitly gates the deterministic *rules* (window,
play inclusion, neutral script, thresholds, source assumptions, pace,
drives/red-zone, pressure, metadata, emission checks, governance) that a
future PR C must apply identically to every team/week so the resulting
artifact is reproducible and honestly labeled.

Every rule below is marked one of:

- **LOCKED** — adopted as the candidate policy PR C must implement as written
  unless a later spec revision changes it. "Locked" means *decided for this
  spec*, not *governed*; it does not authorize artifact emission and does not
  by itself satisfy promotion review.
- **GATED** — explicitly not decided here. PR C must not silently choose a
  default; either the gate is resolved by an explicit follow-up decision, or
  the affected field stays null/deferred with the policy in §8/§9.

## 1. Window decision

**LOCKED**: the source artifact's primary build window is the **full Week
1-18 2024 regular season**, all 32 teams, postseason excluded.

Rationale:

- The source artifact is team-state-only context (pace, EPA, success,
  explosive rate, drives, red zone), not a fantasy-scoring artifact. There is
  no team-state reason to truncate before Week 18; doing so would discard
  real team-week observations for no derivation-correctness benefit.
- TIBER-Teamstate #50 §6 and TIBER-Data #162 frame 2024 team context as a
  predictor for a 2025 target, not an explanation of 2024 outcomes. Full
  regular-season coverage maximizes usable predictor history without
  crossing the leakage boundary, since the cutoff that matters is relative
  to the 2025 target window, not relative to Week 18 vs Week 17.
- A fantasy-aligned window (e.g. excluding Week 18, or excluding weeks past
  a typical fantasy-playoff cutoff) is a **downstream filter**, not a
  separate acquisition. It can be derived from the full-window artifact by
  selecting a week subset; it must not be built as a second, independently
  acquired source artifact.

Consequences locked alongside this decision:

- `season=2024`, expected weeks = `1..18` inclusive, for all 32 teams.
- Each team is expected to contribute up to 18 team-week rows; bye weeks
  produce no row for that team/week (no zero-filled or synthetic bye row).
- Regular-season neutral-site/international games are in-window if they
  occurred within Weeks 1-18 of the 2024 regular season; no regular-season
  game is excluded for venue reasons. Postseason and the Pro Bowl are always
  excluded, regardless of week number or venue.
- A fantasy-aligned *view* (if ever needed downstream) is documented as
  "rows where `week <= N`" filtered from this artifact, not a new source.

**GATED**: the exact value of `N` for any future fantasy-aligned view, and
whether such a view is ever materialized as its own artifact, is not decided
here and is out of scope for PR C.

## 2. Play inclusion rules

These rules govern which raw plays count toward `offensivePlays` and the
rate/efficiency fields derived from it. They apply to the team in possession
on offense unless stated otherwise.

| Rule | Status | Policy |
| --- | --- | --- |
| Offensive play inclusion | **LOCKED** | A play counts toward `offensivePlays` only if it is a designated scrimmage play with a recorded offensive result: pass attempt, sack, scramble, or rush attempt (including QB kneels/spikes, counted per their own rows below). Special-teams plays are never offensive plays (see special-teams row). |
| No-plays | **LOCKED** | Plays nullified entirely (no down consumed, no result recorded — e.g. pre-snap dead-ball plays with no penalty accepted) are excluded from `offensivePlays` and from every rate/efficiency numerator and denominator. |
| Penalties | **LOCKED** | If a penalty is accepted and the underlying play has no statistical result (e.g. false start, delay of game, dead-ball foul before the snap resolves a play), the play is excluded, same as a no-play. If a penalty is accepted on a play that still has a recorded statistical result (e.g. defensive holding with the pass result also recorded by the source), the underlying play's offensive result is included and counted under its natural play type; the penalty itself does not create or remove a play. |
| Kneels | **LOCKED** | QB kneels are excluded from `passRate`, `neutralPassRate`, `rushRate`, `epaPerPlay`, `passEpaPerPlay`, `rushEpaPerPlay`, `successRate`, and `explosivePlayRate` (they are not competitive snaps). They are excluded from `neutralPlays` by construction (kneels do not occur in neutral script). They still count toward the raw `offensivePlays` total per the offensive-play-inclusion rule above, but are **excluded from the `secondsPerPlay` pace denominator and from the elapsed-time numerator** — `secondsPerPlay` measures competitive offensive pace, not clock-liquidation behavior; see §6. |
| Spikes | **LOCKED** | Same rate/efficiency and `neutralPlays` treatment as kneels. Counted toward the raw `offensivePlays` total, but **excluded from the `secondsPerPlay` pace denominator and from the elapsed-time numerator** for the same competitive-pace reason — a spike is clock-management, not tempo, and must not make a team look artificially fast; see §6. |
| Sacks | **LOCKED** | A sack counts as a pass play (part of the dropback total) for `passRate`, `neutralPassRate`, and `passEpaPerPlay`. A sack is never counted toward `explosivePlayRate` (a loss cannot be explosive) and is separately counted in `sacksAllowed`. |
| Scrambles | **LOCKED policy, GATED column mapping** | A scramble (a called pass that becomes a designed-look run by the QB) counts toward `passRate`/`neutralPassRate`/dropback totals for play-calling purposes, consistent with the standard nflverse dropback definition (pass attempts + sacks + scrambles) — this holds regardless of source schema. EPA attribution policy is locked: if the retrieved nflverse release exposes a standard dropback/pass indicator that includes scrambles, scramble EPA must be attributed to `passEpaPerPlay` under that indicator, not split off into `rushEpaPerPlay`. If the source instead exposes only a coarse rush/pass flag that cannot reliably distinguish scramble-from-designed-run semantics, PR C must record the exact column mapping it used in the transform code path and **fail closed** for the affected `passEpaPerPlay`/`rushEpaPerPlay` split on those rows (or mark the split as blocked) rather than guessing an attribution. No custom EPA model and no invented mapping are permitted either way. Only the literal source column names remain gated, since they are unknown until retrieval. |
| Aborted plays | **LOCKED** | Plays with no clean snap/exchange and no recorded offensive result (e.g. botched snap with no result) are excluded from `offensivePlays` and all rate/efficiency fields, same as no-plays. The excluded-play count must be recorded in build metadata for transparency, not silently dropped. |
| Special-teams exclusions | **LOCKED** | Punts, kickoffs, field goal attempts, extra-point attempts, and two-point conversion attempts are entirely excluded from offensive-snap accounting: they never count toward `offensivePlays`, `neutralPlays`, `drives`, `redZoneTrips`, or any play-rate/efficiency field (`passRate`, `neutralPassRate`, `rushRate`, `epaPerPlay`, `passEpaPerPlay`, `rushEpaPerPlay`, `successRate`, `explosivePlayRate`, `redZoneTdRate`). This exclusion does **not** extend to `pointsFor`/`pointsAgainst`: those two fields are full-game team score totals and must include points scored via field goals, extra points, two-point conversions, defensive touchdowns, and special-teams touchdowns. `pointsPerDrive` (§7) is computed from this full-game `pointsFor`, not an offense-only point total. |
| End-of-half / end-of-game edge cases | **LOCKED (partial)** | Any play that occurs after a half/game-ending whistle with no recorded result is excluded (same as no-play). Kneels/spikes at the end of a half/game follow the kneel/spike rule above. **GATED**: whether a half-ending live snap with a real result (e.g. a Hail Mary attempt as time expires) requires any special handling beyond its natural play-type classification — default is no special handling, but this must be confirmed once real plays are inspected in PR C. |

## 3. Neutral-script rules

**LOCKED** candidate definition (standard nflverse-community neutral-script
convention; adopted as the working definition for this artifact, not
asserted as the only valid one):

- **Score margin threshold**: offense's score differential is within 8
  points (i.e. `-8 <= score_differential <= 8` from the offense's
  perspective). Eight points reflects one possession inclusive of a
  touchdown, extra point, and a two-point-conversion swing.
- **Game clock / window**: all of Q1-Q3 are eligible by default (subject to
  the score-margin filter). In Q4, plays are eligible only while more than
  5:00 remains on the game clock; the last 5 minutes of regulation are
  treated as a script in which leverage/clock strategy can dominate
  play-calling regardless of margin, so they are excluded from "neutral"
  even if the margin condition is met.
- **Period exclusions**: overtime is excluded entirely from `neutralPlays`
  (and from `neutralPassRate`). Overtime is rare, sudden-death-flavored, and
  not comparable in structure to a regulation neutral script.
- **Garbage-time filter**: included by construction — the margin and
  late-Q4 exclusions above are the garbage-time filter. No separate garbage
  time flag is layered on top.
- **Zero-denominator convention**: `neutralPassRate = neutral-script pass
  plays / neutralPlays`. If a team-week has `neutralPlays == 0` (e.g. a
  one-sided game where the trailing/leading team never had a snap inside
  the neutral-script window), `neutralPassRate` must be emitted as `null`
  — an undefined ratio, not a fabricated `0` or `1`. The same
  zero-denominator-is-null convention applies to any other ratio field
  whose denominator can be legitimately zero for a real team-week (see
  `redZoneTdRate` in §7). This is independent of the `pressureRateAllowed`
  deferral in §8: that field is null because no governed source has been
  identified yet, not because of a zero denominator.

**GATED**: this 8-point / 5-minute convention is a candidate, not a
contractual constant. If a different neutral-script definition is preferred
before PR C executes, it must be changed here (in a spec revision) before
implementation, not adjusted ad hoc inside the build script.

## 4. Explosive-play thresholds

**LOCKED** candidate thresholds (standard public nflverse-community
convention):

- **Pass explosive threshold**: a completed pass (not a sack, not an
  incompletion) gaining 15 or more yards.
- **Rush explosive threshold**: a rush attempt (including scrambles, per
  the scramble policy in §2) gaining 10 or more yards.
- **Thresholds differ by play type**: yes — 15 yards for pass, 10 yards for
  rush, as above. There is no further split by down/distance or by team.
- **Sacks/no-plays excluded**: yes. Sacks (negative or zero yardage by
  definition of the play) and no-plays/aborted plays (no recorded gain) can
  never count toward `explosivePlayRate`, consistent with §2.

`explosivePlayRate` denominator is the same included-offensive-play set used
for `epaPerPlay` (i.e. excludes kneels, spikes, no-plays, aborted plays, and
special-teams plays; sacks are in the denominator as pass plays but can never
satisfy the explosive condition).

**GATED**: whether these thresholds should be neutral-script-only (i.e.
computed only over `neutralPlays`) or computed over all included offensive
plays. This spec defaults to **all included offensive plays** (not
neutral-script-restricted) because `explosivePlayRate` is listed in the
contract as a standalone field, separate from `neutralPlays`/
`neutralPassRate`. This default must be confirmed, not silently overridden,
if a later reviewer expects a neutral-script-scoped explosive rate.

## 5. EPA and success-rate source assumptions

| Requirement | Status | Policy |
| --- | --- | --- |
| Selected source family | **LOCKED** | nflverse, retrieved via `nflreadpy` (the path already used by this repo's existing FORGE/upstream scaffold code), specifically `nflreadpy.load_pbp([2024])` for play-level fields. This matches PR A/PR B's documented candidate path; this PR does not introduce a new loader. |
| EPA source/model/version | **GATED** | The artifact must consume the `epa` column exactly as shipped by the selected nflverse play-by-play release for the retrieved season — this build must not compute or fit its own EP/WP model. The specific nflverse data release tag/version and `nflreadpy` package version are not known until retrieval and must be recorded at retrieval time (see §9); they cannot be locked in a docs-only PR. |
| Success-rate column vs deterministic derivation | **LOCKED policy, GATED value** | If the retrieved nflverse play-by-play release ships a `success` column, it must be consumed directly and not re-derived. If it does not, the deterministic fallback is `success = 1 if epa > 0 else 0` per play, applied over the same included-play set as `epaPerPlay`. Which of these two paths applies is unknown until PR C inspects the actual retrieved columns, and the chosen path must be recorded in the transform code path and build metadata. |
| Source retrieval date | **GATED** | Not decided here; must be the actual UTC timestamp recorded at the moment PR C retrieves data, not invented or backfilled. |
| Source version / dataset identifier | **GATED** | Must be the actual nflverse release tag/identifier and `nflreadpy` package version observed at retrieval time, recorded verbatim. |
| Transformation code path | **LOCKED (path convention only)** | A future PR C build script must live under `scripts/` (consistent with `scripts/probe_team_week_raw_v0_2024_sources.py` from PR B) and its exact module path must be recorded in artifact metadata and the lineage manifest. The literal path is not created by this PR. |

## 6. Pace / seconds-per-play rules

| Requirement | Status | Policy |
| --- | --- | --- |
| Game clock source | **LOCKED** | Derived from the selected nflverse play-by-play release's per-play clock/quarter fields (the same source as EPA/success), not a separate pace feed. |
| Elapsed time calculation | **LOCKED** | For each offensive drive/possession, elapsed seconds between consecutive included snaps are summed using within-quarter clock deltas; the clock resets at each quarter boundary (no elapsed time is computed across a quarter break, half break, or change of possession). |
| Play denominator | **LOCKED** | `secondsPerPlay` measures **competitive offensive pace**, not clock-liquidation or clock-management behavior. Only competitive offensive snaps — the same included-play set used for `epaPerPlay`/`explosivePlayRate` per §2/§4, i.e. excluding kneels, spikes, no-plays, aborted plays, and special-teams plays — count toward the `secondsPerPlay` denominator. This supersedes the "all clock-consuming snaps" alternative previously left open: kneels would make a leading team look artificially slow and spikes would make a stopped-clock team look artificially fast, and neither reflects competitive tempo. |
| Period boundaries | **LOCKED** | No elapsed-time interval spans a quarter or half boundary; the first snap of a new quarter/half starts a fresh elapsed-time accumulation. |
| No-play exclusions | **LOCKED** | No-plays and aborted plays (per §2) contribute no snap to the pace denominator, consistent with the competitive-pace policy above. Elapsed clock time attributable *only* to a no-play/pre-snap administrative event (e.g. a pre-snap penalty runoff, a dead-ball foul before the snap) must not be included in the elapsed-time numerator — it is administrative clock consumption, not competitive pace. If the retrieved source's clock fields cannot cleanly attribute a given interval to a no-play/administrative event versus a competitive snap, PR C must record the limitation in build metadata and either fail closed for that interval (exclude it from both numerator and denominator) or mark `secondsPerPlay` as blocked for the affected row/window — it must not impute or guess the split. |
| Kneels/spikes | **LOCKED** | Kneels are excluded from the `secondsPerPlay` denominator, and the elapsed-clock interval attributable *only* to a kneel-down sequence is excluded from the elapsed-time numerator. Spikes are excluded from the `secondsPerPlay` denominator, and the elapsed-clock interval attributable *only* to a spike sequence is excluded from the elapsed-time numerator. Kneels and spikes remain excluded from all rate/efficiency fields per §2/§3 independent of this pace rule. If the retrieved source cannot cleanly identify which plays are kneels/spikes, or cannot cleanly attribute a clock interval to a kneel/spike sequence, PR C must fail closed for this derivation (exclude the ambiguous interval rather than guess) or mark the affected `secondsPerPlay` value as blocked for that row/window — it must not impute or estimate the split. |
| Missing clock values | **LOCKED** | If a play's clock fields are null/unparseable, that play-to-play interval is excluded from the elapsed-time sum and the play is excluded from the pace denominator for that interval; missing clock values must never be imputed or assumed equal to a league-average interval. |

## 7. Drives and red-zone rules

| Requirement | Status | Policy |
| --- | --- | --- |
| Drive counting | **LOCKED** | `drives` counts offensive possessions/drives as identified by the selected source's drive identifier for that team/week, restricted to possessions that contain at least one included offensive play per §2. |
| Drive start/end handling | **LOCKED** | The selected source's drive identifier is accepted as the **drive-boundary authority** for the first candidate artifact: this spec does not redefine drive boundaries (e.g. how a drive start is marked after a turnover vs. a change of possession via punt), and PR C must not implement a custom drive-reconstruction algorithm in the first build unless separately authorized in a future spec revision. Any source-specific drive-id quirks discovered during PR C implementation must be recorded in both the lineage manifest and the validation report, not silently normalized or corrected. |
| Kneel-only drives | **LOCKED** | A drive consisting entirely of kneels (e.g. a closing-the-game victory formation series) still counts toward `drives` (a possession occurred) but contributes no plays to `neutralPlays`, rate fields, or `explosivePlayRate`, consistent with §2/§3. |
| End-of-half drives | **LOCKED** | A drive that ends because the half/game clock expires (no score, no turnover) still counts toward `drives` if it contained at least one included offensive play. |
| Points-per-drive numerator/denominator | **LOCKED** | `pointsPerDrive = pointsFor / drives` for that team/week, using the same `drives` count as above. `pointsFor` is the team's full-game point total (per §2's special-teams note), not limited to offensive-drive scoring. Points are attributed to the week in which the drive occurred, not split across weeks for any reason. |
| Red-zone trip definition | **LOCKED** | A red-zone trip is a drive in which the offense has at least one included offensive play with the line of scrimmage at or inside the opponent's 20-yard line. `redZoneTrips` counts trips, not plays. |
| Red-zone touchdown definition | **LOCKED** | `redZoneTdRate = (red-zone drives ending in an offensive touchdown) / redZoneTrips`. A drive counts as a red-zone touchdown drive only if the scoring play is an offensive touchdown (passing or rushing); defensive/special-teams touchdowns during a red-zone-trip drive do not count toward the numerator. If `redZoneTrips == 0` for a team-week, `redZoneTdRate` must be emitted as `null` (undefined ratio, per the zero-denominator convention in §3), never a fabricated `0`. |
| Touchdown attribution | **LOCKED** | Touchdowns are attributed to the offensive team in possession at the time of the scoring play, per the play-level possession-team field, not by game final score inference. |
| Penalty/no-play effects on drives | **LOCKED** | A no-play/aborted play within an otherwise-valid drive does not remove the drive from `drives`, `redZoneTrips`, or `redZoneTdRate` calculations; it simply contributes no play-level data per §2. A drive is not invalidated by containing excluded plays. |

## 8. Pressure rate allowed

**DEFERRED for the first real candidate artifact.** `pressureRateAllowed`
remains a required field name in the PR A contract, but PR B's probe found
no confirmed pressure column in the standard nflverse weekly-stats or
play-by-play probe path, and this preflight does not identify or approve an
additional charting/provider source.

Decision: **defer, do not silently fill.**

- For the first real (`partial_real_data`) candidate artifact, every row's
  `pressureRateAllowed` must be emitted as an explicit `null`, never a
  zero, league-average, or any other invented numeric placeholder.
- The artifact's metadata must carry a field-level deferral record (e.g.
  `metadata.deferredFields: ["pressureRateAllowed"]`) with a human-readable
  reason ("no confirmed governed pressure-rate source as of PR C preflight")
  so downstream consumers cannot mistake the null for a zero-pressure
  observation.
- `pressureRateAllowed` must be excluded from any "finite numeric required
  field" validation check (§10) for as long as it is deferred; it must not
  be silently reclassified as optional in the PR A contract without a
  contract revision.
- Promotion to `governed_real_data` (TIBER-Data #162 governance section,
  TIBER-Teamstate #50 §5) is **blocked** while `pressureRateAllowed` remains
  a contractually-required field that is null-deferred for every row. This
  block is not lifted by documenting the deferral in a promotion record, by
  a plausible artifact path, by build success, or by passing validation
  (per §11) — only un-deferring the field (next bullet) or a formal
  contract revision can remove this block, and no promotion record may
  silently omit the deferral's existence.
- Un-deferring this field requires a separate, explicitly authorized
  follow-up: either an accepted additional pressure-charting source with its
  own source refs/retrieval metadata, or a contract revision that formally
  makes `pressureRateAllowed` optional for this lane. Neither is decided by
  this PR.

This deferral is unrelated to the zero-denominator-is-null convention in
§3/§7: `pressureRateAllowed` is null for every row because no governed
source exists yet; `neutralPassRate`/`redZoneTdRate` are null only for the
specific team-weeks where their own denominator is genuinely zero, and must
otherwise be computed normally.

## 9. Source metadata requirements

**LOCKED** minimum metadata set. A future PR C build (and its companion
lineage manifest) must record, at minimum, per ingested source and for the
artifact as a whole:

- `sourceName` — e.g. `nflverse play-by-play`, `nflverse weekly team stats`.
- `sourceType` — e.g. `nflverse`, matching PR A's existing source-typing
  vocabulary.
- `retrievalMethod` — exact function/call used (e.g.
  `nflreadpy.load_pbp([2024])`), matching the style already used in PR B's
  probe table.
- `retrievalTimestamp` — UTC ISO-8601 timestamp of the actual retrieval,
  recorded at retrieval time, never backfilled or estimated.
- `packageVersion` — the `nflreadpy` (and any other library) version
  actually installed/used at retrieval time, where available.
- `sourceUrlOrDatasetId` — the nflverse release tag, dataset URL, or other
  stable identifier, where available.
- `transformCodePath` — the repository-relative path of the build script
  that produced the artifact from the raw retrieval (e.g. under `scripts/`).
- `sourceRefs` — the list of raw source artifact ids/paths/URLs consumed,
  matching the `sourceArtifacts` envelope field from the existing
  `team_week_raw_v0` contract.
- `validationReportPath` — the candidate path/id of the validation report a
  future PR C would emit (per PR A: `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json`).
  Not created by this PR.
- `lineageManifestPath` — the candidate path/id of the lineage/source
  manifest a future PR C would emit (per PR A:
  `data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json`).
  Not created by this PR.

All of the above are metadata *requirements*, not values. No example values
are populated here; populating them with real data is PR C's job, not this
preflight's.

## 10. PR C artifact emission gate

**LOCKED** checklist. A future PR C must not emit even a non-promoted
candidate artifact unless all of the following pass:

- All 32 NFL teams present for the selected (Week 1-18, §1) window.
- Expected weeks/window present per team (up to 18 team-week rows per team,
  bye weeks producing no row, per §1).
- No duplicate `(season, week, teamCode)` rows.
- All `teamCode`/`opponentCode` values are valid canonical team
  abbreviations (no unmapped/legacy codes).
- Reciprocal opponent consistency: for every team-week row, the paired
  opponent's row for the same game (where it exists in-window) lists this
  team as its opponent.
- All rate fields (`passRate`, `neutralPassRate`, `rushRate`, `successRate`,
  `explosivePlayRate`, `redZoneTdRate`) are bounded in `0..1` **when their
  own denominator is nonzero**. When the denominator is legitimately zero
  for a team-week (e.g. `neutralPlays == 0` for `neutralPassRate`,
  `redZoneTrips == 0` for `redZoneTdRate`), the field must be `null` per
  the zero-denominator convention in §3/§7, not a fabricated `0` or `1`,
  and that row is not rejected for it.
- All required finite-numeric fields (per PR A §4, minus `pressureRateAllowed`
  while deferred per §8, minus any ratio field that is `null` for a
  given row solely because its own denominator is legitimately zero per
  the zero-denominator convention in §3/§7, minus `secondsPerPlay` for
  any row where it is null-blocked because the source could not cleanly
  separate kneel/spike/no-play clock intervals from competitive pace per
  §6's fail-closed rule, and minus `passEpaPerPlay`/`rushEpaPerPlay` for any
  row where the scramble/dropback split is blocked because the source's
  play-type flags could not reliably distinguish scramble-from-designed-run
  semantics per §2's fail-closed rule) are finite — not `NaN`, not infinite,
  not empty-string-coerced.
- `pressureRateAllowed` is explicitly `null` with the deferral recorded in
  metadata, per §8 — never silently filled.
- If `secondsPerPlay` is null-blocked for any row per §6, that block must be
  recorded in build metadata with a stated reason, in the same style as the
  §8 deferral record — it must never be silently imputed, estimated, or
  backfilled with a league-average value.
- If the `passEpaPerPlay`/`rushEpaPerPlay` scramble split is blocked for any
  row per §2's fail-closed rule, that block must likewise be recorded in
  build metadata with a stated reason — it must never be silently imputed,
  estimated, or defaulted to one split over the other. A builder that hits
  this branch may still emit the candidate artifact with the split fields
  null-blocked and recorded; it is not required to abandon emission entirely,
  provided every other §10 criterion still passes.
- `sourceRefs` is present and non-empty for the artifact and, where the
  contract requires it, per row.
- Retrieval metadata (§9) is present and complete for every source consumed.
- A validation report (candidate path from PR A, still not created by this
  PR) is emitted alongside the candidate artifact, not merely promised.
- A lineage manifest (candidate path from PR A, still not created by this
  PR) is emitted alongside the candidate artifact.
- The artifact's `provenanceStatus` is `partial_real_data` (or an equally
  honest non-governed status) — **no `governed_real_data` claim** is made by
  PR C under any circumstance; promotion is a separate, later, explicitly
  authorized PR D per PR A's PR sequence.

## 11. Governance boundary

Restated and preserved from TIBER-Data #162 and TIBER-Teamstate #50, and
binding on any future PR C/D:

- Public availability of a source (e.g. nflverse being open data) is not
  governance by itself.
- A plausible artifact path or file name (e.g. living under `exports/` or
  `data/manifests/`) is not governance and must never be treated as proof of
  promotion.
- Downstream need (Teamstate or PPM wanting the artifact sooner) is not
  governance and does not relax any criterion in §10.
- `governed_real_data` / `governanceStatus: governed` requires an explicit
  governance marker (`governanceSource: explicit_marker`) set by a human
  promotion review, not inferred from build success or validation passing
  alone.
- Missing or unrecognized governance metadata must fail closed — an artifact
  with absent/unknown governance fields must be treated as ungoverned, never
  defaulted to governed.
- If any future PR materializes a candidate artifact, its interim status
  must be honest: `candidate`, `partial_real_data`, or `ungoverned` as
  appropriate — never `governed`, regardless of how complete the build looks.

## Hard guardrails

This preflight, and any PR that lands it, must not include:

- A real 2024 artifact emission.
- A committed candidate artifact.
- A validation report artifact, other than this docs/spec placeholder
  reference (no data validation output is produced).
- A lineage manifest artifact, other than this docs/spec placeholder
  reference (no lineage output is produced).
- A `governed_real_data` claim.
- TIBER-Teamstate code changes.
- PPM model changes.
- A PPM run.
- Product/Management work.
- Rankings.
- Fantasy advice.
- Invented values for any rule, threshold, or metadata field left **GATED**
  above.
- Placeholder filling of any deferred field (notably `pressureRateAllowed`).
- Path-inference governance.
- Treatment of offline/FORGE proof data (2024 Weeks 1-3, ATL/DET only) as
  sufficient support for full governed 2024 all-32 coverage; it remains
  context-only.

## Relationship to other issues/PRs

- Follows TIBER-Data PR #163 (PR A: spec) and PR #165 (PR B: dry-run probe)
  under TIBER-Data #162.
- Consumes the field classification from PR B's probe (`docs/data/team-week-raw-v0-2024-source-probe.md`)
  and the contract from PR A's spec (`docs/data/team-week-raw-v0-2024-source-artifact-spec.md`).
  Both remain the source of truth for contract/field-classification details
  not restated here.
- Feeds TIBER-Teamstate #50's PR-C step ("partial_real_data`/ungoverned real
  2024 artifact + validation report") — this document is the rule-lock that
  step depends on, not that step itself.
- Tracked from TIBER-Ops #5 as the ML/modeling lane's current continuation
  issue.

## Next step after this PR

Once this preflight is reviewed and any **GATED** items are either resolved
(via a spec revision) or explicitly accepted as still-deferred-with-null-policy,
a separate PR C may implement the build script that retrieves real 2024
nflverse data and emits a `partial_real_data` candidate artifact plus
validation report and lineage manifest, per §10. That PR is not part of this
change.
