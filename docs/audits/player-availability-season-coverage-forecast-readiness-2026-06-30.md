# Audit: Player Availability, Season Coverage, and Active-Player Detection for Forecast Readiness

- **Date:** 2026-06-30
- **Scope:** TIBER-Data only (read-only inventory).
- **Tracking issue:** [TIBER-Data #184](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/184)
- **Type:** Audit-only. No artifact promotion, no contract changes, no Forecast/Teamstate/FORGE work, no live roster scraping, no fabricated status.

> **Reading note on `exports/promoted/`.** This audit treats `exports/promoted/...` as a *location*, not a provenance guarantee. Several promoted files carry row-level `source: "offline_fixture:..."` and synthetic `fixture_*` IDs. Where that is true, this audit calls them fixture-sourced regardless of directory.

---

## 1. Executive verdict

TIBER-Data can describe **2025 player weekly production and weekly roster membership from a real source** (nflverse via `nflreadpy`), but it **cannot currently detect *current* active players** and **has no multi-season career history**. The honest state is:

1. **One real season of player data exists: 2025.** It is source-backed (`nflverse`/`nflreadpy`) and lives in `data/processed/evidence/*.source_backed.json` and `data/gold/forge/*2025*`. It is **not promoted** into `exports/promoted/nfl/` — the promoted `*_v1.json` files there are **offline fixtures** with synthetic IDs.
2. **2024 is fixtures/scaffolds only.** No governed 2024 player-level production exists; the 2024 FORGE files are `offline_fixture` and 8-player proof scaffolds.
3. **No season before 2024 exists anywhere.** A 9-year veteran has **one** real season (2025) represented today — not nine.
4. **Active-player status is `unknown` even in the real roster source.** `roster_player_team_map_2025.source_backed.json` is source-verified for *membership* but every row has `active_roster_status: "unknown"`. The only artifact that carries an `active`/`inactive`-style status is `player_ownership_latest.json` (27 players, a smoke-test subset), and it **explicitly states its status is stale** (`source_snapshot_stale_for_current_roster`, observed at 2025 week 18 / 2026 draft, not confirmed current).
5. **Strong contracts exist without data behind them.** `roster_snapshot_v0` (schema), `RoleOpportunity` (Zod contract + validator + tests), and `player_ownership_v0` all have rich, provenance-aware shapes, but the first two have **zero real data rows** and the third has only a 27-player provisional snapshot.

**Bottom line for Forecast:** the safest next lane is **active-player detection scoped as a derived, source-bounded snapshot** built on the already-source-backed 2025 weekly roster, *not* historical coverage (which requires multi-season ingestion that does not exist yet) and *not* FORGE/Role&Opportunity as a Forecast input (no governed data). See §9–§10.

---

## 2. Artifact inventory table

Provenance legend: **source_backed** = real upstream (nflverse/nflreadpy or named source); **fixture** = `offline_fixture`/synthetic IDs; **contract_only** = schema/validator/examples, no real data; **scaffold** = small proof-reference subset.

| Artifact (path) | Kind / version | Grain | Seasons | Rows / players | Provenance | Has `generated_at`/`observed_at`/as-of? | Active-detector safe? |
|---|---|---|---|---|---|---|---|
| `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json` | evidence (ppr outcomes) | player-week | 2025 (wk 1–22) | 6,394 records | **source_backed** (`nflreadpy.load_player_stats`) | top-level `provenance`/`source_path`; **no per-row `generated_at`** | n/a (production, not status) |
| `data/processed/evidence/player_weekly_ppr_outcomes_2025.computed_source_backed.json` | evidence (ppr, with rolling/`games_played`) | player-week | 2025 (wk 1–22) | 6,394 rows / 620 players | **source_backed** | per-row `source` + `generated_at` (2026-04-27) | n/a |
| `data/processed/evidence/player_weekly_usage_2025.source_backed.json` | evidence (usage) | player-week | 2025 (wk 1–22) | 6,326 records | **source_backed** (`nflreadpy.load_player_stats`) | top-level provenance; nulls honest (`routes_run: null` etc.) | n/a |
| `data/processed/evidence/roster_player_team_map_2025.source_backed.json` | evidence (roster map) | player-week (roster membership) | 2025 (wk 1–22) | 14,348 rows / 971 players | **source_backed** (`nflreadpy.load_rosters_weekly([2025])`, `source_status: source_verified`) | top-level only; **no observed_at per row** | **Membership yes; status no** — every row `active_roster_status: "unknown"` |
| `data/processed/research/goblin_signal_candidates_2025.source_backed.json` | research signal candidates | player-week (derived) | 2025 | ~1.8 MB | source_backed (derived) | derived | n/a |
| `exports/promoted/nfl/player_weekly_ppr_outcomes_v1.json` | promoted export v1 | player-week | 2025 | small sample | **fixture** (`source: offline_fixture:.../player_weekly_box_scores_2025.offline_fixture.json`) | per-row `source` + `generated_at` | No (fixture) |
| `exports/promoted/nfl/player_weekly_usage_v1.json` | promoted export v1 | player-week | 2025 | small sample | **fixture** (`offline_fixture`) | per-row `source` + `generated_at` | No (fixture) |
| `exports/promoted/nfl/roster_player_team_map_v1.json` | promoted export v1 | player-week | 2025 (wk 1) | small sample | **fixture** (synthetic `fixture_zay_flowers` IDs; `source_status: offline_fixture`) | per-row `source`/`generated_at` | No — IDs fake, status `active`/`fixture_only` mixed |
| `exports/promoted/player_ownership/player_ownership_latest.json` | `player_ownership_v0` | player (current ownership) | snapshot (2025 wk18 + 2026 draft) | 27 players (20 `active_roster` provisional, 7 `unsigned_draft_pick`) | **source_backed but provisional/stale** (`nflreadpy_load_rosters_weekly_2025`, `nfl_draft_results_2026_*`; 1 fixture) | `generated_at`, `last_verified_at`, per-`source_ref` `observed_at`, **explicit staleness note** | **Closest fit, but stale + 27-player subset** |
| `exports/promoted/player_ownership/events/player_ownership_events_2026.jsonl` | `player_ownership_change_event_v0` | player change event | 2026 | 1 event (Tee Higgins team_change) | **fixture** (`fixture_demonstration_only`, `confidence: fixture_only`) | `detected_at`, `observed_at` | No (fixture scaffold) |
| `exports/promoted/player_ownership/player_ownership_aliases.json` | aliases | player alias | — | small | seed | — | n/a |
| `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json` | identity crosswalk v1 | player (provider→tiber id) | 2025-tagged ids | 25 records (`sleeper` only) | seeded operator-verified (`coverage: ...not_full_player_universe`) | `generated_at` | Partial join key only |
| `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json` | draft results | player (draft) | **2026 only** | 257 picks | source_backed (NBC/PFT tracker) | `source`/`source_url` | Rookie/draft-year only |
| `data/gold/forge/forge_player_weekly_ppr_2025.cohort.v1.json` | FORGE cohort v1 | player-week cohort | 2025 (18 wk) | 50 players | **source_backed** (nflverse via nflreadpy; `asOf`/`sourceUpdatedAt` 2026-04-27) | `asOf`, `sourceUpdatedAt`, `buildId` | n/a (production) |
| `data/gold/forge/forge_weekly_player_ppr_2025.v1.json` | FORGE weekly v1 | player-week | 2025 (18 wk) | 792 records / 50 players | **source_backed** | `metadata.asOf`/`sourceUpdatedAt` | n/a |
| `data/gold/forge/forge_season_player_input_2025.ppr.v1.json` | FORGE season input v1 | player-season | 2025 | 50 players | **source_backed** | `metadata.asOf`/`sourceUpdatedAt` | n/a |
| `data/gold/forge/forge_weekly_player_input_2024_w0[1-6].{skill,qb}_offline_fixture.derived.json` (glob; `skill_` for w01–w06, `qb_` for w01) | FORGE weekly | player-week | 2024 (w01–w06) | fixtures | **fixture** (`offline_fixture`) | derived | No |
| `data/gold/forge/forge_weekly_player_input_2024_w0[1-3].skill_upstream_public_w01_w03_8player_scaffold.proof_reference_snapshot.derived.json` (glob) | FORGE weekly | player-week | 2024 (w01–w03) | 8-player scaffold | **scaffold** (`upstream_public_..._8player_scaffold`) | snapshot | No |
| `data/raw/evidence/*.offline_fixture.json` (box scores, usage, roster map, team offense/pace, rookie replay) | raw fixtures | mixed | 2025 | small | **fixture** (`offline_fixture`) | — | No |
| `data/raw/forge/weekly_player_stats.offline_fixture.json` | raw forge fixture | player-week | (forge) | 25 KB | **fixture** | — | No |
| `data/raw/player_ownership/player_ownership_source_roster_smoke_test_2026_05_24.json` | raw ownership smoke test | player | 2025/2026 | 20 KB | source smoke test | observed | input to ownership_v0 |
| `data/gold/rookies/2026/*` , `data/raw/rookies/2026/*` , `data/rookies_manifest.csv` | rookies | player (rookie) | **2026 only** | small | predraft alpha + draft id ref | — | Rookie-only |
| `exports/promoted/rookie-replay/historical_rookie_replay_v0.json` | rookie replay v0 | player (replay) | 2025 replay | 3 records | **fixture** (`fixture_*` IDs) | provenance block | No |
| `data/projection-input-fixtures/weekly_projection_input_fixture_2026_w01.json` | projection input fixture v1 | player-week bundle | 2026_w01 label | fixture | **fixture** (`bounded_rehearsal_fixture`, `production_coverage_claim: false`) | declared scope | No |
| `schemas/roster_snapshot_v0.schema.json` + `docs/contracts/roster-snapshot-v0.md` | **contract only** | (team-roster-snapshot) | — | **0 data rows** | **contract_only** | schema mandates `generated_at`,`source_updated_at`,`observed_at`,`confidence` | Schema is detector-shaped; no data |
| `src/contracts/v1/roleOpportunity.ts` + `src/validate/validateRoleOpportunity.ts` + `test/roleOpportunity.v1.test.ts` + examples | **contract only** | (player-week role/usage) | example: 2024 window | **0 real data rows** | **contract_only** (examples are `tiber-role-opportunity-contract` fixtures) | example has `generatedAt`/`inputWindow` | n/a |
| `schemas/player_ownership_v0.schema.json` / `player_ownership_change_event_v0` / `player_ownership_aliases_v0` | contracts | player / event | — | schemas | contract (data: 27-player snapshot above) | schema mandates provenance | partial (see ownership_latest) |

---

## 3. Season coverage table

| Season | Player production (ppr/usage) | Roster membership | Active status | Career/age | Provenance summary |
|---|---|---|---|---|---|
| **≤ 2023** | none | none | none | none | **No data of any kind.** |
| **2024** | fixtures only (FORGE `offline_fixture` w01–w06; 8-player upstream scaffold w01–w03) | none real | none | none | Fixtures/scaffolds only; not governed. |
| **2025** | **source_backed** (6,394 ppr / 6,326 usage rows, wk 1–22; 620–971 players) | **source_backed membership** (14,348 rows, 971 players, wk 1–22) | **`unknown`** in source; 27-player provisional snapshot in ownership_v0 | none (no age/birth/career fields populated) | Real nflverse via nflreadpy, **not promoted**. |
| **2026** | none | none (ownership snapshot references 2025 wk18) | provisional snapshot + 1 fixture event | draft year only (257 picks); rookie predraft | Draft results source_backed; ownership provisional; rookies predraft. |

Raw season-token scan across `data/` + `exports/`: `2024` ≈ 716 mentions (fixtures/scaffolds), `2025` ≈ 36,037 (real source-backed evidence), `2026` ≈ 10 (draft/rookies/ownership). **Zero pre-2024 tokens.**

---

## 4. Player availability / active-status verdict

**Verdict: Current active-player detection is NOT currently possible from a governed, source-backed artifact.**

- The only **real roster source** (`roster_player_team_map_2025.source_backed.json`, `nflreadpy.load_rosters_weekly`) proves **weekly membership** (player was on a 2025 weekly roster) but encodes **`active_roster_status: "unknown"` on all 14,348 rows**. It does not distinguish active / inactive / IR / practice squad.
- The only artifact carrying an `active_roster`-style status is **`player_ownership_latest.json`** (`player_ownership_v0`), and it is honest about its limits:
  - 27 players only (operator smoke-test subset, not the player universe);
  - statuses are `provisional` (20 `active_roster`) or tied to the 2026 draft (7 `unsigned_draft_pick`);
  - each `source_ref` carries the note *"source_snapshot_stale_for_current_roster: team membership verified at observation date only; current roster status as of 2026-05-24 not confirmed"* — observed at 2025 **week 18** and 2026 draft, **not current**.
- The change-event lane (`player_ownership_events_2026.jsonl`) is a **single fixture event** (`fixture_demonstration_only`, `confidence: fixture_only`) — a scaffold, not a transaction feed.

So TIBER-Data has the **contract shape** for active status (the `player_ownership_v0` `ownership_status` enum: `active_roster`, `practice_squad`, `unsigned_draft_pick`, `free_agent`, `retired`, `injured_reserve`, `suspended`, `unknown`, etc.) and a **fail-closed `unknown` posture**, but not a populated, current, full-universe source. Per repo rules, missing status must remain `unknown`; it must **not** be inferred from missing rows.

---

## 5. Historical career coverage verdict

**Verdict: A 9-year veteran has at most ONE real season (2025) represented today — not nine.**

TIBER-Data has **no** career-season rows, **no** player-season summaries spanning multiple historical seasons, **no** games-active/played/missed by season, **no** team-history-by-season, and **no** season-availability status across years. The only multi-week depth is **within 2025** (weeks 1–22). 2024 is fixtures/scaffolds; pre-2024 is absent entirely.

**Gap + likely source path (for a future, separately-approved issue — not built here):** multi-season career coverage would require ingesting `nflreadpy.load_player_stats` / `load_rosters` / `load_rosters_weekly` and `load_players` across a season range (e.g., 2016–2025) into a new `player_season_*` / `player_career_*` evidence + contract surface, mirroring the existing 2025 `*.source_backed.json` build scripts (`scripts/build_*_source_backed_2025.py`). This is a data-promotion effort, explicitly out of scope for this audit.

---

## 6. Age / career-year support verdict

**Verdict: TIBER-Data cannot currently emit player age, career year, age bucket, or rookie/sophomore/veteran bucket from real data.**

- `docs/schemas/players.md` declares an `age` column as `derived_now_if_available` — "deterministically derived from `birth_date` when the roster source exposes it; **null otherwise**" — plus `college`, `draft_team`, `draft_round` as passthrough/future-optional. **No `players` data table exists**, and a scan of `data/` + `exports/` finds **zero populated `age` or `birth_date` fields**.
- Draft-year/round exists only for **2026** (`nfl_draft_results_2026.json`, 257 picks) and the 2026 rookie reference — enough to know a 2026 rookie's draft slot, not enough to compute career year for veterans.
- Per the cross-repo ownership matrix, **Age-Curve is a separate producer repo**; TIBER-Data owns only the contract surface and does **not** own an age-context dataset.

**Missing contract/source boundary:** to emit age/career-year, TIBER-Data needs (a) a `players_v0`/`player_identity` artifact populated from `nflreadpy.load_players()` carrying `birth_date`, `draft_year`, `rookie_year`, and (b) a per-season age/career-year derivation. Neither exists today.

---

## 7. Role & Opportunity readiness verdict

**Verdict: `contract_only`. Role & Opportunity is NOT Forecast-ready — there is no real, source-backed, season-safe Role&Opportunity dataset in TIBER-Data.**

- **Contract:** `src/contracts/v1/roleOpportunity.ts` (Zod) — rich `identity` + `scope` + `role` + `usage` + `opportunity` + `confidence` + `source` shape.
- **Validator/tests:** `src/validate/validateRoleOpportunity.ts`, `test/roleOpportunity.v1.test.ts`, examples in `src/contracts/v1/examples.ts`.
- **Producer ownership (governance):** `Role-and-Opportunity-Model` is a **separate producer repo**; TIBER-Data owns the contract surface, the producing repo emits the data.
- **Data:** **none.** No file under `data/` or `exports/` contains `primaryRole`/`roleTags`; the only instances are the contract, validator, tests, and 2024-window **examples** (`model: tiber-role-opportunity-contract`).
- **Partial support:** the 2025 `player_weekly_usage_2025.source_backed.json` could feed *some* `usage` fields (targets, target_share, rush attempts, snap_share, red-zone touches), but key contract fields (`routeParticipation`, `airYardShare`, several opportunity shares) are **null or absent** in the source usage rows, and there is no producer step that emits the contract. So usage can *partially* back the contract; it does not satisfy it.

---

## 8. Depth-chart / injury / availability gap table

| Concept | Existing contract? | Docs-only gap? | Candidate/scenario enum? | Real source-backed artifact? | Missing source requirement |
|---|---|---|---|---|---|
| Depth chart (starter/backup) | No typed contract | Flagged in cross-repo-governance §4 ("roster/depth-chart context", "QB stability") | `roster_snapshot_v0.roster_role` field (schema only) | **No** | Depth-chart source (e.g., `nflreadpy.load_depth_charts`) + contract |
| Injury / deactivation | No | Referenced via `ownership_status: injured_reserve` enum | enum value only | **No** (no injury rows) | Injury report source + per-week status |
| Active / inactive status | `player_ownership_v0` (status field); `roster_snapshot_v0.status` | — | `ownership_status` enum incl. `active_roster`, `practice_squad`, `unknown` | **Partial** — 27-player provisional snapshot only; source roster map = `unknown` | Full-universe, current weekly roster/gameday-inactives source |
| Practice participation | No | — | No | **No** | Practice report source |
| Role change / team change | `player_ownership_change_event_v0` | — | `event_type` enum (`team_change`, `signing`, `release`, `trade`, `injured_reserve_change`, ...) | **No** (1 `fixture_only` event) | Transaction feed |
| One-injury-away / depth context | No | World-modeling gap (governance §4) | No | **No** | Depth chart + injury joined |

**Summary:** depth-chart, injury, practice, and transaction lanes are **contract/enum-shaped at best and fixture-only or absent in data.** The status vocabulary exists; the populated, current source does not.

---

## 9. Forecast readiness ranking

Conservative status per candidate lane (definitions per issue #184):

| Rank | Candidate lane | Status | Why |
|---|---|---|---|
| 1 | **Active-player detection** | `source_backed_candidate` (status field) / `needs_data_promotion_before_forecast` for full universe | Real 2025 weekly roster membership is source-backed (971 players); `player_ownership_v0` gives a fail-closed status contract. Membership is solid; **status** needs a derived classification + current source. Smallest honest step. |
| 2 | **Player weekly PPR outcomes** | `source_backed_but_not_governed` | 6,394 real 2025 rows exist (`data/processed/evidence/...source_backed.json`); the **promoted** `v1` file is fixture. Real data is one promotion away, but single-season. |
| 3 | **Player weekly usage** | `source_backed_but_not_governed` | 6,326 real 2025 rows; nulls honest; promoted `v1` is fixture. Single season. |
| 4 | **Historical player-season coverage** | `needs_data_promotion_before_forecast` | Only 2025 exists. Requires multi-season ingestion that does not exist; high value, larger effort. |
| 5 | **Role & Opportunity** | `contract_only` | Rich contract + validator, **zero real data**; owned by a separate producer repo. Usage can only partially back it. |
| 6 | **Age / career-year context** | `greenfield_contract_needed` (no populated `players` table; Age-Curve is external) | No age/birth/career data; needs a `players_v0` ingest + derivation. |
| 7 | **Depth chart** | `greenfield_contract_needed` | Only a `roster_role` schema field; no source, no contract doc. |
| 8 | **Injury / availability** | `contract_only` (enums) → `greenfield_contract_needed` for data | Status enums exist; no injury/practice source. |
| 9 | **FORGE as Forecast input** | `promoted_but_fixture_sourced` for 2024 / `source_backed_candidate` for 2025 cohort (50 players, ungoverned) | 2025 FORGE gold is real but a 50-player cohort in `data/gold/`, not governed/promoted; 2024 FORGE is fixture. Not gate-ready. |
| 10 | **FORGE as observer-only** | `source_backed_candidate` (observer) | The 2025 FORGE cohort is fine to *observe/calibrate against* without binding into Forecast. Lowest risk if FORGE is touched at all. |

**Recommended Forecast lane: active-player detection**, scoped as a *derived, source-bounded snapshot over the existing 2025 weekly roster*, with fail-closed `unknown`. It is the only lane with (a) a real source already in-repo, (b) a fail-closed status contract already written, and (c) no dependency on a separate producer repo or on multi-season ingestion. Historical coverage is the higher-value but larger second step.

---

## 10. Recommended next issue

**Title (suggested):** `spec: active_player_detection_v0 contract and source boundary (no implementation)`

**Shape (spec/contract only — do not build the detector or scrape live rosters):**

Define `active_player_detection_v0` as a **derived classification artifact** (not source truth) over the already-source-backed 2025 weekly roster, with explicit provenance and fail-closed behavior. Required fields:

- `as_of` (explicit ISO-8601 UTC as-of timestamp);
- `source_name` + `source_path` (e.g., `nflreadpy.load_rosters_weekly`, `data/processed/evidence/roster_player_team_map_2025.source_backed.json`);
- `source_updated_at` / `observed_at`;
- `player_id`, `player_name`, `team`, `position`;
- `roster_status` and a detection enum `active_status ∈ {active, inactive, ir, practice_squad, released, traded, unknown}` — **see the enum-boundary note below; this is a gameday-availability axis and is NOT the governed `ownership_status` enum**;
- `status_basis ∈ {source_truth, derived_classification}` (so consumers know status is *derived*, not asserted by the source);
- `confidence` / provenance posture;
- `season` / `week` / `date` scope;
- **fail-closed rule:** when status is missing → `unknown`, never inferred from absent rows; when the snapshot is stale → carry the staleness note (as `player_ownership_latest.json` already does).

**Enum boundary vs. the governed `player_ownership_v0.ownership_status`.** The detection enum above must **not** be assumed to round-trip with the governed `ownership_status` enum (`active_roster`, `practice_squad`, `unsigned_draft_pick`, `college`, `devy`, `free_agent`, `retired`, `injured_reserve`, `suspended`, `unknown`). A future `active_player_detection_v0` must either (a) reuse `ownership_status` for the roster-membership axis, or (b) keep this distinct detection enum **and** document the mapping below as an explicit new enum boundary:

| detection `active_status` | governed `ownership_status` | boundary note |
|---|---|---|
| `active` | `active_roster` | direct |
| `inactive` | *(none)* | no governed value for gameday-inactive — needs a roster-status sub-field or an `ownership_v0` extension |
| `ir` | `injured_reserve` | direct |
| `practice_squad` | `practice_squad` | direct |
| `released` | `free_agent` | approximate; release is a transaction, free-agent is the resulting ownership state |
| `traded` | *(none)* | not an `ownership_status`; modeled by `player_ownership_change_event_v0.event_type` = `team_change`/`trade` |
| `unknown` | `unknown` | direct |

So the next issue must pick (a) or (b) explicitly; it cannot silently emit `active`/`ir`/`released`/`traded` as if they were governed `ownership_status` values.

**Can existing artifacts satisfy this today?** Partially: `roster_player_team_map_2025.source_backed.json` supplies identity + team + membership for 971 players (status `unknown`), and `player_ownership_v0` supplies the ownership enum + a 27-player provisional snapshot. **What is missing:** a current, full-universe roster/inactives source; a derivation step that maps membership → active/inactive with `status_basis = derived_classification`; and the explicit enum reconciliation above. Until that exists, the artifact must remain a 2025-scoped, fail-closed snapshot, not a claim of *current* active state.

---

## Appendix A — Provenance honesty notes

- `exports/promoted/nfl/{player_weekly_ppr_outcomes_v1,player_weekly_usage_v1,roster_player_team_map_v1}.json` are **fixture-sourced** (`source: offline_fixture:...`, synthetic `fixture_*` IDs). Directory `promoted/` does **not** make them governed real data.
- `data/processed/evidence/*.source_backed.json` are the **real** 2025 artifacts and are **not** promoted.
- `player_ownership_latest.json` is the most provenance-complete availability artifact (per-`source_ref` `observed_at`, `confidence`, explicit staleness), but is a 27-player provisional smoke-test subset, not current truth.
- FORGE 2025 gold (`data/gold/forge/*2025*`) is source-backed (50-player cohort) but ungoverned; FORGE 2024 is fixture/scaffold.
- No `age`/`birth_date` is populated anywhere; `players.md` is a schema doc, not a data table.

## Appendix B — Files inspected (non-exhaustive)

`TRUTH_SOURCES.md`, `AGENTS.md`, `ARCHITECTURE.md`, `docs/governance/cross-repo-governance-v0.md`, `docs/schemas/players.md`, `schemas/roster_snapshot_v0.schema.json`, `schemas/player_ownership_v0.schema.json`, `schemas/player_ownership_change_event_v0.schema.json`, `src/contracts/v1/roleOpportunity.ts`, `src/validate/validateRoleOpportunity.ts`, `data/processed/evidence/*.source_backed.json`, `exports/promoted/nfl/*.json`, `exports/promoted/player_ownership/*`, `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json`, `exports/promoted/nfl_draft_results/nfl_draft_results_2026.json`, `data/gold/forge/*`, `data/raw/evidence/*`, `data/projection-input-fixtures/*`.
