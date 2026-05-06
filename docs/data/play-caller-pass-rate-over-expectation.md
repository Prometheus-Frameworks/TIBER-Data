# Play-caller pass rate over expectation scaffold

## Purpose

This lane is a bounded research scaffold for a future historical play-caller pass rate over expectation artifact. The target metric family is inspired by public work titled "Play Caller Historical Pass Rates Over Expectation" covering 2006-2025 with nflfastR data, but this repository must not copy that table into source artifacts.

The immediate purpose of this first PR is only to establish:

- the repository boundary for this metric family;
- a deterministic bucket taxonomy helper for future aggregation work;
- an explicit list of source-field questions that must be answered before artifact generation;
- a no-op build script that exits cleanly while refusing to generate unsupported data.

This scaffold does not produce a 2006-2025 artifact and does not claim source-backed play-caller attribution.

## Why this belongs in TIBER-Data

TIBER-Data is the canonical source of truth for deterministic football data contracts, fixtures, and governed handoff artifacts. A source-backed play-caller pass rate over expectation dataset would eventually be a governed upstream evidence artifact, not a downstream scoring tweak.

This lane belongs here only at the scaffold/research boundary because it needs:

- deterministic data provenance;
- documented source fields;
- repeatable bucket classification;
- explicit handoff constraints for downstream consumers;
- fail-closed refusal to fabricate missing play-caller mappings.

Until source truth is settled, this lane is documentation plus helper logic only.

## Relationship to TIBER-Teamstate

The eventual output is expected to be a future input to TIBER-Teamstate, where historical play-caller tendencies may become team-context evidence. Teamstate should consume only a source-backed, documented artifact once this repository can prove how each row was derived.

TIBER-Teamstate must not infer play-caller pass rate over expectation from this scaffold alone. This repository has not yet established the authoritative play-caller mapping layer or the final aggregation contract.

## Relationship to GOBLIN

GOBLIN is future context only for this lane. This scaffold does not add GOBLIN candidates, change GOBLIN source-readiness gates, create recommendation logic, or introduce any scoring behavior.

If a future source-backed artifact is promoted, GOBLIN may later evaluate whether that evidence is useful. That evaluation belongs in a separate downstream or explicitly governed follow-up, not in this scaffold PR.

## Source-field investigation notes

nflfastR/nflverse play-by-play exposes or can derive expected pass fields through `add_xpass()`. The expected fields of interest are:

- `xpass`: probability of dropback, scaled 0-1;
- `pass_oe`: dropback percentage over expected on a play, scaled 0-100.

The nflfastR documentation notes that `add_xpass()` adds `xpass` and `pass_oe`, and that those values return `NA` before 2006 because scrambles were not marked before then. The complete `build_nflfastR_pbp()` workflow includes `add_xpass()` in the play-by-play build.

Candidate raw fields for future investigation include:

- `season`
- `posteam`
- `down`
- `ydstogo`
- `yardline_100`
- `play_type` or a quarterback dropback/pass indicator
- `epa`
- `xpass`
- `pass_oe`

Open source-field questions that must be settled before artifact generation:

1. Which nflfastR/nflverse release and extraction path is authoritative for this repository?
2. Whether `pass_oe` should be consumed directly or recomputed from `xpass` plus observed dropback/pass indicators for auditability.
3. Which play inclusion rules should apply for spikes, kneels, penalties, scrambles, sacks, aborted plays, and no-plays.
4. Whether team attribution should use `posteam`, possession context, or another canonical team field.
5. How to document any nflfastR schema or model-version assumptions at artifact build time.

## Bucket scaffold

The first deterministic helper for this lane classifies rows into exact Issue #84 bucket strings. Every valid row belongs to `overall`. Outside-red-zone situational buckets apply only when `yardline_100 > 20`. Red-zone buckets apply when `yardline_100 <= 20`, with `red_zone_inside_5` also applying when `yardline_100 <= 5`.

The current bucket labels are:

- `overall`
- `outside_rz_1st_10`
- `outside_rz_2nd_8_plus`
- `outside_rz_2nd_3_to_7`
- `outside_rz_2nd_1_to_2`
- `outside_rz_3rd_5_plus`
- `outside_rz_3rd_3_to_4`
- `outside_rz_3rd_1_to_2`
- `red_zone_inside_20`
- `red_zone_inside_5`

This helper is not an artifact generator. It only gives future source-backed aggregation code a tested taxonomy.

## Screenshot/reference-table warning

Screenshot or public reference-table values must not be copied into committed artifacts, fixtures, or tests. They may be used only as human context for understanding the desired metric family.

This repository must derive any future artifact directly from governed source data and documented transformation logic. Manual transcription would create false provenance and is explicitly out of scope.

## Play-caller mapping is a separate provenance problem

The hard unresolved problem is play-caller attribution. nflfastR play-by-play can support expected-pass calculations, but play-caller identity over historical seasons requires a separate, source-backed mapping layer.

This scaffold does not create or consume play-caller mappings. A future mapping proposal must document, at minimum:

- source documents for coordinator/play-caller assignments;
- season and team validity windows;
- interim play-caller changes;
- shared duties or ambiguous attribution rules;
- confidence/provenance fields;
- validation rules that prevent silent continuity across unsupported weeks or seasons.

Do not fabricate play-caller mappings to complete this lane.

## Manual mapping scaffold proposal

No manual mapping file is added in this PR. If a future PR introduces a manual or semi-manual mapping scaffold, it should live under an explicitly labeled path such as `data/manual/test/manual_needs_verification/` until source provenance is settled.

Any such fixture must be clearly labeled as test-only and must not be consumed as source-backed truth.

## Current status

This lane is research/scaffold only until source/provenance is settled. The scaffold script exists only to state that boundary and exits without fetching data or generating artifacts.

Run the scaffold message with:

```bash
node scripts/build_play_caller_pass_rate_over_expectation.mjs
```
