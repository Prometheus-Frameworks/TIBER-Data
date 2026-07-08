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

This is a sandbox egress-policy denial for this session (per this environment's proxy status: `recentRelayFailures` policy block on the release-asset host), **not** evidence that the source is unreachable in general — `src/team_state/loader.py` already depends on this exact call (`nflreadpy.load_pbp(seasons=[season])`) succeeding in the repo's real execution environment today. Per this environment's own operating guidance, a 403 from an organization egress policy is reported, not retried or routed around.

Because of that, the field classification in §2 combines:

1. **In-repo evidence** (verified by reading committed files in this session): `src/team_state/loader.py`, `src/team_state/definitions.py` (`REQUIRED_PBP_COLUMNS`), `src/team_state/compute.py` (existing offensive-play filter and success-rule logic), and `team-state/fixtures/pbp_fixture.json` (fixture shape only).
2. **The published nflverse/nflfastR play-by-play data dictionary** — external, well-established public documentation for this exact source family, cited as a **documented-schema reference**, not a live pull verified in this session.

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
| no-play indicator (`play_type == "no_play"` or equivalent) | native | source_truth | documented_schema_unverified_live | No in-repo reference. Existing `compute.py::_base_offense_plays` relies only on `pass == 1 \| rush == 1 \| play_type in ["pass","run"]` — this is a known risk (see §3.1): a no-play row negated by a pre-snap penalty can still carry `pass`/`rush` = 1 in the standard nflverse schema, reflecting the on-field action rather than the accepted outcome. |
| kneel indicator (`qb_kneel`) | native | source_truth | documented_schema_unverified_live | No in-repo reference. Required to exclude kneels from the offensive-play denominator (§3.1) — kneels are not formation-tendency plays. |
| spike indicator (`qb_spike`) | native | source_truth | documented_schema_unverified_live | No in-repo reference. Same exclusion requirement as kneels. |
| penalty-only row handling | native | source_truth | documented_schema_unverified_live | A `penalty` indicator is standard in nflverse pbp; a penalty can occur on a real, otherwise-classifiable play (e.g., accepted defensive holding on a completed pass) or can be the *entire* play (no snap counted). These two cases must not be conflated — only the latter is excluded (folded into the no-play exclusion above). |
| two-point attempt handling (`two_point_attempt`) | native | source_truth | documented_schema_unverified_live | No in-repo reference. See §3.1 for recommended handling (excluded from primary denominator, optionally tracked separately). |
| special-teams exclusion | derived | derived_summary | verified_in_repo | Already handled correctly by the existing offensive-play filter pattern in `compute.py`: special-teams `play_type` values (`punt`, `field_goal`, `kickoff`, `extra_point`) are outside `["pass", "run"]` and have `pass == 0`/`rush == 0`, so they fall out of the filter without extra rules. |
| sack handling (`sack`) | native | source_truth | documented_schema_unverified_live | No in-repo reference. Standard nflverse pbp keeps sacks coded as pass plays (`play_type == "pass"`, `pass == 1`) — a sack does not need separate exclusion from the offensive-play denominator, but formation attribution for a sacked dropback should follow the same `shotgun` value as any other dropback. |
| scramble handling (`qb_scramble`) | native | source_truth | documented_schema_unverified_live | No in-repo reference. Per the standard nflverse schema, scrambles are typically coded with `play_type == "run"` / `rush == 1` (the ball was run), while also carrying `qb_dropback == 1` (the play originated as a dropback). For `formation_summary_v0`'s offensive-play denominator (run + pass only, not a dropback-rate denominator), this is **not a problem to solve at v0** — scrambles fall correctly under the rush bucket via the existing filter shape. Flag only so a future pass-rate-over-expectation-style artifact does not double-count scrambles without knowing this quirk. |
| designed QB run handling | derived, requires rusher-role join | unsafe_for_v0 | documented_schema_unverified_live | No dedicated field distinguishes a designed QB run from an RB carry or a scramble without joining rusher identity/position — out of scope per this issue's own non-goals ("infer offensive scheme labels ... without a separate governed taxonomy"). **Not attempted.** |
| aborted/botched play handling (`aborted_play`) | native | source_truth | documented_schema_unverified_live | No in-repo reference; presence/absence in the actually-ingested schema version is unconfirmed. If present, exclude from the denominator (unclassifiable snap). If absent, flag as `unavailable` and note the residual risk in `missing_fields` rather than silently assuming zero aborted plays. |
| `down` | native | source_truth | verified_in_repo | In fixture and used throughout `compute.py`. |
| `distance` (`ydstogo`) | native | source_truth | verified_in_repo | Same. |
| yardline / red-zone context (`yardline_100`) | native | source_truth | verified_in_repo | Used for `is_red_zone_play` in `compute.py`. |
| score / game-script context (`score_differential`, `game_seconds_remaining`) | native | source_truth | verified_in_repo | Used for neutral-situation and garbage-time logic in `compute.py`/`definitions.py`. |
| `epa` | native (provider-modeled) | source_truth, but flag as **provider_model_derived** | documented_schema_unverified_live | Not currently consumed anywhere in this repo. This is nflverse's own modeled advanced stat (not raw NFL data) — safe to pass through as an optional field, but the artifact must disclose it is a third-party model output, not a raw measurement, consistent with the issue's "insufficient_data until source-backed" posture for optional efficiency fields. |
| success indicator | **conflict**, see §3.2 | derived_summary | verified_in_repo (existing TIBER definition) / documented_schema_unverified_live (nflverse's own field) | TIBER-Data **already has** a governed success-rate definition in `src/team_state/definitions.py`/`compute.py` (≥40% of yards-to-go on 1st down, ≥60% on 2nd, 100% on 3rd/4th) — independent of whatever `success` column nflverse's pbp may also carry. See §3.2: do not silently pick one without naming the fork. |

### 2.1 Summary: field readiness for a future implementation

| status | fields |
|---|---|
| Ready today (verified in repo, already used by an existing TIBER artifact) | `season`, `week`, `game_id`, `posteam`, `play_type`, `pass`, `rush`, `down`, `ydstogo`, `yardline_100`, `score_differential`, `game_seconds_remaining` |
| Plausible but **must be live-verified before use** (no in-repo precedent) | `shotgun`, `defteam`, no-play indicator, `qb_kneel`, `qb_spike`, `penalty`, `two_point_attempt`, `sack`, `qb_scramble`, `aborted_play`, `epa` |
| Explicitly unsafe / out of scope for v0 | designed-QB-run indicator (no dedicated field; requires an identity/role join this issue's non-goals forbid) |

---

## 3. Core derivation question: can `under_center` be safely derived?

**Decision: not unconditionally. The v0 artifact must not emit a plain `under_center` field derived only from `shotgun == 0`.** Instead, v0 must carry an explicit `unknown_or_unclassified_alignment` bucket, and the "non-shotgun" label must be named to reflect what it actually measures until a live pull confirms otherwise (§3.3).

### 3.1 Denominator answers

| question | answer for v0 |
|---|---|
| Are kneels excluded? | **Yes.** `qb_kneel == 1` rows are excluded from the offensive-play denominator regardless of `pass`/`rush` values — kneels are not formation-tendency plays. |
| Are spikes excluded? | **Yes**, same rule as kneels (`qb_spike == 1`). |
| Are no-plays excluded? | **Yes, but not the way the existing `team_state` filter does it.** `compute.py::_base_offense_plays` currently derives the offensive-play set from `pass == 1 \| rush == 1 \| play_type in ["pass","run"]` alone. That is insufficient for a formation artifact: in the standard nflverse schema, a no-play row negated by a pre-snap penalty can still carry `pass`/`rush` = 1 (reflecting the on-field action, not the accepted outcome). `formation_summary_v0`'s denominator must **explicitly** exclude rows where the no-play indicator is set, independent of `pass`/`rush`, rather than relying on those flags to do it implicitly. |
| Are penalty-only rows excluded? | **Yes**, folded into the no-play exclusion above — only the case where the penalty *is* the entire play (no snap counted). A penalty on an otherwise-live, classifiable play is not excluded. |
| Are special-teams plays excluded? | **Yes** — already handled correctly by the existing `play_type in ["pass","run"]` shape (§2). |
| Are two-point attempts excluded or separately tracked? | **Excluded from the primary team-season denominator for v0**, optionally counted in a separate `two_point_plays` field. Two-point plays are a small, situationally distinct subset (disproportionately shotgun by design) that would distort shotgun/under-center rates if mixed into the main denominator. |
| Are missing shotgun values preserved as unknown instead of forced into under center? | **Yes — this is the central fail-closed rule of this spec.** A null/missing `shotgun` value must never default to `under_center = 1`. It must fall into `unknown_or_unclassified_alignment`. |
| Does the source distinguish pistol or other non-under-center/non-shotgun alignments? | **Unknown as of this audit — flagged, not assumed.** The standard nflverse/nflfastR pbp schema does not have a dedicated `pistol` (or other alignment) field alongside `shotgun`; formation is exposed as a single binary `shotgun` indicator. Community documentation for this source family describes pistol snaps as ambiguous under a binary shotgun/non-shotgun encoding, but this audit could not independently re-verify that against a live pull (§0). **This is exactly why `shotgun == 0` cannot be safely relabeled `under_center` at v0** — some non-shotgun rows may be pistol snaps, not under-center snaps, and this spec has no verified way to tell them apart. |
| Does source `shotgun` mean alignment at snap, charted formation, or derived indicator? | **Unconfirmed.** Documented nflverse schema describes it as an upstream-charted, at-snap formation indicator (not something nflverse itself derives from other pbp columns) — but this claim is `documented_schema_unverified_live` and must be confirmed against real column metadata before implementation. |

### 3.2 Existing in-repo success-rate conflict (new finding, not in the issue text)

`src/team_state/definitions.py` and `src/team_state/compute.py` already define and compute a TIBER-specific success rule (yards-to-go thresholds by down: ≥40%/≥60%/100% on 1st/2nd/3rd+4th) for `tiber_team_state_v0_1`. The standard nflverse pbp schema is documented (unverified live) to also carry its **own** `success` column, defined independently (commonly an EPA-positive rule). If `formation_summary_v0` naively passes through nflverse's native `success` field for `shotgun_success_rate`/`under_center_success_rate`, TIBER-Data would silently carry **two different "success" definitions** across sibling artifacts (`team_state` vs. `formation_summary`), which is exactly the kind of quiet semantic drift `AGENTS.md` prohibits ("no enum drift / no contract drift").

**Recommendation:** if/when success-rate fields are implemented for `formation_summary_v0`, reuse the existing TIBER `team_state` down/distance success rule verbatim for cross-artifact consistency, rather than adopting nflverse's native `success` column under the same field name. If a future implementer prefers nflverse's own field instead, it must be named distinctly (e.g., `epa_success_rate` vs. `distance_success_rate`) so the fork is visible, never silent.

### 3.3 Recommended v0 alignment vocabulary

Given §3.1–3.2, v0 must use a **three-bucket** alignment classification, not a binary one:

- `shotgun_plays` — `shotgun == 1` on a qualifying offensive play (source_truth passthrough).
- `unknown_or_unclassified_alignment_plays` — qualifying offensive plays where `shotgun` is null/missing, **or** (until a live pull settles the pistol question) explicitly documented as a superset that *may* include pistol snaps.
- `non_shotgun_plays` (**not** `under_center_plays`) — `shotgun == 0` on a qualifying offensive play, labeled honestly as "non-shotgun" rather than "under center" until a live pull confirms the source either has no material pistol volume or exposes a way to separate it out.

**`under_center` may only replace `non_shotgun` as a field name in a later revision, after a live `nflreadpy.load_pbp()` pull confirms pistol-snap treatment.** Until then, using the label `under_center` would be an overclaim this repo's fail-closed posture (`TRUTH_SOURCES.md`) forbids.

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
offensive_plays                # denominator per §3.1
shotgun_plays
non_shotgun_plays              # NOT "under_center_plays" (§3.3)
unknown_or_unclassified_alignment_plays   # required, not optional — this is the fail-closed bucket, not a nice-to-have
shotgun_rate
non_shotgun_rate
unknown_alignment_rate
shotgun_pass_rate
shotgun_run_rate
non_shotgun_pass_rate
non_shotgun_run_rate
two_point_plays                # tracked separately, excluded from the rates above (§3.1)
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
- the offensive-play denominator rule (§3.1) is not applied consistently, or is ambiguous for a given row;
- `non_shotgun` is emitted under the label `under_center` (§3.3) — this is a hard validation failure, not a style note;
- kneel, spike, no-play, penalty-only, two-point, or special-teams handling is not explicit per row/artifact metadata;
- team/season coverage is incomplete without explicit `missingFields` metadata;
- source snapshot/version (`nflreadpy`/nflverse release identifier) is missing;
- `sourceRefs` are missing;
- `governanceStatus`/`provenanceStatus` markers are missing, unrecognized, or inferred from path/branch/filename rather than stated explicitly;
- sample-size thresholds (§6.1) are not declared or not enforced;
- rates do not reconcile with counts within tolerance (`shotgun_plays + non_shotgun_plays + unknown_or_unclassified_alignment_plays == offensive_plays`, exactly, not approximately);
- `success` is emitted without disclosing which definition (TIBER `team_state` rule vs. nflverse native field, §3.2) was used.

---

## 8. Relationship to existing lanes

| lane | relationship |
|---|---|
| `tiber_team_state_v0_1` (`src/team_state/**`) | **Closest sibling, not a dependency.** Shares the offensive-play-filter *pattern* (posteam non-null, pass/rush/play_type gate) but `formation_summary_v0` must tighten that pattern for no-play/kneel/spike exclusion (§3.1) — do not assume `compute.py::_base_offense_plays` is sufficient as-is for a formation artifact. Shares (and must not fork silently from) the success-rate definition (§3.2). |
| `formation_lens_v0` (TIBER-Teamstate #75/#76) | **Downstream consumer, not started here.** That spec is documentation-only and explicitly blocked from real-data interpretation until this artifact exists, passes validation, and is separately approved for consumption. Nothing here wires that connection. |
| `player_season_coverage_v0` (#188) | **Shape/vocabulary precedent only.** This spec reuses its `truth_status` vocabulary and envelope shape for consistency; no data or code dependency. |
| Fantasy / Forecast | **Out of scope entirely.** Not referenced by field, grain, or envelope choice in this document. |

---

## 9. Recommended next issue (separate, gated — not authorized by this document)

**This document concludes the contract is conditionally feasible, gated on live-data verification.** The next safe step is **not** a fixture-scaffold implementation issue yet — it is a narrower verification step:

**`audit: verify nflreadpy.load_pbp() column availability for formation_summary_v0 (read-only, no artifact)`**, scoped to:

1. a single bounded, already-complete recent regular season;
2. confirm presence/absence and null rates of: `shotgun`, `defteam`, no-play indicator, `qb_kneel`, `qb_spike`, `two_point_attempt`, `sack`, `qb_scramble`, `aborted_play`, `epa`, native `success` (if any);
3. specifically resolve the pistol-formation question in §3.1 (does the raw source distinguish pistol at all; if not, confirm whether pistol snaps fall into `shotgun == 0` or are otherwise unrecoverable);
4. confirm whether a no-play row can carry `pass`/`rush` = 1 in the actual data (§3.1), which determines whether the existing `team_state`-style filter is unsafe to reuse as-is;
5. **produce no artifact, no schema, no promoted data** — only a committed audit report (`docs/audits/`) updating the `documented_schema_unverified_live` tags in §2 to `verified_in_repo`.

Only after that verification step resolves (or explicitly narrows) the open questions in §3 should a `feat: build formation_summary_v0 (bounded, source-bounded, gated)` implementation/dry-run issue be opened, with gates modeled on §7 (this document does not authorize that issue).

---

## Appendix — Referenced facts

- `src/team_state/loader.py` calls `nflreadpy.load_pbp(seasons=[season])` in production; this is the accepted TIBER-Data play-by-play loader.
- `src/team_state/definitions.py::REQUIRED_PBP_COLUMNS` = `posteam, season, season_type, week, game_id, drive, down, ydstogo, yards_gained, touchdown, first_down, score_differential` — notably **no `shotgun` field anywhere in this list or in the repo**.
- `team-state/fixtures/pbp_fixture.json` is a fixture (5 rows), shape reference only, and also has **no `shotgun` field** — consistent with it never having been needed by any artifact built so far.
- Live `nflreadpy.load_pbp(seasons=[2024])` fetch attempted this session, blocked by session egress policy (403 on the nflverse-data release asset host) — reported per environment guidance, not retried.
- Truth-status vocabulary (reused): `source_truth | derived_summary | unavailable | out_of_scope`, extended here with `unsafe_for_v0`.
- Verification-status vocabulary (new, this spec): `verified_in_repo | documented_schema_unverified_live`.
