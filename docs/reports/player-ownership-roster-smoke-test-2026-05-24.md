# Player Ownership Roster Smoke-Test Report

**Date:** 2026-05-24  
**Issue:** #135 — Player Ownership Pipeline Population  
**Branch:** `claude/player-ownership-pipeline-xmpMs`

---

## Summary

| Metric | Count |
|---|---|
| Total players tested | 26 |
| Recognized (matched) | 26 |
| Unmatched | 0 |
| Ambiguous | 0 |
| Source-verified | 26 |
| Provisional / unverified | 0 |
| Name normalizations applied | 4 |

All 26 smoke-test roster players were matched and recognized by TIBER-Data player ownership sources. No players remain unresolved.

---

## Sources Used

| Source | Path | Confidence |
|---|---|---|
| nflreadpy weekly rosters 2025 | `data/processed/evidence/roster_player_team_map_2025.source_backed.json` | `source_verified` |
| NFL Draft Results 2026 (NBC Sports PFT) | `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json` | `source_verified` |

---

## Name Normalizations Applied

Four input names required normalization to match their canonical source record. No manual inference was applied; all normalizations are Jr. suffix or documented nickname aliases.

| Input Name | Canonical Source Name | Reason |
|---|---|---|
| `Michael Penix` | `Michael Penix Jr.` | Jr. suffix — matches nflreadpy player record |
| `Chris Rodriguez` | `Chris Rodriguez Jr.` | Jr. suffix — matches nflreadpy player record |
| `Mike Washington` | `Mike Washington Jr.` | Jr. suffix — matches 2026 NFL Draft record |
| `Tet McMillan` | `Tetairoa McMillan` | Known nickname alias — matches nflreadpy player record |

---

## Pipeline Run Results

Source input: `data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json`  
Previous latest: `exports/promoted/player_ownership/player_ownership_latest.json`

**Pre-population dry-run** (run before builder `--write`):
- 26 new players detected (all smoke-test players were absent from the scaffold-only latest)
- Promotion blocked: `new_player_requires_operator_review` (expected — initial bootstrap)

**Builder write** (`build_player_ownership_source_roster_smoke_test_2026_05_24.py --write`):
- Operator-supervised bootstrap: validated all 26 rows against `player_ownership_v0`, merged with existing latest (preserving Tee Higgins scaffold row)
- Wrote 27-player promoted latest artifact

**Post-population dry-run** (run after builder `--write`):
- 26 unchanged, 0 changes detected, 0 validation errors
- Tee Higgins scaffold row: reported as `missing_source_row_is_uncertainty_not_release` (not removed — absence is uncertainty, not release)

---

## Per-Player Table

### nflreadpy 2025 Roster — 19 players (`active_roster`, `source_verified`)

> Observation dates are derived from nflreadpy weekly roster week-end snapshots:  
> Week 18 ≈ 2026-01-05, Week 19 ≈ 2026-01-12, Week 20 ≈ 2026-01-19, Week 22 ≈ 2026-02-09

| Input Name | Player ID | Canonical Name | Pos | Level | Team | Status | Confidence | Source | Observed At | Warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| Jalen Hurts | `00-0036389` | Jalen Hurts | QB | NFL | PHI | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Geno Smith | `00-0030565` | Geno Smith | QB | NFL | LV | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-05 | — |
| Michael Penix | `00-0039917` | Michael Penix Jr. | QB | NFL | ATL | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-05 | Name normalized (Jr. suffix) |
| Omarion Hampton | `00-0040666` | Omarion Hampton | RB | NFL | LAC | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Chris Rodriguez | `00-0038611` | Chris Rodriguez Jr. | RB | NFL | WAS | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-05 | Name normalized (Jr. suffix) |
| Joe Mixon | `00-0033897` | Joe Mixon | RB | NFL | HOU | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-19 | — |
| Tank Bigsby | `00-0038555` | Tank Bigsby | RB | NFL | PHI | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Christian Watson | `00-0038124` | Christian Watson | WR | NFL | GB | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Ladd McConkey | `00-0039915` | Ladd McConkey | WR | NFL | LAC | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Tet McMillan | `00-0040124` | Tetairoa McMillan | WR | NFL | CAR | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | Name normalized (nickname alias) |
| Khalil Shakir | `00-0037261` | Khalil Shakir | WR | NFL | BUF | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-19 | — |
| Tory Horton | `00-0040648` | Tory Horton | WR | NFL | SEA | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-02-09 | — |
| Keon Coleman | `00-0039901` | Keon Coleman | WR | NFL | BUF | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-19 | — |
| Jaylin Noel | `00-0040138` | Jaylin Noel | WR | NFL | HOU | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-19 | — |
| Kyle Williams | `00-0040131` | Kyle Williams | WR | NFL | NE | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-02-09 | — |
| Romeo Doubs | `00-0037816` | Romeo Doubs | WR | NFL | GB | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Colston Loveland | `00-0040126` | Colston Loveland | TE | NFL | CHI | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-19 | — |
| Dallas Goedert | `00-0034351` | Dallas Goedert | TE | NFL | PHI | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-12 | — |
| Juwan Johnson | `00-0036040` | Juwan Johnson | TE | NFL | NO | active_roster | source_verified | nflreadpy_load_rosters_weekly_2025 | 2026-01-05 | — |

### 2026 NFL Draft Results — 7 players (`unsigned_draft_pick`, `source_verified`)

> Source: NBC Sports ProFootballTalk 2026 NFL Draft picks full tracker, published 2026-04-25  
> Status `unsigned_draft_pick` reflects source snapshot date; signing status not confirmed post-draft.

| Input Name | Player ID | Canonical Name | Pos | Level | Team | Status | Confidence | Source | Observed At | Warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| Garrett Nussmeier | `qb-garrett-nussmeier` | Garrett Nussmeier | QB | NFL | KC | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 7, pick 249 |
| Jonah Coleman | `rb-jonah-coleman` | Jonah Coleman | RB | NFL | DEN | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 4, pick 108 |
| Eli Heidenreich | `rb-eli-heidenreich` | Eli Heidenreich | RB | NFL | PIT | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 7, pick 230 |
| Mike Washington | `rb-mike-washington-jr` | Mike Washington Jr. | RB | NFL | LV | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Name normalized (Jr. suffix); Rd 4, pick 122 |
| Seth McGowan | `rb-seth-mcgowan` | Seth McGowan | RB | NFL | IND | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 7, pick 237 |
| Jordyn Tyson | `wr-jordyn-tyson` | Jordyn Tyson | WR | NFL | NO | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 1, pick 8 |
| Antonio Williams | `wr-antonio-williams` | Antonio Williams | WR | NFL | WAS | unsigned_draft_pick | source_verified | nfl_draft_results_2026_nbcsports_profootballtalk | 2026-04-25 | Rd 3, pick 71 |

---

## Promoted Artifact State

After operator-supervised bootstrap, `exports/promoted/player_ownership/player_ownership_latest.json` contains **27 players**:

- 26 smoke-test roster players: `confidence: source_verified`
- 1 pre-existing scaffold row (Tee Higgins): `confidence: provisional`, `source: fixture_demonstration_only`

The promoted artifact validates against `player_ownership_v0.schema.json`. All 26 source-backed rows carry `source_refs` with `source_name`, `observed_at`, and `confidence`.

---

## Unresolved / Unknown Players

None. All 26 smoke-test players were matched to source-backed records. No players have `player_id: null` in the promoted artifact.

---

## Promotion Rules Compliance

| Rule | Status |
|---|---|
| No source-verified rows without a source | ✓ All rows carry `source_refs` |
| No inferred NFL team ownership from fantasy roster list | ✓ Teams sourced from nflreadpy / draft results only |
| No hidden missing coverage | ✓ Tee Higgins scaffold gap explicitly noted |
| No invented teams, player IDs, or ownership status values | ✓ All IDs from nflreadpy GSIS or draft result slugs |
| Schema validation required before artifact write | ✓ All 26 rows validated before writing |
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
tests/test_ingest_player_ownership.py      14 passed
tests/test_player_ownership_contracts.py    6 passed
tests/test_player_ownership_source_builder.py  24 passed
Total: 44 passed
```
