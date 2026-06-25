# team_week_raw_v0 2024 source probe

## Status

Dry-run schema mapping only. This report does not create, emit, promote, or validate the future real 2024 artifact.

Spec reference: `docs/data/team-week-raw-v0-2024-source-artifact-spec.md`.

Candidate paths named by the spec remain future-only and were not created by this probe:

- artifact: `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`
- validation report: `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json`
- lineage manifest: `data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json`

## Source availability

| Source | Type | Retrieval method | Available without fetch | Package version | Fetch status | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| nflreadpy / nflverse weekly team stats | nflverse | `nflreadpy.load_team_stats([2024], summary_level="week")` | True | 0.1.5 | not_attempted | Weekly team stats alone do not settle neutral-script, EPA, success, drives, red-zone trips, or pressure-rate requirements.<br>A later source-fetch PR must record retrieval date, source version, and raw source refs. |
| nflfastR / nflverse play-by-play via nflreadpy if exposed | nflverse | `nflreadpy.load_pbp([2024]) or selected deterministic nflverse play-by-play retrieval path` | True | 0.1.5 | not_attempted | The accepted play-by-play loader and EPA/source version remain governance decisions.<br>The probe must not commit real rows; PR C would need a validation report and lineage manifest before candidate emission. |
| existing offline fixture / FORGE proof-of-path data | fixture_or_proof_reference | `committed repo files and existing FORGE audits only` | True | not_available | context_only_not_full_coverage | Insufficient for full governed 2024 all-32 coverage.<br>Must not be promoted by path inference or used as real all-32 source support. |

## Required field mapping

| Field | Classification | Source basis | Deterministic rule needed | Unresolved/blocker |
| --- | --- | --- | --- | --- |
| `season` | `direct` | weekly team stats or play-by-play season column | Normalize to integer season=2024. | None after source availability is confirmed. |
| `week` | `direct` | weekly team stats or play-by-play week column | Normalize to integer NFL week and filter to the unresolved approved window. | Window remains unresolved. |
| `teamCode` | `direct` | weekly team stats team column or play-by-play possession team | Canonicalize to TIBER team abbreviation set before validation. | Team alias policy must be enforced. |
| `opponentCode` | `requires_play_by_play` | play-by-play defensive/opponent team or schedule/game join | Derive from paired game context and validate reciprocal team-game rows. | Weekly team stats alone may not provide opponent. |
| `offensivePlays` | `derivable` | weekly team pass/rush attempts or play-by-play filtered offensive plays | Define included offensive plays and aggregate by team/week. | Play inclusion rules must be settled. |
| `neutralPlays` | `requires_play_by_play` | play-by-play game state | Define neutral script, filter eligible plays, and count by team/week. | Neutral script thresholds are unresolved. |
| `secondsPerPlay` | `requires_play_by_play` | play-by-play game clock / elapsed time | Compute elapsed offensive seconds divided by included offensive plays. | Clock handling, period boundaries, and no-play treatment are unresolved. |
| `passRate` | `derivable` | weekly team pass attempts and offensive plays or play-by-play pass flags | Pass attempts divided by included offensive plays using the same denominator as offensivePlays. | Scramble/sack/dropback treatment must be explicit. |
| `neutralPassRate` | `requires_play_by_play` | play-by-play neutral-script subset | Pass attempts in neutral subset divided by neutralPlays. | Neutral script and pass/dropback treatment unresolved. |
| `rushRate` | `derivable` | weekly team rush attempts and offensive plays or play-by-play rush flags | Rush attempts divided by included offensive plays using the same denominator as offensivePlays. | Kneel/spike/scramble treatment must be explicit. |
| `epaPerPlay` | `requires_play_by_play` | play-by-play EPA field | Average EPA over included offensive plays by team/week. | EPA provider/version and inclusion rules must be recorded. |
| `passEpaPerPlay` | `requires_play_by_play` | play-by-play EPA and pass/dropback flag | Average EPA over included pass/dropback plays by team/week. | Sacks/scrambles/dropbacks must be defined. |
| `rushEpaPerPlay` | `requires_play_by_play` | play-by-play EPA and rush flag | Average EPA over included rush plays by team/week. | Kneels and scrambles must be defined. |
| `successRate` | `requires_play_by_play` | play-by-play success indicator or EPA/down-distance derivation | Aggregate agreed success definition over included offensive plays. | Success definition/source version unresolved. |
| `explosivePlayRate` | `requires_play_by_play` | play-by-play gained yards and play type | Count plays meeting agreed explosive thresholds divided by included plays. | Explosive thresholds unresolved. |
| `drives` | `requires_play_by_play` | play-by-play drive id or drive table | Count offensive drives by team/week after drive inclusion exclusions. | End-of-half/game and kneel-only drives need rules. |
| `pointsPerDrive` | `requires_play_by_play` | drive count plus points scored by drive/team | pointsFor divided by included offensive drives, or sum drive points divided by drives. | Drive scoring attribution must be explicit. |
| `pointsFor` | `direct` | weekly team stats points/total_points or game score | Normalize source points scored by team/week. | Confirm source column semantics include team points, not fantasy points. |
| `pointsAgainst` | `requires_play_by_play` | schedule/game score join or opponent paired rows | Derive from opponent score for the same game/week and validate reciprocity. | Weekly team stats alone may not provide points against. |
| `pressureRateAllowed` | `requires_additional_source` | not confirmed in weekly team stats or standard play-by-play probe | If available, divide pressures allowed by governed dropback/pass-block denominator. | Likely needs charting/provider source or explicit deferral. |
| `turnovers` | `requires_play_by_play` | play-by-play interception/fumble turnover events | Attribute offensive turnovers to possession team by week. | Aborted plays, laterals, and special teams exclusions need rules. |
| `sacksAllowed` | `requires_play_by_play` | play-by-play sack/dropback fields | Attribute offensive sacks to possession team by week. | Scramble/aborted-play treatment must be explicit. |
| `redZoneTrips` | `requires_play_by_play` | play-by-play yardline/drive data | Count offensive drives with a snap at or inside the opponent 20. | Drive and penalty/no-play treatment unresolved. |
| `redZoneTdRate` | `requires_play_by_play` | red-zone trips plus drive result/touchdown events | Red-zone touchdown drives divided by redZoneTrips. | TD attribution and drive result source must be settled. |

## Optional/deferred fantasy-point split fields

These fields do not block the real Teamstate lane because movement v1 drops them and forecast-features v1 forbids them.

| Field | Status | Note |
| --- | --- | --- |
| `fantasyPointsForQB` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsForRB` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsForWR` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsForTE` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsAllowedQB` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsAllowedRB` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsAllowedWR` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |
| `fantasyPointsAllowedTE` | `deferred_not_blocking` | Fantasy-point splits do not block the real Teamstate lane; movement v1 drops them and forecast-features v1 forbids them. |

## Blockers and unresolved decisions

- `pressureRateAllowed` likely requires an additional charting/provider source or explicit contract deferral.
- EPA and success-rate values require a selected source version and documented inclusion rules.
- Neutral-script filters, explosive-play thresholds, and seconds-per-play clock handling remain unresolved.
- Drive counting, points-per-drive, red-zone trips, and red-zone touchdown rate require drive rules and play inclusion rules.
- The full Week 1-18 regular-season window vs fantasy-aligned window decision remains unresolved.
- Retrieval metadata must include source name, source type, retrieval method, package/library version where available, retrieval date, dataset identifier or URL where available, transform code path, and validation report path candidate.

## PR C validation plan

Before PR C emits any non-promoted candidate artifact, it must validate:

- all 32 NFL teams for the selected window;
- expected weeks/window;
- duplicate team-week rows;
- valid team/opponent codes and reciprocal opponent consistency;
- bounded rates;
- finite numeric required fields;
- explicit null/deferred fields;
- source refs, retrieval metadata, validation report, and lineage manifest.

No artifact can be marked `governed_real_data` from this probe. Governance requires explicit markers and promotion review; path inference is not governance.
