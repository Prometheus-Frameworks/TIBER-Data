# Audit: `formation_summary_v0` Implementation Gate Status and 2024 Dry-Run Attempt

- **Date:** 2026-07-13
- **Tracking issue:** [TIBER-Data #214](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/214)
- **Predecessors:** #208 / PR #209 (`docs/specs/formation-summary-v0-source-boundary.md`), #210 / PR #211 (`docs/audits/formation-summary-v0-live-pbp-field-verification-2026-07-09.md`)
- **Scope:** TIBER-Data only. Documents (1) that the #210 verification gate is now satisfied, (2) the live evidence #214 recorded, and (3) the exact fail-closed outcome of this session's source-backed dry-run attempt. No promotion, no Teamstate/Fantasy/Forecast wiring, no governed artifact.

---

## 1. The #210 verification gate is now satisfied

The #209 spec and the #210/#211 audit blocked any `formation_summary_v0` implementation until a live `nflreadpy.load_pbp(seasons=[2024])` pull answered the open alignment questions. Per the operator's record in **issue #214**, that gate has now been passed: a fresh pull succeeded in a separate read-only verification environment, and #214 explicitly authorizes a bounded implementation and candidate dry run (and nothing more).

This document preserves that evidence in the durable audit trail, with each value tagged for where it was verified. **These values are observations for the 2024 run recorded in #214, not timeless schema guarantees.**

### 1.1 Live input facts recorded in #214 (verified in the operator's environment, not re-verified here)

| fact | value |
|---|---|
| Loader command | `nflreadpy.load_pbp(seasons=[2024])` |
| Package version | `nflreadpy 0.1.5` |
| Source rows / columns loaded | 47,274 rows, 372 columns (2024 regular-season slice) |
| `shotgun` | exists, `Float64`, values `0.0`/`1.0`, zero nulls |
| Pistol/formation-disambiguation field | none found (no source column contains `pistol`, `formation`, `under`, `center`, `align`, `personnel`, `motion`, or `shift`) |
| `defteam` | exists, string, zero nulls on all 44,686 possession rows, always differs from `posteam`; remains deferred (not needed by this artifact) |
| `qb_scramble` | exists, `Float64`, `0.0`/`1.0`, zero nulls; on all 1,135 flagged rows `pass=1`/`rush=0`; 1,062 are `play_type=run` with `qb_dropback=1`, 73 are `play_type=no_play` with `qb_dropback=0` |
| Denominator fields | `play_type`, `qb_kneel`, `qb_spike`, `two_point_attempt`, `sack`, `penalty`, `aborted_play`, `epa`, `success`, `qb_dropback` all present |
| Aborted plays inside `play_type in {pass, run}` | **111** regular-season rows with `aborted_play=1` — a naive pass/run denominator is unsafe and must exclude them explicitly |
| Null-safe qualifying denominator | **33,225** plays across all 32 teams; 981–1,110 per team; `shotgun` and `qb_dropback` non-null on every qualifying play |

### 1.2 Consequences locked into the implementation

- `shotgun` is binary and non-null in the 2024 source, so the three-bucket vocabulary partitions cleanly; the `unknown_or_unclassified_alignment` bucket is expected to be zero for 2024 but remains a required, explicit field (fail-closed home for future source gaps).
- No pistol-disambiguation field exists, so **`non_shotgun` remains the correct v0 label and `under_center` remains prohibited** — unchanged from #209 §3.3 and #211 §4.3, now confirmed by live evidence rather than preserved by default.
- `qb_scramble`/`qb_dropback` behavior confirms the #209 §3.1b rule: scrambles stay in the **pass** split via `qb_dropback`; the 73 `no_play` scramble rows fall outside the qualifying denominator entirely.
- The 111 aborted `play_type in {pass, run}` rows are excluded explicitly and null-safely (`aborted_play == 1`; a null flag is never itself an exclusion).

## 2. What this PR implements

- `scripts/build_formation_summary_v0_2024_candidate.py` — source-backed candidate builder (httpx retrieval against the same nflverse release asset `nflreadpy.load_pbp([2024])` resolves, sha256 over the exact bytes consumed, REG-only, `team_season` grain, three-bucket alignment, `qb_dropback` splits, TIBER distance success rule, #209 §6.1 sample thresholds, fail-closed validation before any file is written).
- `schemas/formation_summary_v0.schema.json` — candidate contract; rows are closed objects (an `under_center` field is a structural violation) and the alignment vocabulary enum is closed.
- `scripts/validate_formation_summary_v0.py` — standalone schema + business-rule validator (reconciliation identity, forbidden-label grep, rate bounds/count consistency, threshold and fail-closed note enforcement, retrieval-metadata/checksum completeness, non-governed markers).
- `tests/test_build_formation_summary_v0_2024_candidate.py`, `tests/test_validate_formation_summary_v0.py` — deterministic fixture tests (no network), covering every case #214 enumerates.

## 3. This session's dry-run attempt: failed closed, documented, not routed around

| item | value |
|---|---|
| Environment | Claude Code remote execution sandbox (ephemeral container), outbound HTTPS through a policy-enforcing egress proxy; GitHub access scoped to the five TIBER repositories |
| Command | `python scripts/build_formation_summary_v0_2024_candidate.py` |
| Result | **Failed closed before any row was built; no artifact, validation report, or manifest was emitted** |
| Error | `403 Forbidden` for `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet` |
| Block mechanism | Session-level GitHub repository scoping (proxy response: "GitHub access to this repository is not enabled for this session. Use add_repo to request access.") — a narrower, more precisely attributed block than the domain-level 403 documented in #211 §3.1 |
| Operator decision | The operator was asked in-session whether to expand session access to `nflverse/nflverse-data` and chose to open the implementation PR **without** the dry run instead |

Consistent with `TRUTH_SOURCES.md` and the #211 precedent, no season was substituted, no alternate provider was substituted, and no workaround was attempted. The 33,225/111/32-team expectations in §1.1 therefore remain **externally recorded evidence from #214**, not yet independently re-observed by this repo's own build.

## 4. Remaining step for #214 acceptance (deferred, not skipped)

The source-backed 2024 candidate dry run must be executed in an environment where the nflverse release asset is reachable (e.g., the repo's real development/CI environment, or a session with `nflverse/nflverse-data` access granted):

```
python scripts/build_formation_summary_v0_2024_candidate.py
python scripts/validate_formation_summary_v0.py \
  exports/candidates/formation_summary/formation_summary_v0_2024_real_source_candidate.json
```

The build emits the candidate artifact, validation report, and lineage manifest (retrieval method, `nflreadpy`/`polars` versions, retrieval timestamp, source URL, and sha256 checksum of the exact bytes consumed) only if every validation check passes, and refuses to write anything otherwise. Expected cross-checks against §1.1: 32 team rows; `qualifyingPlaysTotal` = 33,225; `abortedPlaysExcludedTotal` = 111; per-team `offensive_plays` within 981–1,110; `unknownAlignmentPlaysTotal` = 0 — material deviation means upstream drift (the release asset is mutable) and must be investigated, not absorbed silently.

## 5. Addendum (2026-07-14): dry run completed in a source-enabled environment and committed

The remaining step in §4 is now complete. The operator ran the builder and the standalone
validator in an independent source-enabled environment and pushed the three generated
files to the PR branch as commit
[`fa84f1a`](https://github.com/Prometheus-Frameworks/TIBER-Data/commit/fa84f1afa398618fa46e75e0739b6f93d77ed939)
("Add 2024 formation summary candidate evidence"). §3 above is preserved unchanged as the
record of this session's earlier fail-closed attempt.

| item | value |
|---|---|
| Commands | `python scripts/build_formation_summary_v0_2024_candidate.py` then `python scripts/validate_formation_summary_v0.py exports/candidates/formation_summary/formation_summary_v0_2024_real_source_candidate.json` |
| Package versions | `nflreadpy 0.1.5`, `polars 1.42.1` |
| Retrieval timestamp | `2026-07-14T01:44:19+00:00` |
| Source URL | `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet` |
| Source checksum (sha256, exact bytes consumed) | `6d432dd4308329bfddaef633309ea119f9ca46d52cbb3c09f47172a2e8efcd01` |
| Artifact generatedAt | `2026-07-14T01:44:28+00:00` |
| Build validation | all 19 checks passed (`allPassed: true`), including JSON Schema validation |
| Standalone validator | `PASS: 32 row(s) validated against schema and business rules.` |

**Independent cross-check against §1.1 (#214's recorded observations), re-run in this
session against the committed files** — every expected value matched exactly:

| expected (§1.1 / #214) | committed evidence | match |
|---|---|---|
| 32 team rows, full league, none suppressed | 32 rows; `isFullLeague: true`; `suppressedRows: []` | ✅ |
| `qualifyingPlaysTotal` = 33,225 | 33,225 (and per-row `offensive_plays` sums to the same) | ✅ |
| `abortedPlaysExcludedTotal` = 111 | 111 | ✅ |
| per-team `offensive_plays` in 981–1,110 | min 981, max 1,110 | ✅ |
| `unknownAlignmentPlaysTotal` = 0 | 0 (bucket still explicit per row) | ✅ |
| exact three-bucket reconciliation per row | holds on all 32 rows | ✅ |
| no `dropback_split_blocked` rows expected (qb_dropback non-null on every qualifying play) | `dropbackSplitBlockedRowCount: 0` | ✅ |
| no `under_center` anywhere | absent from the serialized artifact | ✅ |
| candidate-only markers | `provenanceStatus: candidate_real_data`; `governanceStatus: ungoverned` | ✅ |

No drift from the mutable release asset was observed between the #214 verification pull
and this retrieval. The artifact remains a non-promoted candidate; nothing in this
addendum authorizes promotion or downstream consumption.

## 6. Non-goals observed

- No promotion to `exports/promoted` or `governed_real_data`; no governance marker set.
- No Teamstate `formation_lens_v0` consumer, no Fantasy/Forecast/ranking/advice integration.
- No player-level formation splits; no scheme/personnel/motion/pistol labels; no league-relative high/low labels.
- No `under_center` field, label, or prose anywhere in the artifact surface (hard validation failure at schema and business-rule level).
