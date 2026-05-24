# Player Ownership Roster Smoke-Test Report

**Date:** 2026-05-24  
**Issue:** #135 — Player Ownership Pipeline Population  
**Branch:** `claude/player-ownership-pipeline-xmpMs`

---

## Summary

| Metric | Count |
|---|---|
| Total players tested | 26 |
| Matched to source-backed evidence | 26 |
| Unmatched | 0 |
| Ambiguous | 0 |
| Source-verified (current-reliable) | 7 |
| Provisional (stale roster snapshot) | 19 |
| Name normalizations applied | 4 |

**26/26 matched to source-backed ownership evidence. Current roster freshness varies by source and observed_at timestamp.** nflreadpy rows reflect 2025-season roster snapshots (observed Jan/Feb 2026) and are marked `provisional` — team membership at observation time is source-verified, but current roster truth as of 2026-05-24 is not confirmed. The 7 2026 draft-pick rows are marked `source_verified` based on the NBC Sports PFT 2026 draft tracker.

---

## Confidence Framing

| Source | Ownership Confidence | Rationale |
|---|---|---|
| nflreadpy weekly rosters 2025 | `provisional` | Source row is verified (nflreadpy provenance), but the 2025-season snapshot is stale for current (2026-05-24) roster truth. Upgrade to `source_verified` once a live 2026 roster source is available. |
| NFL Draft Results 2026 (NBC Sports PFT) | `source_verified` | Draft selection is a permanent historical fact; team assignment as of 2026-04-25 is directly source-backed. Status reflects `unsigned_draft_pick` at observation date. |

---

## Sources Used

| Source | Path | Source Confidence |
|---|---|---|
| nflreadpy weekly rosters 2025 | `data/processed/evidence/roster_player_team_map_2025.source_backed.json` | `source_verified` (provenance) |
| NFL Draft Results 2026 (NBC Sports PFT) | `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json` | `source_verified` |

---

## Name Normalizations Applied

Four input names required normalization to match their canonical source record. All normalizations are Jr. suffix or documented nickname aliases — no inference from the roster list.

| Input Name | Canonical Source Name | Reason |
|---|---|---|
| `Michael Penix` | `Michael Penix Jr.` | Jr. suffix — matches nflreadpy player record |
| `Chris Rodriguez` | `Chris Rodriguez Jr.` | Jr. suffix — matches nflreadpy player record |
| `Mike Washington` | `Mike Washington Jr.` | Jr. suffix — matches 2026 NFL Draft record |
| `Tet McMillan` | `Tetairoa McMillan` | Known nickname alias — matches nflreadpy player record |

---

## Bootstrap Write Path

The promoted latest artifact was written via `--bootstrap-promote-new-players`, an explicit one-time bootstrap flag. This path bypasses the ingestion pipeline's `new_player_requires_operator_review` gate, which is appropriate only for initial population of a scaffold-only latest artifact.

**For ongoing updates, use `ingest_player_ownership.py --write`** — the standard ingestion pipeline with source-conflict detection, identity resolution, and change-event gating.

---

## Pipeline Run Results

Source input: `data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json`  
Previous latest: `exports/promoted/player_ownership/player_ownership_latest.json`

**Pre-population dry-run** (before bootstrap):
- 26 new players detected (all absent from scaffold-only latest)
- Promotion blocked: `new_player_requires_operator_review` (expected — initial bootstrap)

**Bootstrap write** (`--bootstrap-promote-new-players`):
- Schema validation: 26/26 rows pass `player_ownership_v0`
- Merged with existing latest (preserving Tee Higgins scaffold row)
- Wrote 27-player promoted latest artifact

**Post-population dry-run** (after bootstrap):
- 26 unchanged, 0 changes detected, 0 validation errors
- Tee Higgins: reported as `missing_source_row_is_uncertainty_not_release` (retained, not released)

---

## Per-Player Table

### nflreadpy 2025 Roster — 19 players (`provisional`, observation from 2025 season)

> Staleness note: these rows carry `confidence: provisional` because the nflreadpy snapshot reflects 2025-season team membership (observed Jan/Feb 2026). Team assignments are not re-verified as of 2026-05-24.  
> Week-to-date approximation: Week 18 ≈ 2026-01-05, Week 19 ≈ 2026-01-12, Week 20 ≈ 2026-01-19, Week 22 ≈ 2026-02-09

| Input Name | Player ID | Canonical Name | Pos | Level | Team (at obs.) | Status | Confidence | Observed At | Warnings |
|---|---|---|---|---|---|---|---|---|---|
| Jalen Hurts | `00-0036389` | Jalen Hurts | QB | NFL | PHI | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Geno Smith | `00-0030565` | Geno Smith | QB | NFL | LV | active_roster | provisional | 2026-01-05 | Snapshot stale |
| Michael Penix | `00-0039917` | Michael Penix Jr. | QB | NFL | ATL | active_roster | provisional | 2026-01-05 | Name normalized; snapshot stale |
| Omarion Hampton | `00-0040666` | Omarion Hampton | RB | NFL | LAC | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Chris Rodriguez | `00-0038611` | Chris Rodriguez Jr. | RB | NFL | WAS | active_roster | provisional | 2026-01-05 | Name normalized; snapshot stale |
| Joe Mixon | `00-0033897` | Joe Mixon | RB | NFL | HOU | active_roster | provisional | 2026-01-19 | Snapshot stale |
| Tank Bigsby | `00-0038555` | Tank Bigsby | RB | NFL | PHI | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Christian Watson | `00-0038124` | Christian Watson | WR | NFL | GB | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Ladd McConkey | `00-0039915` | Ladd McConkey | WR | NFL | LAC | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Tet McMillan | `00-0040124` | Tetairoa McMillan | WR | NFL | CAR | active_roster | provisional | 2026-01-12 | Name normalized; snapshot stale |
| Khalil Shakir | `00-0037261` | Khalil Shakir | WR | NFL | BUF | active_roster | provisional | 2026-01-19 | Snapshot stale |
| Tory Horton | `00-0040648` | Tory Horton | WR | NFL | SEA | active_roster | provisional | 2026-02-09 | Snapshot stale |
| Keon Coleman | `00-0039901` | Keon Coleman | WR | NFL | BUF | active_roster | provisional | 2026-01-19 | Snapshot stale |
| Jaylin Noel | `00-0040138` | Jaylin Noel | WR | NFL | HOU | active_roster | provisional | 2026-01-19 | Snapshot stale |
| Kyle Williams | `00-0040131` | Kyle Williams | WR | NFL | NE | active_roster | provisional | 2026-02-09 | Snapshot stale |
| Romeo Doubs | `00-0037816` | Romeo Doubs | WR | NFL | GB | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Colston Loveland | `00-0040126` | Colston Loveland | TE | NFL | CHI | active_roster | provisional | 2026-01-19 | Snapshot stale |
| Dallas Goedert | `00-0034351` | Dallas Goedert | TE | NFL | PHI | active_roster | provisional | 2026-01-12 | Snapshot stale |
| Juwan Johnson | `00-0036040` | Juwan Johnson | TE | NFL | NO | active_roster | provisional | 2026-01-05 | Snapshot stale |

### 2026 NFL Draft Results — 7 players (`source_verified`, `unsigned_draft_pick`)

> Source: NBC Sports ProFootballTalk 2026 NFL Draft picks full tracker, observed 2026-04-25.  
> `unsigned_draft_pick` reflects status at observation date; signing status post-draft not confirmed.

| Input Name | Player ID | Canonical Name | Pos | Level | Team | Status | Confidence | Observed At | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Garrett Nussmeier | `qb-garrett-nussmeier` | Garrett Nussmeier | QB | NFL | KC | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 7, pick 249 |
| Jonah Coleman | `rb-jonah-coleman` | Jonah Coleman | RB | NFL | DEN | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 4, pick 108 |
| Eli Heidenreich | `rb-eli-heidenreich` | Eli Heidenreich | RB | NFL | PIT | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 7, pick 230 |
| Mike Washington | `rb-mike-washington-jr` | Mike Washington Jr. | RB | NFL | LV | unsigned_draft_pick | source_verified | 2026-04-25 | Name normalized; Rd 4, pick 122 |
| Seth McGowan | `rb-seth-mcgowan` | Seth McGowan | RB | NFL | IND | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 7, pick 237 |
| Jordyn Tyson | `wr-jordyn-tyson` | Jordyn Tyson | WR | NFL | NO | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 1, pick 8 |
| Antonio Williams | `wr-antonio-williams` | Antonio Williams | WR | NFL | WAS | unsigned_draft_pick | source_verified | 2026-04-25 | Rd 3, pick 71 |

---

## Promoted Artifact State

After bootstrap, `exports/promoted/player_ownership/player_ownership_latest.json` contains **27 players**:

| Confidence | Count | Players |
|---|---|---|
| `source_verified` | 7 | 2026 draft picks |
| `provisional` | 20 | 19 nflreadpy 2025 roster snapshots + Tee Higgins scaffold |

All rows validate against `player_ownership_v0.schema.json`. No `player_id: null` rows in the promoted artifact.

---

## Unresolved / Unknown Players

None. All 26 smoke-test players were matched to source-backed records with resolved player IDs.

---

## Promotion Rules Compliance

| Rule | Status |
|---|---|
| No source-verified rows without a source | ✓ All rows carry `source_refs` with `source_name`, `observed_at`, `confidence` |
| No blanket "current roster verified" from stale snapshots | ✓ nflreadpy rows use `provisional`; staleness note in every source_ref |
| No inferred NFL team ownership from fantasy roster list | ✓ Teams sourced from nflreadpy / draft results only |
| No invented teams, player IDs, or ownership status values | ✓ All IDs from nflreadpy GSIS or draft result slugs |
| Schema validation required before artifact write | ✓ All 26 rows validated before bootstrap write |
| Bootstrap path explicitly guarded | ✓ `--bootstrap-promote-new-players` flag with printed warning; not `--write` |
| Absence is uncertainty, not release | ✓ Tee Higgins reported as `missing_source_row_is_uncertainty_not_release` |

---

## Artifacts Produced

| Artifact | Path |
|---|---|
| Source builder script | `scripts/build_player_ownership_source_roster_smoke_test_2026_05_24.py` |
| Source input JSON | `data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json` |
| Promoted latest artifact | `exports/promoted/player_ownership/player_ownership_latest.json` |
| Source builder tests | `tests/test_player_ownership_source_builder.py` |
| This report | `docs/reports/player-ownership-roster-smoke-test-2026-05-24.md` |

---

## Test Results

```
tests/test_ingest_player_ownership.py         14 passed
tests/test_player_ownership_contracts.py       6 passed
tests/test_player_ownership_source_builder.py 26 passed
Total: 46 passed
```
