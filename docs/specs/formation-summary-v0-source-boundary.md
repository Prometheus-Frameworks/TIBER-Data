# Spec: `formation_summary_v0` — Contract and Source Boundary

- **Status:** Pre-contract specification. **Spec-only. Not implementation-ready. Not a promoted contract. Not a dataset. No governed artifact is created, and no Teamstate/Fantasy/Forecast wiring is authorized by this document.**
- **Date:** 2026-07-08
- **Tracking issue:** [TIBER-Data #208](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/208)
- **Upstream context:** TIBER-Teamstate issue #75 / PR #76 — `formation_lens_v0`, a documentation-only, human-readable Teamstate explanation surface for shotgun vs. under-center tendencies. That spec intentionally blocks real-data interpretation until TIBER-Data defines and owns this artifact.
- **Precedent pattern followed:** `docs/specs/player-season-coverage-v0-source-boundary.md` (#188), `docs/specs/active-player-detection-v0-source-boundary.md` (#186) — same "spec before ingestion" posture.

> **Why this document exists.** Teamstate's Formation Lens cannot honestly describe shotgun vs. under-center tendencies until TIBER-Data decides which play-by-play fields are safe to summarize, what the offensive-play denominator is, and whether "under center" can be derived at all without silently absorbing pistol or unclassified snaps. This document answers those questions **before** any artifact is built, any row is emitted, or any consumer is wired.

---

## 0. What this audit could and could not verify in this session

This audit needed a live column/dtype/null-rate inspection of `nflreadpy.load_pbp()` output. That fetch was attempted and blocked:

```
nflreadpy.load_pbp(seasons=[2024])
-> 403 Client Error: Forbidden
   https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet
```

This is a sandbox egress-policy denial for this session (per this environment's proxy status: `recentRelayFailures` policy block on the release-asset host), **not** evidence that the source is unreachable in general — `src/team_state/loader.py` already depends on this exact call (`nflreadpy.load_pbp(seasons=[season])`) succeeding in the repo's real execution environment today, and `scripts/build_team_week_raw_v0_2024_candidate.py` has **already succeeded at reaching the same release asset URL** in a prior session, producing the real, validated, 544-row 2024 candidate cited throughout §2–§3 (`exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`). Per this environment's own operating guidance, a 403 from an organization egress policy is reported, not retried or routed around.

**Correction (post-merge, flagged by review on the follow-up verification PR #211):** that prior sentence, and the parallel claim in §"Appendix" below, originally said the 2024 candidate build proves `nflreadpy.load_pbp()` itself succeeded. It does not. `scripts/build_team_week_raw_v0_2024_candidate.py::retrieve_pbp` fetches the release asset via a **direct `httpx.Client().get(url)` call**, not via `nflreadpy.load_pbp()`'s own `requests`-based downloader — the `nflreadpy_loader=f"nflreadpy.load_pbp([{SEASON}])"` string passed into `_retrieve_nflverse_parquet` is only a descriptive label in retrieval metadata, not evidence the function was invoked. The candidate is genuine proof the release asset URL was reachable via `httpx` in that prior environment; it is not proof `nflreadpy.load_pbp()` has ever successfully executed in this repo. See `docs/audits/formation-summary-v0-live-pbp-field-verification-2026-07-09.md` §3.1 for the full correction.

Because of that, the field classification in §2 combines three sources of evidence, not two:

1. **Real-data evidence from a prior successful run** (the strongest tier): the `team_week_raw_v0` 2024 candidate build and its validation report, which prove `play_type`, `qb_kneel`, `qb_spike`, `two_point_attempt`, `qb_dropback`, `sack`, `epa`, and related fields exist and behave as expected against real ingested nflverse pbp — because that build actually ran and passed.
2. **In-repo evidence read directly in this session**: `src/team_state/loader.py`, `src/team_state/definitions.py` (`REQUIRED_PBP_COLUMNS`), `src/team_state/compute.py`, `team-state/fixtures/pbp_fixture.json`, and `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` (locked play-inclusion policy).
3. **The published nflverse/nflfastR play-by-play data dictionary** — external, well-established public documentation for this exact source family, cited only where neither (1) nor (2) settles a field, as a **documented-schema reference**, not a live pull verified in this session.

**Fail-closed consequence:** every field claim below is tagged either `verified_in_repo` (I read it in a committed file) or `documented_schema_unverified_live` (known from the public nflverse pbp schema, but not re-confirmed against a live pull in this session). Any future implementation/dry-run issue **must** re-verify the `documented_schema_unverified_live` fields against an actual `nflreadpy.load_pbp()` pull before relying on them — this spec does not substitute for that verification, per `TRUTH_SOURCES.md` ("verify the raw support exists").

---

## 1. Purpose and non-goals

### Purpose

Define the source/spec boundary for a future `formation_summary_v0` artifact: which play-by-play fields are safe to expose or derive, what the offensive-play denominator is, whether `under_center` can be safely derived, the candidate envelope/row contract, and required validation — so that, **if and only if** a bounded follow-up is later approved, an implementer can build it without re-deriving the boundary.

### Non-goals (hard blocks)

This document does **not**, and any PR carrying it must **not**:

- promote a governed artifact or emit any row of real data;
- wire TIBER-Teamstate, Fantasy, or Forecast consumption;
- train models, compute fantasy rankings, or create advice language;
- infer route concepts, motion/shift/personnel truth, or offensive scheme labels (Shanahan/McVay/RPO/spread) without a separate governed taxonomy;
- call `nflreadpy` to ingest or emit data (the one blocked diagnostic call in §0 was a column/reachability check, not an ingestion, and produced no rows and no artifact).

---

## 2. Field audit

**Truth-status vocabulary** (reused from `player_season_coverage_v0` spec, #188, for cross-spec consistency): `source_truth` (passthrough from the named source), `derived_summary` (deterministically computed from source-backed inputs), `unavailable` (cannot be emitted yet; null, not zero), `unsafe_for_v0` (technically derivable but classification risk is too high to expose without a stated caveat or a blocking bucket).

**Verification-status vocabulary** (new, specific to this audit): `verified_in_repo` (read directly from a committed file in this session), `documented_schema_unverified_live` (known from the public nflverse/nflfastR pbp data dictionary; not re-confirmed against a live pull this session).

| field | native / derived | truth status | verification | notes |
|---|---|---|---|---|
| `season` | native | source_truth | verified_in_repo | Present in `team-state/fixtures/pbp_fixture.json`; used in `src/team_state/loader.py` filter. |
| `week` | native | source_truth | verified_in_repo | Same. |
| `game_id` | native | source_truth | verified_in_repo | Used as the drive/game unique key in `src/team_state/compute.py`. |
| `posteam` (offensive team) | native | source_truth | verified_in_repo | `REQUIRED_PBP_COLUMNS` in `src/team_state/definitions.py`; non-null `posteam` is already the offensive-play gate in `compute.py::_base_offense_plays`. |
| `defteam` (defensive team) | native | source_truth | documented_schema_unverified_live | Not referenced anywhere in this repo today (team_state groups by `posteam` only). Standard nflverse pbp field; needs live confirmation before any defense-side rollup is built. |
| `play_type` | native | source_truth | verified_in_repo | Used in `compute.py` (`play_type.is_in(["pass", "run"])`) and present in the fixture (`"pass"`, `"run"`). |
| `pass` (dropback/attempt indicator) | native | source_truth | verified_in_repo | In fixture and `REQUIRED_PBP_COLUMNS`-adjacent usage (`compute.py` uses `pl.col("pass") == 1`). |
| `rush` (rush indicator) | native | source_truth | verified_in_repo | Same pattern as `pass`. |
| `shotgun` | native | source_truth | documented_schema_unverified_live | **Not present anywhere in this repo** — absent from `team-state/fixtures/pbp_fixture.json`, absent from `REQUIRED_PBP_COLUMNS`, absent from every script in `src/` and `scripts/`. This is the single field this whole spec turns on, and it has **zero in-repo precedent**. See §3 for why this blocks an unconditional `under_center` claim. |
| no-play indicator (`play_type` categorical, not a `pass`/`rush` flag) | native | source_truth | **verified_in_repo** | **Correction from an earlier draft of this audit** (flagged by review): `scripts/build_team_week_raw_v0_2024_candidate.py::is_offensive_play`/`is_competitive_play` already gate on categorical `play_type` membership (`OFFENSIVE_PLAY_TYPES = {"pass","run","qb_kneel","qb_spike"}` / `PASS_RUN_PLAY_TYPES = {"pass","run"}`), not on the `pass`/`rush` binary flags — and this exact filter has been run successfully against real 2024 nflverse play-by-play (544-row candidate, `allPassed: true`; see `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`, `docs/data/team-week-raw-v0-governance-blockers-audit.md`). The no-play/penalty-only policy itself is locked in `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Plays nullified entirely ... are excluded from `offensivePlays`"). `formation_summary_v0` should **reuse this categorical `play_type`-based gate**, not the older `compute.py::_base_offense_plays` pattern (`pass==1 \| rush==1 \| play_type in [...]`), which this audit's earlier draft incorrectly treated as the only in-repo precedent. |
| kneel indicator (`qb_kneel`) | native, exposed as a `play_type` value | source_truth | **verified_in_repo** | Confirmed via the real 2024 candidate build (`OFFENSIVE_PLAY_TYPES` includes `"qb_kneel"`; `is_competitive_play` excludes it) and `tests/test_build_team_week_raw_v0_2024_candidate.py::test_is_offensive_play_includes_kneel_and_spike` / `test_is_competitive_play_excludes_kneel_and_spike`. Policy locked in the PR C preflight doc §2 ("Kneels"): counted toward raw offensive-play totals, excluded from every rate/efficiency field. `formation_summary_v0` should follow the same exclusion for shotgun/non-shotgun tendency rates — kneels are not formation-tendency plays regardless of whether they count toward a raw denominator. |
| spike indicator (`qb_spike`) | native, exposed as a `play_type` value | source_truth | **verified_in_repo** | Same evidence and policy as kneels (PR C preflight §2, "Spikes"; same test coverage). |
| penalty-only row handling | native (`penalty` indicator plus play-type/result fields) | source_truth | **verified_in_repo (policy)** | Policy already locked and reasoned through in `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Penalties"): a penalty on an otherwise-recorded play does not remove that play; a penalty that nullifies the entire play is excluded, same as a no-play. `formation_summary_v0` should adopt this distinction verbatim rather than re-deriving it. |
| two-point attempt handling (`two_point_attempt`) | native | source_truth | **verified_in_repo** | Confirmed via the real 2024 candidate build (`is_offensive_play`/`is_competitive_play` both check `not row.get("two_point_attempt")`) and `tests/test_build_team_week_raw_v0_2024_candidate.py::test_is_offensive_play_excludes_two_point_attempt` / `test_is_competitive_play_excludes_two_point_attempt`. This repo already excludes two-point attempts from its offensive-play denominator entirely (not just "primary denominator with separate tracking" as this audit's earlier draft proposed) — `formation_summary_v0` should match that existing exclusion for consistency unless a documented reason requires a separate `two_point_plays` count. |
| special-teams exclusion | derived | derived_summary | verified_in_repo | Handled correctly by both the `team_state` filter pattern and the `team_week_raw_v0` categorical `play_type` pattern; special-teams `play_type` values (`punt`, `field_goal`, `kickoff`, `extra_point`) are outside both patterns' offensive-play sets. Also explicitly locked in the PR C preflight §2 ("Special-teams exclusions"). |
| sack handling (`sack`) | native | source_truth | **verified_in_repo** | Confirmed via the real 2024 candidate build (`stats.sacks_allowed` increments on `row.get("sack")`; sacks are counted as pass plays via `qb_dropback`). Policy locked in PR C preflight §2 ("Sacks"): counts as a pass/dropback play, separately tallied in `sacksAllowed`, never counted as explosive. `formation_summary_v0` formation attribution for a sacked dropback should follow the same `shotgun` value as any other dropback — no separate exclusion needed. |
| scramble handling (`qb_scramble`) | native | source_truth | documented_schema_unverified_live (field name itself unconfirmed) | The real 2024 candidate build's policy discussion (PR C preflight §2, "Scrambles") confirms scrambles are a real, distinctly-relevant category sourced from `qb_dropback`-style indicators, though the exact column name/mapping is left **GATED** there pending live retrieval (the preflight doc explicitly defers the literal source column names as "unknown until retrieval"). **Correction from an earlier draft of this audit** (flagged by review): "scrambles fall correctly under the rush bucket via `play_type`" is true **only** for denominator *inclusion* (a scramble has `play_type == "run"`, so it correctly counts toward `offensive_plays`/§3.1a) — it is **not** true for the pass/run *split* used by `shotgun_pass_rate`/`shotgun_run_rate`/`non_shotgun_pass_rate`/`non_shotgun_run_rate`. `team_week_raw_v0`'s own precedent (`aggregate_game`, `stats.pass_plays`/`stats.rush_plays`) classifies pass-vs-run using `qb_dropback`, **not** `play_type` — under that precedent a scramble is a *pass*/dropback play despite having `play_type == "run"`. See §3.1b: `formation_summary_v0` must follow the same rule for its pass/run split fields, or this spec would silently fork from the exact precedent it tells implementers to reuse. |
| designed QB run handling | derived, requires rusher-role join | unsafe_for_v0 | documented_schema_unverified_live | No dedicated field distinguishes a designed QB run from an RB carry or a scramble without joining rusher identity/position — out of scope per this issue's own non-goals ("infer offensive scheme labels ... without a separate governed taxonomy"). **Not attempted.** |
| aborted/botched play handling (`aborted_play`) | native or category-coded | source_truth | **verified_in_repo (policy)** | Policy already locked in `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Aborted plays"): excluded from `offensivePlays` and all rate/efficiency fields, same as no-plays, with the excluded-play count recorded in build metadata (`excludedPossessionPlays` in the real 2024 candidate's diagnostics). The exact column/detection mechanism used by the real build is not itself named in the script (it falls out of plays whose `play_type` is not in `OFFENSIVE_PLAY_TYPES`), so the **specific field name** `aborted_play` remains `documented_schema_unverified_live` even though the **policy** is proven. `formation_summary_v0` should adopt the same policy and confirm the field-level mechanism during the verification step in §9. |
| `down` | native | source_truth | verified_in_repo | In fixture and used throughout `compute.py`. |
| `distance` (`ydstogo`) | native | source_truth | verified_in_repo | Same. |
| yardline / red-zone context (`yardline_100`) | native | source_truth | verified_in_repo | Used for `is_red_zone_play` in `compute.py`. |
| score / game-script context (`score_differential`, `game_seconds_remaining`) | native | source_truth | verified_in_repo | Used for neutral-situation and garbage-time logic in `compute.py`/`definitions.py`. |
| `epa` | native (provider-modeled) | source_truth, but flag as **provider_model_derived** | documented_schema_unverified_live | Not currently consumed anywhere in this repo. This is nflverse's own modeled advanced stat (not raw NFL data) — safe to pass through as an optional field, but the artifact must disclose it is a third-party model output, not a raw measurement, consistent with the issue's "insufficient_data until source-backed" posture for optional efficiency fields. |
| success indicator | **conflict**, see §3.2 | derived_summary | verified_in_repo (existing TIBER definition) / documented_schema_unverified_live (nflverse's own field) | TIBER-Data **already has** a governed success-rate definition in `src/team_state/definitions.py`/`compute.py` (≥40% of yards-to-go on 1st down, ≥60% on 2nd, 100% on 3rd/4th) — independent of whatever `success` column nflverse's pbp may also carry. See §3.2: do not silently pick one without naming the fork. |

### 2.1 Summary: field readiness for a future implementation

| status | fields |
|---|---|
| Ready today (verified in repo, already used by an existing TIBER artifact) | `season`, `week`, `game_id`, `posteam`, `play_type` (including categorical `no_play`/`qb_kneel`/`qb_spike` values), `pass`, `rush`, `down`, `ydstogo`, `yardline_100`, `score_differential`, `game_seconds_remaining`, `penalty` (policy), `two_point_attempt`, `sack`, `aborted_play` (policy; field name itself still needs confirmation), `epa` (used and computed on in the real 2024 candidate build) |
| Plausible but **must be live-verified before use** (no in-repo precedent at all) | `shotgun`, `defteam`, `qb_scramble` (exact column name gated in the PR C preflight doc itself) |
| Explicitly unsafe / out of scope for v0 | designed-QB-run indicator (no dedicated field; requires an identity/role join this issue's non-goals forbid) |

**Revision note:** an earlier draft of this audit classified `qb_kneel`, `qb_spike`, `two_point_attempt`, `penalty`, `sack`, and `aborted_play` handling as having "no in-repo reference." That was wrong — `scripts/build_team_week_raw_v0_2024_candidate.py`, its tests, and `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 already establish and validate (against a real, source-backed 2024 candidate, not a fixture) exactly this policy. Only `shotgun` itself — the field this entire spec turns on — has zero in-repo precedent of any kind.

---

## 3. Core derivation question: can `under_center` be safely derived?

**Decision: not unconditionally. The v0 artifact must not emit a plain `under_center` field derived only from `shotgun == 0`.** Instead, v0 must carry an explicit `unknown_or_unclassified_alignment` bucket, and the "non-shotgun" label must be named to reflect what it actually measures until a live pull confirms otherwise (§3.3).

### 3.1 Denominator answers

| question | answer for v0 |
|---|---|
| Are kneels excluded? | **Yes — and excluded from `offensive_plays` (the alignment denominator) entirely, not merely from rates.** `play_type == "qb_kneel"` rows are excluded via `is_competitive_play` in `scripts/build_team_week_raw_v0_2024_candidate.py`, matching the PR C preflight policy (§2, "Kneels"). **Correction from an earlier draft of this audit** (flagged by review, §3.1a below): that draft said kneels are "excluded from formation/tendency rates" while implying they might still count toward a raw offensive-play total — `team_week_raw_v0` itself keeps two *separate* denominators for exactly this reason (`offensivePlays`, kneel/spike-inclusive, vs. `competitivePlays`, pass/run only). `formation_summary_v0`'s `offensive_plays` field must mean the **latter** (`competitivePlays`-equivalent) so the reconciliation identity in §3.3 holds; see §3.1a. |
| Are spikes excluded? | **Yes**, same rule, same precedent, and same denominator-scoping correction as kneels (§2, "Spikes"; §3.1a). |
| Are no-plays excluded? | **Yes — and `formation_summary_v0` should reuse the already-proven `team_week_raw_v0` pattern, not the older `team_state` pattern.** `compute.py::_base_offense_plays` (the `tiber_team_state_v0_1` lane) derives the offensive-play set from `pass == 1 \| rush == 1 \| play_type in ["pass","run"]`. The `team_week_raw_v0` lane instead gates on **categorical `play_type` membership** (`is_offensive_play`/`is_competitive_play` in `scripts/build_team_week_raw_v0_2024_candidate.py`, validated against a real 2024 candidate) and the no-play policy is separately locked in the PR C preflight doc §2. `formation_summary_v0` should follow the `team_week_raw_v0` pattern: it has already been run successfully against real data, whereas the `pass`/`rush`-flag-only `team_state` pattern has not been proven against a case where those flags might not cleanly track play-type membership. |
| Are penalty-only rows excluded? | **Yes**, per the already-locked policy in `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Penalties") — a penalty that nullifies the entire play is excluded, same as a no-play; a penalty on an otherwise-recorded play does not remove that play. |
| Are special-teams plays excluded? | **Yes** — handled correctly by both the `team_state` and `team_week_raw_v0` filter patterns (§2), and separately locked in the PR C preflight doc §2. |
| Are two-point attempts excluded or separately tracked? | **Excluded from the offensive-play denominator entirely for v0**, matching the already-proven `team_week_raw_v0` policy (`is_offensive_play`/`is_competitive_play` both check `not row.get("two_point_attempt")`) rather than this audit's earlier (weaker) proposal of "excluded from the primary denominator, optionally tracked separately." A separate `two_point_plays` count may still be added if a future consumer needs it, but the default follows existing precedent: full exclusion. |
| Are missing shotgun values preserved as unknown instead of forced into under center? | **Yes — this is the central fail-closed rule of this spec.** A null/missing `shotgun` value must never default to `non_shotgun` (let alone `under_center`). It must fall into `unknown_or_unclassified_alignment`. **This bucket is defined solely by `shotgun` being null/missing** — see the correction in §3.3 below; it is not a home for pistol ambiguity. |
| Does the source distinguish pistol or other non-under-center/non-shotgun alignments? | **Unknown as of this audit — flagged, not assumed.** The standard nflverse/nflfastR pbp schema does not have a dedicated `pistol` (or other alignment) field alongside `shotgun`; formation is exposed as a single binary `shotgun` indicator. If the live source encodes pistol snaps as `shotgun == 0` (as community documentation for this source family suggests, unverified live per §0), those snaps have a **known, non-null** `shotgun` value — they are not unclassified, they are indistinguishably bucketed with genuine under-center snaps inside whatever `shotgun == 0` is labeled. **This is exactly why `shotgun == 0` cannot be safely relabeled `under_center` at v0**, and exactly why it is a labeling problem, not an unknown-alignment problem — see §3.3. |
| Does source `shotgun` mean alignment at snap, charted formation, or derived indicator? | **Unconfirmed.** Documented nflverse schema describes it as an upstream-charted, at-snap formation indicator (not something nflverse itself derives from other pbp columns) — but this claim is `documented_schema_unverified_live` and must be confirmed against real column metadata before implementation. |

### 3.1a Two-tier denominator: `offensive_plays` must mean the formation-eligible count, not the raw count (correction, review finding)

**Finding:** an earlier draft of this spec left `offensive_plays` ambiguous between two different counts that `team_week_raw_v0` already keeps separate: `is_offensive_play` (kneel/spike **included**, two-point excluded — `OFFENSIVE_PLAY_TYPES = {pass, run, qb_kneel, qb_spike}`) vs. `is_competitive_play` (pass/run **only**, two-point excluded — `PASS_RUN_PLAY_TYPES = {pass, run}`; used as the denominator for `passRate`/`rushRate`/`epaPerPlay`/etc.). If `formation_summary_v0`'s `offensive_plays` followed the broader (`is_offensive_play`) definition while `shotgun_plays`/`non_shotgun_plays`/`unknown_or_unclassified_alignment_plays` only cover pass/run snaps (kneels and spikes have no meaningful shotgun/non-shotgun tendency to report), the reconciliation identity in §3.3/§7 would be **mathematically impossible to satisfy** for any team-season containing a kneel or spike — those plays would be in the denominator but in none of the three alignment buckets.

**Resolution:** `formation_summary_v0`'s `offensive_plays` field is defined as the **competitive-play / formation-eligible denominator** — the `team_week_raw_v0` `competitivePlays`-equivalent (pass/run only; kneels, spikes, two-point attempts, no-plays, penalty-only rows, aborted plays, and special teams are excluded from it entirely, not just from rates). This is the only denominator the alignment buckets are ever measured against, and it is what §3.3's reconciliation identity refers to. A separate, optional `raw_offensive_plays` field (kneel/spike-inclusive, matching `team_week_raw_v0`'s broader `offensivePlays`) may be carried for cross-artifact comparison, but it is never used as an alignment-rate denominator and never appears in the reconciliation identity.

### 3.1b Pass/run split for `*_pass_rate`/`*_run_rate` must use the dropback indicator, not `play_type` (correction, review finding)

**Finding:** §2's `qb_scramble` row, in an earlier draft, said scrambles "fall correctly under the rush bucket via the categorical `play_type` filter" without scoping that claim to denominator *inclusion* only. `team_week_raw_v0`'s own precedent (`aggregate_game` in `scripts/build_team_week_raw_v0_2024_candidate.py`) does **not** use `play_type` to decide pass vs. rush for its rate fields — it uses the `qb_dropback` indicator: `dropback` truthy → `pass_plays`, else → `rush_plays`, applied only to already-competitive (`is_competitive_play`) rows. Under that precedent a scramble (`play_type == "run"`, `qb_dropback == 1`) is counted as a **pass** play for `passRate`/`passEpaPerPlay`. Naively using `play_type == "pass"`/`"run"` for `shotgun_pass_rate`/`shotgun_run_rate`/`non_shotgun_pass_rate`/`non_shotgun_run_rate` would silently reclassify scramble dropbacks as rush plays — a semantic fork from the exact precedent §2/§3.1a tell implementers to reuse, introduced by the artifact this spec is defining rather than inherited honestly from it.

**Resolution:** the pass/run split within each alignment bucket (`shotgun_pass_rate` vs. `shotgun_run_rate`, and the `non_shotgun` equivalents) must use the same verified dropback indicator `team_week_raw_v0` uses (`qb_dropback`), not raw `play_type` membership. If `qb_dropback` is null/unavailable for one or more plays in a team-season's formation-eligible set, `formation_summary_v0` must follow `team_week_raw_v0`'s own fail-closed precedent exactly: null-block the affected pass/run split fields for that row (mirroring `dropback_split_blocked`/`dropback_null_rows` in `scripts/build_team_week_raw_v0_2024_candidate.py`) rather than guessing an attribution from `play_type`. `play_type` remains the correct basis for §3.1a's denominator *inclusion* test (a scramble is still a qualifying offensive play) and for the `shotgun`/`non_shotgun`/`unknown` alignment split itself (alignment is orthogonal to dropback-vs-scramble) — only the pass-vs-run split within each alignment bucket must switch to `qb_dropback`.

### 3.2 Existing in-repo success-rate conflict (new finding, not in the issue text)

`src/team_state/definitions.py` and `src/team_state/compute.py` already define and compute a TIBER-specific success rule (yards-to-go thresholds by down: ≥40%/≥60%/100% on 1st/2nd/3rd+4th) for `tiber_team_state_v0_1`. The standard nflverse pbp schema is documented (unverified live) to also carry its **own** `success` column, defined independently (commonly an EPA-positive rule). If `formation_summary_v0` naively passes through nflverse's native `success` field for `shotgun_success_rate`/`under_center_success_rate`, TIBER-Data would silently carry **two different "success" definitions** across sibling artifacts (`team_state` vs. `formation_summary`), which is exactly the kind of quiet semantic drift `AGENTS.md` prohibits ("no enum drift / no contract drift").

**Recommendation:** if/when success-rate fields are implemented for `formation_summary_v0`, reuse the existing TIBER `team_state` down/distance success rule verbatim for cross-artifact consistency, rather than adopting nflverse's native `success` column under the same field name. If a future implementer prefers nflverse's own field instead, it must be named distinctly (e.g., `epa_success_rate` vs. `distance_success_rate`) so the fork is visible, never silent.

### 3.3 Recommended v0 alignment vocabulary

Given §3.1–3.2, v0 must use a **three-bucket** alignment classification, not a binary one — but the buckets are partitioned strictly by the observed `shotgun` value, not by confidence about what a bucket "really" contains:

- `shotgun_plays` — `shotgun == 1` on a qualifying offensive play (source_truth passthrough).
- `non_shotgun_plays` (**not** `under_center_plays`) — `shotgun == 0` on a qualifying offensive play. **Corrected in this revision** (flagged by review): this bucket is defined purely by the observed value `shotgun == 0`, full stop — it is not "possibly pistol, possibly under-center, undetermined." If the live source encodes pistol snaps as `shotgun == 0`, those snaps have a known, non-null value and belong here by construction, not in the unknown bucket (routing them to unknown instead would break the reconciliation identity below and would itself be a fabrication — inventing an "unclassified" status for a play the source did classify). The caveat is about what the *label* honestly means to a downstream reader, not about bucket membership: `non_shotgun` must be documented as "shotgun-negative," which **may silently include pistol formations** if the source does not separately flag them — it is not a verified "under center" claim, and consumers must not read it as one.
- `unknown_or_unclassified_alignment_plays` — qualifying offensive plays where `shotgun` itself is **null or missing** in the source. Nothing else belongs in this bucket. This is the fail-closed home for genuine source gaps, not for interpretive uncertainty about a value the source did provide.

**Reconciliation must hold exactly:** `shotgun_plays + non_shotgun_plays + unknown_or_unclassified_alignment_plays == offensive_plays`, using only the observed `shotgun` field value (§7) — this identity is why pistol ambiguity cannot be handled by moving rows into `unknown`; there is no third observed value to move them from.

**`under_center` may only replace `non_shotgun` as a field name in a later revision, after a live `nflreadpy.load_pbp()` pull confirms pistol-snap treatment** (e.g., pistol volume is negligible, or the source exposes a way to separate it out). Until then, using the label `under_center` for a bucket that may contain undetected pistol snaps would be an overclaim this repo's fail-closed posture (`TRUTH_SOURCES.md`) forbids — the fix is an honest label (`non_shotgun`) plus a documented caveat about what it may contain, not a reclassification into the unknown bucket.

---

## 4. Candidate artifact grain

**Recommendation: `team_season` only for the first governed artifact**, matching the issue's own default recommendation. Justification, consistent with this repo's existing precedent:

- `tiber_team_state_v0_1` (the closest sibling artifact) is already season/through-week scoped per team, not per team-week — `formation_summary_v0` following the same grain keeps the two artifacts structurally consistent for a future joint consumer.
- Teamstate's `formation_lens_v0` (upstream context) is a season-level human-readable explanation surface; it does not need weekly granularity to satisfy its stated purpose.
- A `team_week` grain multiplies the sample-size risk (§6) across 18× more rows per team before any of the alignment-ambiguity questions in §3 are resolved — bounding to `team_season` first keeps the initial safe surface smaller.

`team_week` may be added **later**, once `team_season` coverage and the alignment ambiguity in §3.3 are resolved, and once sample-size/warning behavior is proven reliable at the coarser grain first.

---

## 5. Candidate artifact envelope

Following this repo's established envelope shape (`tiber_team_state_v0_1`, `player_season_coverage_v0`):

```
artifact                  # "formation_summary_v0"
artifactVersion
generatedAt
season
sourceArtifacts           # e.g., ["nflverse-pbp"] with retrieval metadata (season, retrieval date, package version)
metadata
  seasonType               # REG-only for v0 default, explicit per row/artifact (never implicit — see player_season_coverage_v0 precedent, §4.2 of that spec)
  denominatorRule           # the exact offensive-play filter text from §3.1, versioned
  alignmentVocabulary       # ["shotgun", "non_shotgun", "unknown_or_unclassified_alignment"] — not "under_center" (§3.3)
coverage
  teamsCovered
  missingFields             # explicit array, e.g. ["defteam", "aborted_play"] if unconfirmed/unavailable at build time
governanceStatus / provenanceStatus   # never inferred from file path, file name, branch name, or consumer intent
rows
```

## 6. Candidate row shape

Adopting the issue's proposed row shape, with the alignment-vocabulary correction from §3.3:

```
season
week                          # optional; absent for team_season grain (§4)
grain                          # "team_season" for v0
team
offensive_plays                # formation-eligible/competitive-play denominator ONLY -- pass/run, kneel/spike/two-point/no-play/aborted/special-teams excluded entirely (§3.1a); this is what the reconciliation identity in §3.3/§7 uses
shotgun_plays
non_shotgun_plays              # NOT "under_center_plays" (§3.3)
unknown_or_unclassified_alignment_plays   # required, not optional — this is the fail-closed bucket, not a nice-to-have
shotgun_rate
non_shotgun_rate
unknown_alignment_rate
shotgun_pass_rate              # pass/run split MUST use qb_dropback, not play_type (§3.1b) -- a scramble is a pass play here
shotgun_run_rate
non_shotgun_pass_rate          # same qb_dropback-based split (§3.1b)
non_shotgun_run_rate
raw_offensive_plays            # optional; kneel/spike-inclusive count, team_week_raw_v0 offensivePlays-equivalent; NOT used in any rate denominator or the reconciliation identity (§3.1a)
two_point_plays                # tracked separately, excluded from offensive_plays entirely (§3.1a), not just from rates
shotgun_epa_per_play           # optional; null/"insufficient_data" until EPA inclusion rules and sample thresholds (§6.1) are met
non_shotgun_epa_per_play       # optional; same gating
shotgun_success_rate           # optional; MUST use the TIBER team_state success definition (§3.2), or be explicitly named otherwise
non_shotgun_success_rate       # optional; same
sample_notes
sourceRefs
provenanceStatus
```

Any optional efficiency field (`*_epa_per_play`, `*_success_rate`) must remain absent, null, or explicitly `"insufficient_data"` until (a) EPA/success definitions are source-backed and validation-safe per §3.2, and (b) the sample-size thresholds in §6.1 are met.

### 6.1 Sample-size and label thresholds (recommended, not deferred)

Reusing the existing `tiber_team_state_v0_1` precedent (`sampleFlag = "thin"` below 250 offensive plays, `src/team_state/definitions.py`) as a starting point, but set conservatively higher because `formation_summary_v0` further splits the sample into shotgun/non-shotgun/unknown sub-buckets:

- **Minimum offensive plays for a team-season row to be emitted at all:** 250 (matches existing team_state threshold; a team-season sample below this is already flagged `thin` elsewhere in this repo).
- **Minimum shotgun plays before shotgun efficiency prose (`shotgun_epa_per_play`/`shotgun_success_rate`) is allowed:** 100.
- **Minimum non-shotgun plays before non-shotgun efficiency prose is allowed:** 100.
- **Small samples suppress labels, not just warn.** Consistent with `AGENTS.md` ("null/unknown beats fake defaults"): below threshold, the efficiency field is omitted/null with a `sample_notes` explanation — it is not emitted with an attached low-confidence warning. Rate fields (not efficiency/prose fields) may still be emitted below threshold since they are exact counts, not modeled/interpreted values, but `sample_notes` must state the small-sample condition either way.
- **League-relative labels are not allowed in v0.** No league-baseline artifact currently exists in this repo to compute a defensible relative comparison against; this is deferred, not solved, pending a separate future baseline artifact.

---

## 7. Validation and fail-closed rules

A future `formation_summary_v0` artifact must fail closed if:

- required source fields are unavailable (§2.1's "must be live-verified" list resolves to *actually* unavailable at build time);
- `shotgun`/alignment values are missing above a declared threshold (recommend: if `unknown_or_unclassified_alignment_plays` exceeds 10% of `offensive_plays` for a team-season row, the row must carry an explicit high-uncertainty flag rather than presenting rates as if fully resolved);
- the offensive-play denominator rule (§3.1, §3.1a) is not applied consistently, or is ambiguous for a given row;
- `offensive_plays` is populated from the kneel/spike-inclusive raw count instead of the formation-eligible/competitive-play count (§3.1a) — this breaks the reconciliation identity below and is a hard validation failure;
- `non_shotgun` is emitted under the label `under_center` (§3.3) — this is a hard validation failure, not a style note;
- kneel, spike, no-play, penalty-only, two-point, or special-teams handling is not explicit per row/artifact metadata;
- `*_pass_rate`/`*_run_rate` are derived from `play_type` instead of the verified dropback indicator (§3.1b) — scramble misclassification is a hard validation failure, not a rounding concern;
- a team-season has one or more formation-eligible plays with a null/unavailable dropback indicator and `*_pass_rate`/`*_run_rate` are emitted anyway instead of null-blocked (§3.1b, mirroring `team_week_raw_v0`'s `dropbackSplitBlocked`);
- team/season coverage is incomplete without explicit `missingFields` metadata;
- source snapshot/version (`nflreadpy`/nflverse release identifier) is missing;
- `sourceRefs` are missing;
- `governanceStatus`/`provenanceStatus` markers are missing, unrecognized, or inferred from path/branch/filename rather than stated explicitly;
- sample-size thresholds (§6.1) are not declared or not enforced;
- rates do not reconcile with counts within tolerance (`shotgun_plays + non_shotgun_plays + unknown_or_unclassified_alignment_plays == offensive_plays`, exactly, not approximately, using the formation-eligible `offensive_plays` from §3.1a — never the kneel/spike-inclusive raw count);
- `success` is emitted without disclosing which definition (TIBER `team_state` rule vs. nflverse native field, §3.2) was used.

---

## 8. Relationship to existing lanes

| lane | relationship |
|---|---|
| `team_week_raw_v0` (`scripts/build_team_week_raw_v0_2024_candidate.py`, `docs/data/team-week-raw-v0-2024-pr-c-preflight.md`) | **Closest real-data precedent, not a dependency.** This lane already has a real, source-backed 2024 candidate (544 rows, `partial_real_data`, validated) that solves no-play/kneel/spike/penalty/sack/scramble/aborted-play/two-point/special-teams exclusion using categorical `play_type` membership. `formation_summary_v0` should **reuse this pattern and cite this precedent**, not re-derive denominator policy from scratch (§3.1, §8's earlier draft under-credited this lane). |
| `tiber_team_state_v0_1` (`src/team_state/**`) | **Sibling, not a dependency.** Shares the general offensive-play-filter *shape* (posteam non-null gate) but its `pass`/`rush`-flag-only pattern (`compute.py::_base_offense_plays`) is the **weaker** of the two in-repo patterns for no-play exclusion — prefer the `team_week_raw_v0` pattern above. Shares (and must not fork silently from) the success-rate definition (§3.2). |
| `formation_lens_v0` (TIBER-Teamstate #75/#76) | **Downstream consumer, not started here.** That spec is documentation-only and explicitly blocked from real-data interpretation until this artifact exists, passes validation, and is separately approved for consumption. Nothing here wires that connection. |
| `player_season_coverage_v0` (#188) | **Shape/vocabulary precedent only.** This spec reuses its `truth_status` vocabulary and envelope shape for consistency; no data or code dependency. |
| Fantasy / Forecast | **Out of scope entirely.** Not referenced by field, grain, or envelope choice in this document. |

---

## 9. Recommended next issue (separate, gated — not authorized by this document)

**This document concludes the contract is conditionally feasible, gated on live-data verification.** The verification surface is narrower than an earlier draft of this audit assumed, now that `team_week_raw_v0`'s real 2024 candidate (§2, §3.1, §8) is credited correctly: denominator policy for kneels, spikes, no-plays, penalties, sacks, two-point attempts, and special teams is already proven. What remains open is specific to alignment, not to the general offensive-play denominator. The next safe step is **not** a fixture-scaffold implementation issue yet — it is a narrower verification step:

**`audit: verify nflreadpy.load_pbp() shotgun/formation column availability for formation_summary_v0 (read-only, no artifact)`**, scoped to:

1. a single bounded, already-complete recent regular season (the 2024 season already has a validated `team_week_raw_v0` candidate build to cross-reference against);
2. confirm presence/absence and null rates of `shotgun` and `defteam` specifically — the two fields with zero in-repo precedent of any kind;
3. specifically resolve the pistol-formation question in §3.1/§3.3 (does the raw source distinguish pistol at all; if not, confirm whether pistol snaps fall into `shotgun == 0` or are otherwise unrecoverable) — this is the one open question that actually blocks the `under_center` label;
4. confirm the exact scramble-indicator column name, which `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 itself leaves **GATED** pending retrieval — reuse that resolution once it exists rather than re-gating it here;
5. **produce no artifact, no schema, no promoted data** — only a committed audit report (`docs/audits/`) updating the remaining `documented_schema_unverified_live` tags in §2 to `verified_in_repo`.

Only after that verification step resolves (or explicitly narrows) the open questions in §3 should a `feat: build formation_summary_v0 (bounded, source-bounded, gated)` implementation/dry-run issue be opened, with gates modeled on §7 (this document does not authorize that issue).

---

## Appendix — Referenced facts

- `src/team_state/loader.py` calls `nflreadpy.load_pbp(seasons=[season])` in production; this is the accepted TIBER-Data play-by-play loader.
- `src/team_state/definitions.py::REQUIRED_PBP_COLUMNS` = `posteam, season, season_type, week, game_id, drive, down, ydstogo, yards_gained, touchdown, first_down, score_differential` — notably **no `shotgun` field anywhere in this list or in the repo**.
- `team-state/fixtures/pbp_fixture.json` is a fixture (5 rows), shape reference only, and also has **no `shotgun` field** — consistent with it never having been needed by any artifact built so far.
- **`team_week_raw_v0` real 2024 candidate** (`exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`, 544 rows, `partial_real_data`, `allPassed: true`) is genuine source-backed evidence, not a fixture — built from a real nflverse release-asset fetch (`scripts/build_team_week_raw_v0_2024_candidate.py::retrieve_pbp`, via a direct `httpx.Client().get()` call against the same URL `nflreadpy.load_pbp([2024])`/`load_schedules([2024])` would resolve, **not** via those functions themselves — corrected above) — that `play_type`, `qb_kneel`, `qb_spike`, `two_point_attempt`, `qb_dropback`, `sack`, `interception`, `fumble_lost`, `epa`, `success`, `fixed_drive`, `pass_touchdown`, `rush_touchdown`, `quarter_seconds_remaining`, and `game_half` all exist and behave as expected in the real ingested schema. It does **not** touch `shotgun` or `defteam` at all — those two remain the genuinely unverified fields.
- `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 separately locks the play-inclusion policy (no-plays, penalties, kneels, spikes, sacks, scrambles, aborted plays, special teams) that this spec's §3.1 now cites instead of re-deriving.
- Live `nflreadpy.load_pbp(seasons=[2024])` fetch attempted **in this session** (distinct from the `team_week_raw_v0` build above, which reached the release asset via `httpx`, not via this function — corrected above), blocked by this session's egress policy (403 on the nflverse-data release asset host) — reported per environment guidance, not retried. A follow-up verification session (`docs/audits/formation-summary-v0-live-pbp-field-verification-2026-07-09.md`) repeated this same attempt with the same result.
- Truth-status vocabulary (reused): `source_truth | derived_summary | unavailable | out_of_scope`, extended here with `unsafe_for_v0`.
- Verification-status vocabulary (new, this spec): `verified_in_repo | documented_schema_unverified_live`.
