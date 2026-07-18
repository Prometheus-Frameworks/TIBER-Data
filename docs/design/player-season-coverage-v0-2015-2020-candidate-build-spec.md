# Candidate-Build Specification: `player_season_coverage_v0` — 2015–2020 REG

## 1. Status and authority

- **Status:** `design_specification_not_implemented`. This document is a reviewable,
  implementation-ready but **non-executable** specification. No candidate rows, builder
  code, tests, schemas, manifests, or promoted artifacts exist or change because this
  document exists.
- **Tracking issue:** TIBER-Data#220 (design-only frontier; bounded successor to #216,
  #218, PR #217, PR #219).
- **Operator activation:** issue #220 comment `5011745318` (2026-07-18, owner account),
  containing the exact approved phrase
  `[DECISION — APPROVED] Activate the 2015–2020 candidate-build design frontier in TIBER-Data issue #220.`
  That activation authorizes **documentation work only**: this file.
- **Authorized base:** `main` at `251f2369bd5700d9a3afe66269aaae4a60d61fa8`
  (the accepted #218/PR #219 merge). Verified unchanged at branch creation.
- **What this document may authorize:** nothing by itself. Its only positive outcome is
  the terminal design decision in §20, which permits the operator to *consider* a
  separate implementation activation. Candidate implementation requires another explicit
  operator decision after this design is independently reviewed.

## 2. Task classification

Under `AGENTS.md`'s task-classification gate this is a **repo-governance /
documentation task** producing a design doctrine document for a *future* data artifact
task. It inherits the constraints of the data-artifact class it describes without
performing any of that class's work:

- writable surface: exactly this file
  (`docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md`);
- `HANDOFF.md` is deliberately **not** modified in the initial design PR; it may be
  updated only after this design reaches an independently reviewed terminal state;
- no file under `data/**`, `exports/**`, `schemas/**`, `src/contracts/**`,
  `scripts/**`, or `tests/**` changes;
- the promoted 2021–2025 artifact, its manifest, the accepted builders, the audit
  script (blob `529f832b050dba494146f4b133c202072f587c0e`), and README support claims
  are read-only constraints.

## 3. Accepted evidence lock

All normative claims in this specification derive from the following pinned, committed
evidence. Nothing here widens that evidence's meaning.

| item | pinned value |
|---|---|
| accepted `main` commit | `251f2369bd5700d9a3afe66269aaae4a60d61fa8` |
| accepted audit-script blob | `529f832b050dba494146f4b133c202072f587c0e` (`scripts/audit_player_season_coverage_2015_2020_source_availability.py`) |
| human-readable audit evidence | `docs/reports/player-season-coverage-v0-2015-2020-source-availability.md` |
| machine-readable audit evidence | `docs/reports/player-season-coverage-v0-2015-2020-source-availability.json` |
| audit terminal decision | `may_open_player_season_coverage_2015_2020_candidate_build_issue` |
| audit environment | operator-local, Python 3.14.0, nflreadpy 0.1.5 (recorded in the evidence report) |
| approved source family | `nflreadpy.load_player_stats(...)`, `nflreadpy.load_players()` (allowlist in `exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json`) |
| promoted window (unchanged) | 2021–2025 REG only; promoted sha256 `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac` |

Audited per-season facts this design binds to (from the machine-readable evidence
report):

| season | REG weeks observed | gaps | wrong-season rows | dup grain | identity join | max games | unique QB/RB/WR/TE players |
|---|---|---|---|---|---|---|---|
| 2015 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | 16 | 556 |
| 2016 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | 16 | 557 |
| 2017 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | 16 | 553 |
| 2018 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | 16 | 577 |
| 2019 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | **17** | 572 |
| 2020 | 1–17 contiguous | 0 | 0 | 0 | 1.0 | 16 | 602 |

Identity-field availability for joined players (audited): `birth_date` 1.0,
`rookie_season` 1.0, draft fields (`draft_year`/`draft_round`/`draft_pick`/
`draft_team`) ≈ 0.69 — nullable, never fabricated.

## 4. Ownership and non-goals

TIBER-Data owns source-backed player-history evidence artifacts and their contracts.
This design does **not** own and must never drift into:

- promotion or consumer availability (separate gates, §15);
- any merge of 2015–2020 rows with the promoted 2021–2025 artifact (a separately
  governed step modeled on #206, requiring its own issue, review, and promotion);
- TIBER-Forecast mirrors, validation, features, or activation;
- historical ADP or market-data ingestion (separate unresolved provenance dependency);
- rebound/bust cohort research, rankings, projections, advice, or product behavior;
- modification of the 2021 or 2022–2025 builders, the audit script, schemas,
  validators, manifests, promoted artifacts, or README support claims.

The phrase **"2015–2025 is available" remains prohibited** at every stage this
document describes.

## 5. Proposed file-surface inventory

When (and only when) implementation is separately activated, the build may touch
exactly these new surfaces. Every path is candidate-scoped; none collides with a
promoted or accepted path.

| surface | exact proposed path |
|---|---|
| candidate artifact | `data/processed/evidence/player_season_coverage_2015_2020_candidate.source_backed.json` |
| candidate manifest | `data/processed/evidence/player_season_coverage_2015_2020_candidate.source_backed.MANIFEST.json` |
| validation result (machine-readable) | `docs/reports/player-season-coverage-v0-2015-2020-candidate-validation.json` |
| build report (human-readable) | `docs/reports/player-season-coverage-v0-2015-2020-candidate-build.md` |
| build report (machine-readable) | `docs/reports/player-season-coverage-v0-2015-2020-candidate-build.json` |
| historical builder | `scripts/build_player_season_coverage_2015_2020_candidate.py` |
| offline tests | `tests/test_build_player_season_coverage_2015_2020_candidate.py` |

Rules:

- **Row scope:** the candidate contains **exactly 2015–2020 REG rows** for positions
  QB/RB/WR/TE. It never contains 2021+ rows. Any later 2015–2025 merged candidate is a
  **separately governed step** (own issue, own review, own promotion gate, modeled on
  the #206 merged-candidate + #202 promotion-review pattern) and is *not* authorized by
  this design or by the candidate build it specifies.
- **Prohibited writes:** the builder must refuse (path-guard identical in spirit to the
  2021 builder's promoted-path guard) to write under `exports/**` generally and
  `exports/promoted/**` specifically, and must not modify
  `exports/promoted/nfl/player_season_coverage_v0.json`, its
  `PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json`, the 2021/2022–2025 builders, or
  README support claims. These prohibitions are hard test assertions (§14, N-17/G-3/G-4).
- **Candidate manifest content:** sha256 of the artifact, seasons, per-season and
  per-position counts, environment metadata (§6), the pinned evidence lock (§3), the
  exact source calls executed, and `status: candidate_evidence_artifact_not_promoted`.
  The manifest is candidate-scoped evidence; it is not a promotion manifest and confers
  no governed status.
- **Deterministic ordering:** records sorted by `(season, player_id)` ascending
  (family convention); all object keys emitted in fixed insertion order defined by the
  builder; per-season sections of reports ordered ascending by season.
- **Canonical serialization:** `json.dumps(payload, indent=2, allow_nan=False)` plus a
  single trailing newline, UTF-8 (family convention). `NaN`/`Inf` are forbidden by
  `allow_nan=False`; unavailable values are `null`, never sentinel numbers.
- **Repeat-run identity:** the builder accepts an explicit `--generated-at <ISO-8601>`
  argument. Two runs with the same `--generated-at` against unchanged upstream data
  must be **byte-identical** (test G-2). Without the flag, `generated_at` defaults to
  now-UTC and repeat runs must be identical after normalizing only the
  `generated_at`/`observed_at` timestamp fields.

## 6. Source-to-row derivation contract

- **Approved calls (per season, isolated):**
  - `nflreadpy.load_player_stats(seasons=[year], summary_level="week")`
  - `nflreadpy.load_player_stats(seasons=[year], summary_level="reg")`
  - one shared `nflreadpy.load_players()` for identity/birth/rookie/draft metadata.

  Six independent week-level and six independent reg-level calls (one per season),
  mirroring the accepted audit's per-season isolation. No other source, mirror,
  fallback, cache-substitution, or provider is permitted; **any source substitution
  requires a new source-audit issue first.**
- **Environment/dependency metadata recorded** in the candidate manifest and build
  report: Python version, nflreadpy version, polars version, OS platform, UTC build
  timestamp, and the §3 evidence lock (accepted main SHA + audit-script blob).
- **Accepted-source fingerprint gate (G1 correction round):** candidate generation is
  bound to the accepted #218 evidence, not merely reconciled against it afterwards.
  Before any output is staged, the implementation must verify:
  - **dependency pin:** the installed nflreadpy version is **exactly `0.1.5`** — the
    version the accepted #218 audit observed. Any other version aborts; no
    "newer-but-checks-pass" acceptance exists under the current evidence lock.
  - **per-season fingerprint:** for every season 2015–2020, the freshly loaded source
    must agree **exactly** with the accepted #218 machine-readable evidence report on:
    week-level total row count; week-level REG row count; REG-summary total row
    count; included QB/RB/WR/TE row and player counts; unique included player count;
    the exact REG week set; wrong-season row counts (must be 0); duplicate grain
    count (must be 0); maximum games observed; and identity-join rate.

  Any dependency-version or fingerprint mismatch must: abort **before any output is
  staged**; emit a bounded source-evidence-drift diagnostic (aggregate expected-vs-
  observed values only, no player rows); produce **no candidate**; and require a new
  source-audit issue plus explicit operator acceptance before the evidence lock may
  change. Structural drift and dependency drift are therefore never silently
  accepted under the existing #218 authority.
- **Value-level drift and source-content hashes (G1 round,
  discussion_r3608751684):** the aggregate fingerprint detects *structural* drift
  only. #218 recorded no row-level values, so value-level drift inside unchanged
  aggregates (a corrected stat, team, player name, birth date, or draft value) is
  **not detectable against #218**, and this design does not claim that it is. The
  authority claim is narrowed accordingly, and value-level drift is bounded instead
  of ignored:
  - at build time the builder computes deterministic sha256 source-content hashes
    over canonically serialized rows restricted to exactly the columns the build
    consumes, covering **both** consumed frames (discussion_r3608761219): per season,
    one hash over the week-level rows sorted by `(season, player_id, week)`, and one
    hash over the REG-summary rows — which carry no `week` column and supply `games`,
    player name, and the season rollup stats — sorted by `(season, player_id)`; plus
    one hash over the consumed `load_players()` identity fields of joined players,
    sorted by `gsis_id`. All **thirteen** source-content hashes (six week-level, six
    REG-summary, one identity) are recorded in the candidate manifest and build
    report, so no consumed value at either level sits outside the accepted rebuild
    hash;
  - those recorded hashes make the exact consumed source content part of the
    candidate's reviewable evidence: row **values** are accepted at gates G4/G5 by
    the independent audit and operator acceptance — never silently under #218;
  - once a candidate has been accepted (G5), any rebuild must reproduce the accepted
    per-season source-content hashes exactly or abort before staging with a drift
    diagnostic; a value-level upstream correction therefore requires a fresh
    source-audit issue and explicit operator acceptance before any republication.
- **Row-level source references:** identical semantics to the accepted 2021 builder —
  every record carries `source_refs` whose `source_name` values start with the approved
  prefixes (`nflreadpy.load_player_stats(`, `nflreadpy.load_players(`), with
  `observed_at`, `confidence: source_verified`, and explanatory notes. The existing
  validator's all-source allowlist check applies unchanged.
- **Lineage:** the artifact's top-level metadata must cite: tracking issue #220 (and
  the future implementation-activation issue), the #218 audit evidence reports, the
  accepted merge commit `251f236…`, and the audit-script blob `529f832…`. Lineage runs
  source calls → per-season frames → season-verified rows → candidate records; no
  step may substitute downstream output as upstream evidence.
- **Fail-closed drift rules (all raise and abort; nothing is written):**
  - any season's source call fails → whole build fails (no five-season candidate);
  - any required column (per the audit's required sets, including `season` at BOTH
    levels per the PR #217 correction) missing for any season → fail;
  - identity join rate below floor (§10) → fail;
  - any week-span, games, grain, or season-match violation (§7–§9) → fail;
  - `load_players()` failure → fail (identity is required, not optional).

  A failed build publishes **no partial candidate** and leaves no artifact, manifest,
  or report claiming success (§13).

## 7. Historical schedule contract

- **Audited rule (2015–2020 only):**

  ```python
  EXPECTED_REG_WEEKS_2015_2020 = set(range(1, 18))  # weeks 1-17, evidence: #218 audit
  ```

- **Per-season verification, never inferred continuity:** the builder verifies that
  *each* season's week-level REG rows expose exactly this set. Six independent checks;
  season N passing never excuses season M.
- **Behavior table (all fail-closed unless noted):**

| condition | behavior |
|---|---|
| missing week (observed ⊂ 1–17) | `SourceFeasibilityError`, name the season and missing weeks; abort build |
| unexpected week (e.g. 18+ or 0) | `SourceFeasibilityError`, name the season and extra weeks; abort build |
| postseason rows | excluded by explicit `season_type == "REG"` filter before any counting; POST rows are never errors by themselves (the source legitimately carries them) but must never contribute to REG evidence |
| wrong-season rows (row's own `season` ≠ requested season) | build context is stricter than audit context: **any** wrong-season row in a season's response aborts the build (`SourceFeasibilityError` naming counts and observed season values). The audit *reported* drift; the builder must not build on drifted responses |
| mixed-season responses | same as wrong-season rows: abort; rows are never silently filtered into a "clean" subset for building |
| non-contiguous span | covered by the missing/unexpected rules (set equality with 1–17 is the only pass) |
| later evidence of a season-specific exception | not an inline override: requires a new source-audit issue amending the evidence lock before any builder constant changes |

- **2021+ isolation:** the 2021+ builders' `EXPECTED_REG_WEEKS = set(range(1, 19))`
  constant is neither modified nor reinterpreted. The historical constant lives only in
  the new builder, under a distinct era-scoped name. Negative test N-2 proves a week-18
  row fails the historical build; guard test G-3 proves the accepted builders'
  files are untouched.

## 8. Coverage-status semantics

- **Existing 2021+ rule (unchanged where it applies):** `full_season: weeks_observed >= 15`
  against an 18-week span; `partial_season: 1 < weeks_observed < threshold`;
  `single_week: == 1`; `unknown: 0`.
- **Historical rule (2015–2020 only):**

  ```python
  FULL_SEASON_MIN_WEEKS_2015_2020 = 14  # of the 17-week span
  ```

- **Why `>= 15` cannot be reused silently:** 15-of-18 and 15-of-17 are different
  claims. Copying the constant would silently tighten `full_season` from "missed at
  most 3 week-numbers" to "missed at most 2" for the older era, misclassifying rows
  relative to the contract's established meaning without any reviewed decision.
- **Why 14 is the contract-honest mapping:** the 2021+ rule's meaning is a tolerance,
  not a percentage: a player may miss up to **3** of the season's week-numbers (one
  team bye plus up to two additional absences) and still be `full_season`. Two
  independent mappings of that meaning to the 16-game/17-week era both yield 14:
  - *absolute tolerance:* 17 − 3 = 14 (same up-to-3-missed-weeks allowance);
  - *cap-relative:* 2021+ threshold = per-player ordinary week ceiling (17 observed
    weeks for a never-absent single-team player... 18 only via trade) minus 2; the
    historical single-team ceiling is 16 (16 games, one bye), minus 2 = 14.

  The mechanical percentage mapping (15/18 ≈ 83.3% of 17 ≈ 14.2) brackets the same
  value. The historical rule therefore preserves the contract's tolerance semantics
  rather than copying the 2021+ constant.
- **Classification:** `full_season: weeks_observed >= 14`; `partial_season: 2–13`;
  `single_week: 1`; `unknown: 0`. Injury-shortened and inactive-week players classify
  purely by observed distinct REG week-numbers with a recorded stat line (family
  convention: production-week observation, not roster membership). Traded players
  count distinct week-numbers across all their teams. **No-appearance players do not
  appear in the candidate at all** — absence of rows is never converted into a row
  (`AGENTS.md` rule 5: missing is unknown, never inferred).
- **Artifact obligations:** the artifact's `methodology.coverage_status_rule` must
  state the historical rule and its rationale explicitly; `coverage_notes` must say
  "of up to 17 REG week numbers", not 18.
- **Negative tests (§14):** guard test G-1 asserts a 14-weeks-observed row is `full_season`
  under the historical rule and would NOT be under a mechanically copied 2021+
  constant; a guard test asserts the builder's constant equals 14 and its week span
  equals `set(range(1, 18))`, so silent reuse of 2021+ calibration cannot pass CI.

## 9. Games and trade semantics

- **Ordinary maxima (all six audited seasons):** 16 team games in 17 weeks, one bye.
  Ordinary per-player maximum `games_played` = **16** (single team).
- **Absolute maximum:** **17**, achievable only by multi-team players whose teams'
  byes fall in different weeks. The audit observed exactly one season (2019) reaching
  17; 2015–2018 and 2020 observed max 16.
- **Overage is never inferred to be a trade.** A row with `games_played > 16` is valid
  **only** when the row's own week-level team context (the same source evidence that
  builds `teams[]`/`team_weeks[]`) shows ≥ 2 distinct teams with disjoint production
  weeks consistent with the games count. That is source-backed trade evidence. Absent
  that evidence, the overage is source drift and the build fails.
- **Fail-closed limits:**

| condition | behavior |
|---|---|
| `games_played > 16` with exactly one team in week-level context | `SourceFeasibilityError` (unexplained overage); abort |
| `games_played > 17` (any context) | `SourceFeasibilityError`; abort |
| `weeks_observed > 17` | impossible under §7's span check; asserted anyway; abort |
| `games_played > weeks_observed + tolerance 0` | reconciliation failure: a player cannot play more games than distinct weeks; flagged and build fails (an NFL player cannot appear twice in one week-number) |
| multi-team rows | valid; must carry `primary_team_rule` (existing validator enforces); `team_weeks` must partition the observed weeks |
| duplicate `(player_id, season, season_type)` grain | `SourceFeasibilityError` (existing family behavior); duplicates are never "resolved" into a merged row |

- **Team-level reconciliation:** no separate team-schedule source is added (that would
  be a new source needing its own audit). Reconciliation uses only the already-approved
  week-level rows: distinct-week counting, per-team week sets, and the caps above.
- **Rejection evidence (build must fail, not accept):** single-team overage; >17 games;
  duplicate grains; games/weeks contradictions. **Acceptance evidence** for >16 games:
  ≥2 teams in the same row's week-level context with week sets consistent with the
  games total (test B-3 vs N-14).

## 10. Identity and nullable metadata

- **Join expectation (corrected per discussion_r3608761214):** the audit observed
  100% `gsis_id` joins for every season, and the §6 accepted-source fingerprint gate
  requires exact agreement with that audited rate. Under the current #218 evidence
  lock the build therefore requires **exactly 1.0**: any season joining below 1.0 —
  including 0.97 — is source drift and aborts **before any output is staged** (test
  N-24). A sub-1.0 rate is never published and deferred to G4. The family constant
  `IDENTITY_JOIN_RATE_FLOOR = 0.95` is retained only as a defense-in-depth lower
  bound for lineage consistency with the accepted 2021 builder (test N-7); it cannot
  bind while the fingerprint gate demands 1.0, and relaxing the 1.0 requirement would
  itself be an evidence-lock change requiring a new source-audit issue and explicit
  operator acceptance. The achieved rate is still recorded in the manifest and build
  report.
- **Identity-join success is separate from optional-field completeness:** a joined row
  with null draft fields is `identity_confidence: source_verified` with those fields
  null and listed in `missing_fields` — optional-field gaps never abort and are never
  fabricated. The schema's `provisional` identity state is **unreachable in this
  build** (corrected per discussion_r3608772421): under the exact-1.0 join gate above,
  an unjoined included row *is* a join rate below 1.0 and aborts before staging
  (N-24). This spec therefore defines **no emission rule for provisional rows**; the
  enum value stays schema-compatible for other windows or a future re-audited
  evidence lock only, and a published 2015–2020 candidate containing any
  `provisional` row is by definition invalid (guard test G-8).
- **No fabrication:** `birth_date`, `season_age`, `rookie_year`, `career_year`,
  `draft_year`, `draft_round`, `draft_pick`, `draft_team` are emitted only from
  `load_players()` values (with `season_age` computed from `birth_date` against the
  existing September-1-of-season reference, and `career_year` only from a non-null
  `rookie_season`). Null in, null out. The existing validator's fabrication checks
  (`season_age` without `birth_date`, `career_year` without `rookie_year`) apply
  unchanged.
- **Duplicate/contradictory identity records:** the accepted 2021 builder's index is
  last-write-wins on duplicate `gsis_id`; this design **tightens** that for the
  historical build: if `load_players()` returns two rows with the same `gsis_id` whose
  identity-relevant fields (`birth_date`, `rookie_season`, draft fields) contradict,
  the build fails closed naming the colliding key count (never player names in
  reports). Exact-duplicate rows (no contradiction) are collapsed silently. This
  tightening lives entirely in the new builder; it does not modify the accepted
  builders (which remain out of scope).

## 11. Schema and validator reuse assessment

- **Reused unchanged:** `schemas/player_season_coverage_v0.schema.json` — the audited
  evidence violates no constraint in it: `season >= 1900`, `weeks_observed >= 0`, no
  week-span constant, nullable identity fields, `status` const
  `candidate_evidence_artifact_not_promoted`, grain string const. 2015–2020 rows fit
  as-is.
- **Reused unchanged:** every semantic in `scripts/validate_player_season_coverage_v0.py`
  — grain uniqueness, REG+POST overlap ban, explicit season_type, multi-team
  `primary_team_rule`, availability-assertion ban, all-source approved-prefix
  allowlist, fixture-marker rejection, zero-vs-null distinctness, fabrication checks.
  None encode a season shape. Validation command, unchanged:

  ```text
  python scripts/validate_player_season_coverage_v0.py data/processed/evidence/player_season_coverage_2015_2020_candidate.source_backed.json
  ```

- **Historical-only wrapper:** no schema or validator change is needed. Era-specific
  rules (week span 1–17, `full_season >= 14`, games caps, trade evidence, identity
  contradiction) are **builder-level fail-closed checks plus test assertions**, exactly
  where the 2021+ era rules already live (builder constants). A thin *additive*
  validation step — the machine-readable validation result at
  `docs/reports/player-season-coverage-v0-2015-2020-candidate-validation.json`,
  produced by running the unchanged validator plus the builder's era-rule
  re-verification against the emitted artifact — records the outcome without wrapping
  or altering the shared validator.
- **No weakening:** no schema loosening, no validator exception, no contract change to
  admit bad rows is proposed or permitted. If implementation discovers a row the
  current schema/validator cannot honestly admit, the correct outcome is a failed build
  and a follow-up evidence issue — never a contract bend.
- **Promoted schema:** `schemas/player_season_coverage_v0_promoted.schema.json` is out
  of scope entirely (promotion is gate G7; this design produces no promoted envelope).

## 12. Builder architecture decision

Options compared:

- **A. New bounded historical builder** (`scripts/build_player_season_coverage_2015_2020_candidate.py`),
  era constants explicit at top-of-file, zero edits to accepted files.
- **B. Shared parameterized core** with thin era entrypoints: best long-term shape,
  but it requires refactoring the accepted 2021/2022–2025 builders into a common
  module — touching accepted, promotion-lineage scripts, which #220 prohibits and
  which carries direct regression risk to reproducibility claims recorded in the
  promotion manifest (its `reproducibility` block cites those exact scripts).
- **C. Modify an existing builder** (e.g. widen `SEASONS` and branch on era):
  prohibited by #220's hard non-goals and by the audit's own finding that
  `EXPECTED_REG_WEEKS` cannot be silently generalized; highest regression and
  false-continuity risk.

**Selected: A.** Rationale: the family precedent is already parallel bounded builders
per window (2021 vs 2022–2025); A adds a third bounded window with its era rules
explicit and reviewable in one file, and leaves the accepted builders byte-identical
(test G-3). The known cost — some duplicated assembly logic — is accepted; a future
consolidation into option B may be *proposed* as a separate refactor issue only after
this candidate reaches a terminal state, and is explicitly not part of this design.

## 13. Deterministic execution contract

- **Inputs:** the six-season constant list `(2015, …, 2020)`, the approved per-season
  source calls (§6), optional `--generated-at <ISO-8601>`.
- **Network boundary:** only `main()` performs network calls. The assembly function
  (`build_candidate_payload(per_season_frames, players_df, generated_at)`) is pure and
  offline-testable with injected fixture frames — same pattern as the accepted audit
  script and builders.
- **All-or-nothing publication:** the full six-season payload is assembled and
  fail-closed-verified **in memory**; only then does publication begin. A failure in
  any season, check, or serialization step publishes nothing ("no partial candidate
  publication after a failed season").
- **Journaled set publication — preflight, stage, commit (PR #221 review,
  discussion_r3608615744 and discussion_r3608751685; G1 correction round):** the five
  outputs (artifact, manifest, validation result, md report, json report) are
  published as a **set**, never individually:
  - *Phase 0 — residue preflight:* before any staging, the builder scans every output
    directory for `.tmp-*` / `.prev-*` files matching any of the five final names.
    If any exist, it aborts immediately with a fatal residue diagnostic — no staging,
    no cleanup, and the leftovers (which may include the only recoverable prior copy
    left by a prior hard kill) are left exactly as found. Recovery from residue is a
    deliberate, audited operator step (inspect, then restore or clear), never an
    automatic action of the next run — so crash leftovers can never be overwritten
    or cleaned away by a rerun's success path.
  - *Phase 1 — stage:* every output is fully written to a temp file
    (`<final>.tmp-<pid>`) in its destination directory; the manifest's sha256 is
    computed from the staged artifact bytes. Any phase-1 failure deletes all temps and
    exits non-zero — the pre-run state (including the *absence* of any output that did
    not exist before the run) remains exactly intact.
  - *Transaction journal:* before phase 2 begins, the builder records in memory, for
    **every** final path: whether it existed before publication; its backup path
    (`<final>.prev-<pid>`) when it existed; and, as phase 2 proceeds, whether the
    staged replacement has been installed at that path.
  - *Phase 2 — commit:* for each path in a fixed order: if a previous final exists it
    is first renamed to its backup, then the staged temp is `os.replace`d into place
    and the journal marks it installed. Backups are deleted only after **all five**
    installations succeed.
  - *Rollback on any phase-2 failure*, in **reverse installation order**:
    1. remove every newly installed final recorded in the journal;
    2. restore the prior backup for every path that existed before the run;
    3. ensure every path that did **not** exist before the run is absent again
       (first-run failures must not leave a partial first set behind);
    4. if rollback itself cannot complete, retain every recoverable backup on disk
       and emit a **fatal torn-state diagnostic** naming the journal state per path;
    5. never delete the only recoverable prior copy of any output after a rollback
       failure — backups are removed only on full success or full rollback.
  - *Atomicity claims, stated accurately:* this contract makes every **caught**
    staging/commit failure restore the exact pre-run state (presence and bytes, or
    absence). It does **not** claim process-crash atomicity across multiple files: an
    external hard kill mid-phase-2 can leave a torn but detectable state (journal not
    consulted, backups still on disk). Manifest/artifact sha256 verification and
    repository working-tree diff inspection are therefore mandatory rejection gates —
    a torn state must be rejected before any commit to git and before any review
    trusts the output set.
- **Cleanup:** on success, all `.tmp-*` and `.prev-*` files removed (test G-6 asserts
  zero residue); on caught failure, temps removed and pre-run state restored per the
  rollback rules; on rollback failure, backups deliberately retained.
- **Exit codes:** `0` = candidate built, validated, all outputs written; `1` = source
  or feasibility failure (nothing written); `2` = post-assembly validation failure
  (artifact withheld, diagnostic report path printed to stderr only). Any non-zero
  exit means "no candidate exists from this run".
- **Report generation:** the build report (md+json) mirrors the 2021 candidate-build
  report conventions: sha256, artifact_id, status, seasons, counts by position and
  season, coverage-status distribution, identity join rate, environment metadata, and
  a reconciliation table against the #218 audited per-season counts (§3). That
  reconciliation is a **gate, not merely informational**: it restates the §6
  accepted-source fingerprint verification that already had to pass before staging —
  a build whose reconciliation table disagrees with #218 cannot exist as a published
  set. Reports contain aggregates only — never player names or IDs beyond counts.

## 14. Positive and negative test matrix

Offline tests (`tests/test_build_player_season_coverage_2015_2020_candidate.py`),
fixture-injected, no network. IDs are normative for the implementation PR.

Positive:

| id | assertion |
|---|---|
| P-1 | six clean fixture seasons (weeks 1–17, games ≤ 16) build; records sorted `(season, player_id)`; counts per season/position correct |
| P-2 | each season assembled from its own per-season frames (per-season isolation observable in source_refs/manifest) |
| P-3 | exact weeks 1–17 accepted for every season independently |
| P-4 | `weeks_observed == 14` → `full_season`; `13` → `partial_season`; `1` → `single_week` |
| P-5 | multi-team fixture with 2 teams, disjoint weeks, `games_played == 17` → accepted, `primary_team_rule` present |
| P-6 | joined identity rows: `source_verified`, null draft fields preserved as null and listed in `missing_fields` |
| P-7 | payload validates against `schemas/player_season_coverage_v0.schema.json` and passes the unchanged validator |
| P-8 | repeat build with pinned `--generated-at` is byte-identical (G-2's positive half) |

Fail-closed negative tests — **every one must abort and publish nothing**
(PR #221 review, discussion_r3608615746: this table now contains *only* abort cases):

| id | scenario | required outcome |
|---|---|---|
| N-1 | one season missing week 5 | abort naming season + missing week |
| N-2 | unexpected week 18 in one season | abort (historical span violated; 2021+ rule not applied) |
| N-4 | wrong-season rows in one season's response | abort naming counts + observed season values |
| N-5 | mixed-season response (correct + wrong rows) | abort — build never filters drifted responses into a usable subset |
| N-6 | duplicate `(player_id, season, season_type)` grain | abort |
| N-7 | identity join rate 0.90 (< 0.95 legacy floor; also fails the exact-1.0 gate, see N-24) | abort |
| N-9 | contradictory duplicate `gsis_id` identity rows | abort naming collision count (no names in output) |
| N-10 | `load_players()` call fails | abort (identity required) |
| N-11 | one season's source call fails | abort entire build — no five-season candidate |
| N-12b | `games_played == 17` with a single team | abort (unexplained overage) |
| N-14 | `games_played > 17` with any team context | abort |
| N-16 | failure during phase-1 staging | nothing published; no `.tmp-*` residue; pre-run state (including absence of never-existing outputs) untouched |
| N-16b | **first run** (no prior outputs), injected failure after **each** of the five replacement points in turn | rollback removes every newly installed final; **every final remains absent**; no `.tmp-*`/`.prev-*` residue |
| N-16c | **rerun** over a prior successful set, injected failure after **each** of the five replacement points in turn | rollback restores **every prior final byte-for-byte**; no residue |
| N-16d | injected failure during rollback itself | every recoverable backup **retained on disk**; fatal torn-state diagnostic emitted naming per-path journal state; the only recoverable prior copy is never deleted |
| N-16e | pre-existing `.tmp-*` or `.prev-*` residue at builder start | abort in phase 0 **before any staging**; residue left byte-for-byte untouched; fatal residue diagnostic |
| N-25 | rebuild after an accepted candidate (G5) where one source row value changed — in either the week-level or the REG-summary frame — but every aggregate fingerprint still matches | the affected frame's per-season source-content hash differs from the accepted manifest; abort before staging with a value-drift diagnostic |
| N-17 | builder path-guard: any output path under `exports/**` | abort before network |
| N-21 | installed nflreadpy version is not exactly `0.1.5` | abort before staging; bounded source-evidence-drift diagnostic; no candidate |
| N-22 | one per-season fingerprint count differs from #218 (e.g. week-level REG row count off by one for 2017) | abort before staging; drift diagnostic names season + expected-vs-observed aggregate |
| N-23 | max-games fingerprint mismatch (e.g. 2018 source now shows 17) | abort before staging; drift diagnostic |
| N-24 | identity-join rate differs from the audited #218 fingerprint | abort before staging; drift diagnostic |

Boundary-acceptance tests — legitimate source conditions the fail-closed rules must
**not** over-reject (each builds successfully with the stated handling):

| id | scenario | required outcome |
|---|---|---|
| B-1 (was N-3) | POST rows present in a season's response | excluded from REG evidence by the season_type filter; REG counts unchanged; POST rows alone never abort the build |
| B-2 (was N-8) | null draft fields for joined players | rows emitted with nulls, listed in `missing_fields`; never zero-filled; unchanged validator passes (fabrication would fail it) |
| B-3 (was N-13) | valid trade overage: 2 teams, disjoint weeks, `games_played == 17` | accepted; `primary_team_rule` present |
| B-4 (was N-12's first half) | ordinary cap: single-team `games_played == 16` | accepted |

Invariant / guard tests — assertions about constants, determinism, and boundaries
(neither abort cases nor build outcomes):

| id | assertion |
|---|---|
| G-1 (was N-1b) | builder constant guard: `FULL_SEASON_MIN_WEEKS_2015_2020 == 14`, `EXPECTED_REG_WEEKS_2015_2020 == set(range(1, 18))`; a 14-week row classified with the 2021+ constant (15) would flip status — proves silent 2021+ reuse cannot pass |
| G-2 (was N-15) | two runs, same pinned timestamp, same fixtures → byte-identical outputs |
| G-3 (was N-18) | accepted builders + audit script blobs unchanged by the implementation PR (git-level assertion in review, mirrored as a test reading file hashes) |
| G-4 (was N-19) | no support-claim widening: candidate artifact/manifest/reports never contain the phrase "2015–2025 is available"; status fields are exactly `candidate_evidence_artifact_not_promoted` |
| G-5 (was N-20) | candidate status never interpreted as promotion: manifest lacks every promoted-envelope required field (`promoted_at`, `promotion_review`, …) and the promoted schema rejects it |
| G-6 | successful run leaves **zero** `.tmp-*` or `.prev-*` residue in every output directory |
| G-7 | the candidate manifest records all thirteen source-content hashes (six per-season week-level + six per-season REG-summary + one identity-fields), and they are deterministic across repeat runs on unchanged fixtures |
| G-8 | every published record has `identity_confidence == source_verified`; the `provisional` path is unreachable — a fixture with one unjoined included player must abort via N-24 and never emit a provisional row |

## 15. Audit, review, and promotion gates

Eight separate gates. **No gate follows automatically from the previous one**; each
requires its own explicit operator decision, and every artifact-bearing PR requires
independent audit because generated data + builder code can be misread as promotion.

| gate | content | authority required |
|---|---|---|
| G1 design acceptance | this document independently reviewed and accepted | operator decision on the design PR |
| G2 implementation activation | builder + tests may be written (no artifact) | new explicit operator comment |
| G3 candidate build | network-backed run emits the candidate surfaces (§5) | operator-authorized run under G2's issue |
| G4 independent audit | audit function verifies candidate vs this spec + #218 evidence | independent reviewer/auditor |
| G5 candidate acceptance | candidate recorded as accepted evidence | operator decision |
| G6 promotion proposal | separate issue proposing promotion (incl. any merge design) | operator-opened issue |
| G7 explicit promotion | promotion review + manifest event (family precedent #192/#202) | operator decision after review |
| G8 downstream Forecast availability | separate TIBER-Forecast issue pinning new artifact identity/sha | Forecast-side gate; nothing here authorizes it |

## 16. Unresolved questions and blockers

None blocking. Non-blocking notes for the implementation reviewer:

1. nflreadpy version drift: resolved by §6's accepted-source fingerprint gate — the
   implementation requires exactly the audited 0.1.5 and exact per-season fingerprint
   agreement with #218; changing either requires a new source-audit issue and explicit
   operator acceptance of a revised evidence lock.
2. The candidate-manifest shape (§5) is new (prior candidates carried metadata
   in-artifact only); it is additive evidence and requires no contract change.
3. The 2019 17-game observation is bound at build time by §9's trade-evidence rule;
   no player-level pre-verification is needed or performed in this design.

## 17. What is now true

- An operator-activated, documentation-only design exists that settles every decision
  #220 requires: file surfaces, source/provenance binding, the isolated 1–17 historical
  week rule, a justified `full_season >= 14` historical threshold, games/trade
  semantics with fail-closed caps, identity and nullability rules, schema/validator
  reuse with zero contract changes, builder architecture (new bounded builder), a
  deterministic execution contract with a journaled publication transaction (exact
  pre-run state restored on every caught failure, first-run absence included), an
  accepted-source fingerprint gate binding generation to the audited nflreadpy 0.1.5
  evidence (structural drift blocked pre-staging; value-level content pinned by
  recorded source-content hashes and accepted only at gates G4/G5), a mechanically
  actionable test matrix, and eight non-automatic gates.
- The design binds exclusively to accepted, pinned evidence (§3) and changes no
  repository behavior.

## 18. What remains missing

- Independent review of this design (G1) and a separate operator implementation
  activation (G2). No builder, tests, candidate rows, manifest, or validation results
  exist. Historical ADP remains a separate unresolved dependency. Promotion, any
  2015–2025 merge, and Forecast availability remain unproposed and unauthorized.

## 19. What must not be assumed

- This document is not an implementation, not a build, not candidate data, and not a
  promise that the build will succeed.
- The promoted player-season window remains **2021–2025 REG only**.
- `full_season` for 2015–2020 means "≥ 14 of 17 audited week-numbers observed" and
  must never be silently exchanged with the 2021+ rule in either direction.
- A games total above 16 is not evidence of a trade; only week-level multi-team
  evidence makes it valid.
- "2015–2025 is available" remains prohibited at every stage described here.
- No Forecast, ADP, rebound-research, ranking, projection, advice, or product action
  is authorized by this document or by any artifact it describes.

## 20. Terminal decision

```text
may_activate_player_season_coverage_2015_2020_candidate_build
```

Basis: every implementation-relevant rule, file surface, and fail-closed test required
by issue #220 is settled above without weakening any existing contract, schema,
validator, builder, or support claim. This decision permits the operator to *consider*
a separate implementation activation (gate G2). It builds nothing, changes no support
window, and authorizes no promotion, Forecast, ADP, or product behavior.
