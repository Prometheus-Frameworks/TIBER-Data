# Spec: `player_season_coverage_v0` — Contract and Source Boundary

- **Status:** Pre-contract specification. **Spec-only. Not implementation-ready. Not a promoted contract. Not a dataset. No multi-season coverage is claimed to exist.**
- **Date:** 2026-06-30
- **Tracking issue:** [TIBER-Data #188](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/188)
- **Predecessors:**
  - [#184](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/184) / [PR #185](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/185) — player availability & season-coverage audit (`docs/audits/player-availability-season-coverage-forecast-readiness-2026-06-30.md`).
  - [#186](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/186) / [PR #187](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/187) — `active_player_detection_v0` source boundary (`docs/specs/active-player-detection-v0-source-boundary.md`).

> **Why this document exists.** Forecast will eventually need historical player records, not isolated 2024/2025 fixtures. But TIBER-Data does **not** have multi-season coverage today: the audit established one real player-data season (2025, nflverse via `nflreadpy`, not promoted), 2024 as fixtures/scaffolds, no pre-2024 player data, and no populated age/career surface. This document defines what a legitimate `player_season_coverage_v0` artifact *would mean* — its grain, fields, source boundary, recommended first window, and fail-closed rules — **before** any historical data is ingested, any `nflreadpy` call is made, any artifact is generated or promoted, or any player-history feature is bound into Forecast. A spec is not a dataset. It lives under `docs/specs/` (not `docs/contracts/`) on purpose.

---

## 1. Purpose and non-goals

### Purpose

Define the minimal source-bounded player-season artifact TIBER-Data needs before Forecast can safely reason about historical player records — so that, **if and only if** a bounded ingestion window is later approved, an implementer can build it without re-deriving the boundary or overclaiming coverage.

### Non-goals (hard blocks)

This document does **not**, and any PR carrying it must **not**:

- ingest historical data or call `nflreadpy` / add any source pull;
- create a generated artifact or promote any dataset;
- modify Forecast or Teamstate; start FORGE work; implement Role & Opportunity; implement active-player detection;
- create a Forecast gate or bind anything into Forecast;
- claim multi-season coverage exists, or imply 2024 player-level data is real while it is still fixture/scaffold;
- make fantasy advice, rankings, start/sit, trade, draft, or product claims.

Where a source is missing, this document flags the gap rather than inventing it (per `TRUTH_SOURCES.md` / `AGENTS.md` fail-closed posture).

---

## 2. Core question and what a valid spec must answer

**What is the minimal source-bounded player-season artifact TIBER-Data needs before Forecast can safely reason about historical player records?**

This spec answers: what a player-season row is (§3), which fields belong and their truth status (§4), which sources are allowed (§5), the recommended first bounded window (§6), how multi-team seasons and missing weeks/games/usage/availability are represented (§4.3, §4.4, §7), and what would make the artifact safe for a later Forecast coverage/provenance gate (§7, §8).

---

## 3. Row grain

**Grain: one row per `player_id` + `season`.** A `(player_id, season)` pair is unique; duplicate pairs are invalid (see §7).

This grain is a **season-level coverage and summary** record. It is explicitly **not**:

| this artifact is NOT | that is owned by |
|---|---|
| a player-**week** row | `player_weekly_ppr_outcomes_v1` / `player_weekly_usage_v1` (player-week) |
| a roster-membership row | `roster_player_team_map_*` (player-week membership) |
| an availability / active-status row | `active_player_detection_v0` (spec, #187) |
| a player-ownership row | `player_ownership_v0` |
| a Forecast feature row | Forecast (consumer; not produced here) |
| fantasy advice / ranking output | out of scope for TIBER-Data entirely |

A multi-team season is still **one** row keyed by `(player_id, season)`; the multiple teams are represented inside the row (§4.3), never by emitting multiple rows for the same pair.

---

## 4. Required field families

Each field carries a **truth status**: `source_truth` (passthrough from a named source), `derived_summary` (deterministically computed from source-backed inputs), `unavailable` (cannot be emitted yet; null, not zero), or `out_of_scope` (belongs to another lane). Below, **R** = required, **O** = optional-if-source-backed, **U** = explicitly unavailable today.

### 4.1 Identity

| field | req | truth status | notes |
|---|---|---|---|
| `player_id` | R | source_truth | canonical nflverse/TIBER id; **do not invent** |
| `player_name` | R | source_truth | source passthrough |
| `position` | R | source_truth | season-primary position; if it changes, see `position_notes` |
| `provider_ids` | O | source_truth | e.g., gsis/pfr/sleeper ids when source-backed; else omit |
| `identity_confidence` | R | derived_summary | provenance posture (`source_verified` / `provisional` / `low`) — not a downstream score |

### 4.2 Season scope

| field | req | truth status | notes |
|---|---|---|---|
| `season` | R | source_truth | NFL season (integer) |
| `season_type` | O | source_truth | `REG` / `POST` / `REG+POST`; the window covered by this row's summaries |
| `generated_at` | R | — | artifact generation time |
| `source_updated_at` \| `observed_at` | R | — | source's own update time / when TIBER observed it; null only when genuinely unavailable |
| `source_refs` | R (min 1) | — | each: `source_name`, `source_url?`, `observed_at`, `source_updated_at?`, `confidence`, `notes?` |

### 4.3 Team / roster context (multi-team handling)

| field | req | truth status | notes |
|---|---|---|---|
| `teams` | R | source_truth | array of all teams the player appeared on this season, in chronological order |
| `primary_team` | R | derived_summary | by an **explicit rule** (e.g., most weeks observed; ties broken deterministically); the rule must be recorded in `coverage_notes` |
| `team_weeks` | O | derived_summary | per-team week counts `[{team, weeks_observed}]` when weekly source supports it |
| `team_unknown` | R | derived_summary | boolean; true when team for one or more observed weeks could not be resolved (then the affected weeks are excluded from `team_weeks`, not guessed) |

**Multi-team seasons must not be collapsed** to a single team without the explicit `primary_team` rule, and the full `teams` array must be preserved.

### 4.4 Coverage / observation status

| field | req | truth status | notes |
|---|---|---|---|
| `weeks_observed` | R | derived_summary | distinct weeks with a source-backed row for this player |
| `games_observed` | R | derived_summary | weeks where the player has a source-backed stat line |
| `games_played` | O | source_truth/derived | only if the source distinguishes played vs rostered; else `unavailable` |
| `games_missed` | U→O | source_truth | **only if source-backed**; absence of a week is **not** a missed game (§7) |
| `coverage_status` | R | derived_summary | enum `full_season \| partial_season \| single_week \| none \| unknown` relative to the season's scheduled weeks |
| `coverage_notes` | R | — | states the `primary_team` rule, any excluded weeks, and the source window |
| `missing_fields` | R | — | explicit array of field families that are `unavailable` for this row |

### 4.5 Production summaries

Emitted **only** when computed from source-backed weekly box scores; field-level derivation noted.

| field | req | truth status | notes |
|---|---|---|---|
| `season_ppr` | O | derived_summary | sum of source-backed weekly PPR (same formula as `player_weekly_ppr_outcomes_v1`) |
| `games_for_ppg` | O | derived_summary | denominator used; PPG omitted unless denominator is explicit |
| `passing_summary` / `rushing_summary` / `receiving_summary` | O | derived_summary | yards/TDs/attempts/etc. summed from source-backed weeks |
| field-level `*_source` notes | R when present | — | which source artifact each summary derives from |

`null` ≠ `0`: a player with no receiving role has `receiving_summary = null` (unavailable for that family) **only** if the source does not report it; a genuine zero from a source-backed week is `0`. See §7.

### 4.6 Usage summaries

| field | req | truth status | notes |
|---|---|---|---|
| `targets`, `receptions`, `rushing_attempts` | O | derived_summary | summed from source-backed weekly usage |
| `air_yards`, `target_share` | O | derived_summary/`unavailable` | only when the weekly source populates them (2025 source rows leave several usage fields `null`) |
| `snap_share`, `routes_run`, `route_participation`, `red_zone_*` | O | `unavailable` unless source-backed | many are null in current 2025 source rows → remain `unavailable`, never `0` |

### 4.7 Age / career context

> **Current gap (audit finding):** TIBER-Data has **no populated `age`/`birth_date`** anywhere, and draft data exists only for 2026. `docs/schemas/players.md` declares `age` as derived-if-available from `birth_date`, with `draft_*` as future-optional.

| field | req | truth status | notes |
|---|---|---|---|
| `birth_date` | U→O | source_truth | only if `nflreadpy.load_players()` exposes it; else `unavailable` |
| `season_age` | U→O | derived_summary | deterministically derived from `birth_date` + season reference date; **null if birth_date unavailable** |
| `draft_year`, `rookie_year` | U→O | source_truth | source passthrough when available |
| `career_year` / `tenure` | U→O | derived_summary | `season − rookie_year + 1`; **null if rookie_year unavailable** |
| `age_bucket` / `career_stage` | U→O | derived_summary | only if `season_age`/`career_year` are themselves source-derivable; **never fabricated** |

Age/career-year fields **cannot be fabricated** from missing birth/draft data. If the chosen source does not expose them, they remain `unavailable` and `missing_fields` records the gap. Age-**curve** interpretation is **out of scope** (owned by the external Age-Curve repo; see §9).

### 4.8 Availability / status boundary

`player_season_coverage_v0` is a **coverage/history** artifact, **not** an availability artifact.

- It **may** carry source-backed roster *presence* counts (`weeks_observed`) but **must not** carry active/inactive/IR/practice-squad gameday status — that axis belongs to `active_player_detection_v0` (spec, #187) and `player_ownership_v0`.
- If availability is unknown (it always is here, by design), the artifact does not assert it: there is **no** active-status field, and consumers must not infer one.
- Fail-closed: roster/coverage presence is **not** availability and **not** a claim the player was active.

---

## 5. Source boundary

A future implementation may consider **only** the inputs below, and may not ingest any of them under this issue.

### 5.1 Candidate source families (evaluate, do not call here)

| source | role | provides | cannot provide |
|---|---|---|---|
| `nflreadpy.load_player_stats(seasons)` | production + usage | weekly box-score → season production/usage summaries | gameday active/inactive; age/draft |
| `nflreadpy.load_rosters_weekly(seasons)` | team/roster context | per-week team membership, position | active/inactive (carries `unknown`); age |
| `nflreadpy.load_rosters(seasons)` | season roster | season team(s), position | gameday availability |
| `nflreadpy.load_players()` | age/career context | `birth_date`, `draft_year`, `rookie_year` **if exposed** | guarantees of completeness; availability |

### 5.2 Existing in-repo references

- **Source-backed 2025 (real):** `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json` (6,394 rows / 620 players, wk 1–22), `player_weekly_usage_2025.source_backed.json` (6,326 rows), `roster_player_team_map_2025.source_backed.json` (14,348 rows / 971 players, status `unknown`). These prove the **weekly→season summarization is feasible for 2025** and define the field shapes to roll up. They are **one season** and **not promoted**.
- **Non-governing references only:** all `*.offline_fixture.*` and `*_scaffold*` surfaces, and the 50-player `data/gold/forge/forge_season_player_input_2025.ppr.v1.json` (a player-season-*shaped* but ungoverned cohort). These illustrate shape; **fixtures/scaffolds cannot authorize historical coverage**.

### 5.3 Hard rule

Fixtures and scaffolds are shape references, never truth. No row of `player_season_coverage_v0` may derive from a fixture/scaffold source and be presented as historical coverage.

---

## 6. Recommended first implementation window

**Recommended first bounded slice: `2022–2025` (4 seasons, REG by default; POST optional and flagged via `season_type`).** Do **not** build it here.

### Justification

- **Unlocks the existing Forecast experiment.** Forecast's current shape is 2024 → 2025, but 2024 player-level data is fixture/scaffold today. Making **2024 real** is the immediate prerequisite for using 2025 as a legitimate target. A window that includes 2024 and 2025 is therefore the minimum useful slice.
- **Enough depth for basic career signal without overclaiming.** Four seasons let a future build compute bounded `career_year`/tenure-relative trends and multi-season production context, while staying honestly short of full career history (a 9-year veteran still would not have 9 seasons — and the artifact must say so).
- **Source stability.** Recent nflverse seasons have the most consistent weekly usage fields (the advanced usage fields that are already partially null in 2025 are even sparser further back), so a recent bounded window maximizes honest field population.
- **Bounded before full ingestion.** Prefer this slice over `2020–2025` or full-range as a first build; broader history is a **later, separate** expansion once the bounded slice passes review.

### Fallbacks / sequencing

- **Reduced fallback:** `2023–2025` (3 seasons) if scope must shrink — still includes 2024+2025.
- **Minimum to unblock Forecast target:** at least `2024–2025` real player-level coverage; the spec states explicitly that **2024 must become real source-backed player-level data** before Forecast treats 2025 as a target season.
- **Later expansion:** full historical (toward each player's `rookie_year`) is a separate future window, not part of the first slice, and must not be implied as already available.

---

## 7. Fail-closed rules

1. A **missing player-season row** is not proof the player was inactive or out of the league.
2. **Missing weeks** are not proof of games missed unless the source explicitly supports that interpretation; `games_missed` stays `unavailable` otherwise.
3. **Zero production ≠ missing production.** A source-backed zero is `0`; an unreported family is `null`/`unavailable`.
4. **Unavailable usage fields remain `null`/`unavailable`, never `0`** (e.g., `snap_share`, `routes_run` where the source does not populate them).
5. **Fixture/scaffold rows cannot be promoted** as historical truth.
6. **Age/career-year fields cannot be fabricated** from missing birth/draft data; they stay `unavailable` with the gap recorded in `missing_fields`.
7. **Multi-team seasons must not be collapsed** without the explicit `primary_team` rule; the full `teams` array is preserved.
8. **One row per `(player_id, season)`**; duplicate pairs are invalid.
9. **No availability/active-status assertion** (see §4.8).
10. Forecast must not consume this until a real artifact passes a **separate coverage/provenance gate** (§8).

---

## 8. Forecast consumer guidance

- **A spec is not a dataset.** Nothing here is loadable.
- **A player-season row is not automatically a Forecast feature.** Selection/feature-engineering is a separate, gated step.
- **Forecast must not consume `player_season_coverage_v0` until a real artifact exists and passes a separate coverage/provenance gate.**
- **Null/unknown must not be coerced to zero.**
- **Historical coverage does not imply availability, role, depth-chart status, or current active status.**
- **Any future Forecast experiment must preserve target-season cutoff rules** (e.g., a 2024→2025 experiment must not leak 2025 summaries into 2024 inputs).

---

## 9. Relationship to existing lanes

| lane | relationship |
|---|---|
| `active_player_detection_v0` (spec #187) | **Disjoint axis.** That artifact answers *availability/active status as-of a moment*; this one answers *what seasons/production a player has on record*. Coverage presence here is not availability there. |
| `player_ownership_v0` | Ownership/roster-membership category + provenance/staleness shape. This spec reuses its **provenance shape** (`source_refs`, confidence, staleness discipline) but not its status enum. |
| `player_weekly_ppr_outcomes_v1` | **Upstream input.** Season production summaries (§4.5) are deterministic roll-ups of these source-backed weekly outcomes. |
| `player_weekly_usage_v1` | **Upstream input.** Season usage summaries (§4.6) roll up these weekly usage rows; unpopulated weekly fields stay `unavailable` at season level. |
| `RoleOpportunity` | **Downstream/disjoint.** Role interpretation is not produced here. This artifact is raw season coverage, not role/opportunity scoring; Role & Opportunity remains a separate producer repo. |
| Age-Curve / age-context | This artifact may carry source-backed `season_age`/`career_year` **inputs** (when available); age-**curve** interpretation is owned by the external Age-Curve repo. This spec only defines the context fields, not the curve. |
| FORGE | **Observer/shape reference only.** The 50-player `forge_season_player_input_2025` is a player-season-shaped precedent, not a governing source. No FORGE work here. |
| Forecast Run 1 / future player-history runs | This is the **history foundation** a future run would consume *after* a separate gate — not a Run input today. |

Posture: this artifact is **source coverage / history foundation**, not role interpretation, ranking, advice, or model output.

---

## 10. Recommended next issue (separate, not started here)

Only if a bounded ingestion window is later approved:

**`feat: build player_season_coverage_v0 for 2022–2025 (bounded, source-bounded, gated)`**, with required gates:

1. an explicit, approved season window (default `2022–2025`) and an approved source list (§5);
2. a schema + validator proving: required identity/season/source fields enforced; missing `source_refs` fails; unknown/unavailable states explicit; `zero` and `null` distinct; multi-team examples validate only under the explicit `primary_team` rule; invalid grain / duplicate `(player_id, season)` fails;
3. honest coverage reporting (`coverage_status`, `missing_fields`) and **no** age/career fabrication when source lacks birth/draft;
4. **no** Forecast binding until a later, separate coverage/provenance gate passes.

Implementation must remain blocked until those gates are explicitly approved. This document does not authorize it.

---

## Appendix — Referenced facts and vocabulary

- Real source-backed 2025 (audit): `player_weekly_ppr_outcomes_2025.source_backed.json` (6,394 rows / 620 players, wk 1–22), `player_weekly_usage_2025.source_backed.json` (6,326 rows), `roster_player_team_map_2025.source_backed.json` (14,348 rows / 971 players, `active_roster_status: unknown`). Provider: `nflreadpy.load_player_stats` / `load_rosters_weekly`.
- No populated `age`/`birth_date` anywhere; draft data is 2026-only (`nfl_draft_results_2026.json`, 257 picks).
- `truth_status` vocabulary (this spec): `source_truth | derived_summary | unavailable | out_of_scope`.
- `coverage_status` (this spec): `full_season | partial_season | single_week | none | unknown`.
