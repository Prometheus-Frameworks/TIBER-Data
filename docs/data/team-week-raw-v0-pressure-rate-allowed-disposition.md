# Decision: `pressureRateAllowed` disposition for `team_week_raw_v0`

## Status

**Decision spec / ADR — docs only.** For TIBER-Data issue #173.

This document decides the *policy direction* for `pressureRateAllowed`. It does
**not** ingest pressure data, rebuild any artifact, promote anything, change any
contract / schema / code, claim `governed_real_data`, or touch TIBER-Teamstate
or TIBER-Forecast. It chooses the disposition so that a later contract-revision
PR, a rebuild/validation PR, and a promotion review can proceed on an agreed
basis.

**Decision: Option B — formally defer `pressureRateAllowed` for this lane**
(make it optional / non-blocking for governed `team_week_raw_v0`, with pressure
preserved as machine-readable *unknown/unavailable*, never zero). Option A's
real-sourcing work is preserved as a **future additive, non-blocking
enhancement**, not a precondition. See §4 for the decision and §5 for the
rejected alternative.

Follows: issue #171 / PR #172
(`docs/data/team-week-raw-v0-governance-blockers-audit.md`), which found the
2024 candidate *not promotable now* with `pressureRateAllowed` deferred on all
544 rows as the primary blocker.

## 1. Current state

Re-verified against the committed candidate and contract (unchanged since
PR #172):

- `pressureRateAllowed` is a **required field name** in `teamWeekRawRowV0Schema`
  (`src/contracts/v1/teamWeekRawV0.ts`): present and `nullable`, **not**
  `.optional()`. The key must exist on every row; `null` is a schema-valid
  value.
- In the 2024 candidate
  (`exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`)
  it is **explicit `null` on all 544 rows**, recorded in
  `metadata.deferredFields: ["pressureRateAllowed"]` with a reason in
  `deferredFieldReasons`.
- Locked policy (PR C preflight §8,
  `docs/data/team-week-raw-v0-2024-pr-c-preflight.md`): promotion to
  `governed_real_data` is **blocked** while `pressureRateAllowed` is both a
  required field and null-deferred for every row. The block is *not* lifted by
  documenting the deferral, by a plausible path, by build success, or by
  validation passing. Only (1) integrating an accepted pressure source or
  (2) a formal contract revision can lift it.
- PR B probe (`docs/data/team-week-raw-v0-2024-source-probe.md`): **no**
  pressure column exists in the standard nflverse weekly-stats or play-by-play
  paths already used by this repo. No accepted pressure provider is currently
  identified or approved.
- Doctrine constraint (`docs/TIBER_DOCTRINE.md`): "If source truth is missing,
  reduce scope rather than fabricating coverage. A contract-safe artifact is
  allowed to be narrow. It is not allowed to be misleading."

So today the lane is stuck: the field is *required-and-empty*, which blocks a
genuinely useful and otherwise-complete pace/pass/efficiency/scoring source
from ever being governed, while no provider is in hand to fill it.

## 2. Options considered

### Option A — Source pressure properly (keep required, block until sourced)

Keep `pressureRateAllowed` required for governed `team_week_raw_v0`; do not
promote until an accepted pressure-charting/provider source is integrated.

Acceptance bar a future source would have to meet (recorded here so Option A
remains a concrete, non-inferred path even though it is not chosen as the
gate):

- named source/provider and `sourceType`;
- source refs / dataset IDs;
- `retrievalMethod`, `retrievalTimestamp` (UTC, at retrieval);
- package/library `packageVersion`;
- **content checksum or immutable source pin** (per #171 audit §2.4);
- coverage expectations (which team-weeks the provider actually covers);
- validation checks for the new field (bounds, denominator definition,
  null policy for genuinely-missing rows);
- explicit null/deferred policy for any team-weeks the provider does not cover;
- licensing / availability review (most snap-level pressure charting —
  e.g. PFF-style sources — is proprietary and may not be redistributable);
- deterministic rebuild expectation against the pinned bytes.

### Option B — Formally defer pressure for this lane (optional / non-blocking)

Revise the intended contract direction so `pressureRateAllowed` is
optional / non-blocking for `team_week_raw_v0`, while explicitly preserving
pressure as **unknown/unavailable, never zero**:

- Keep the field name (avoid a breaking removal); the future contract revision
  reclassifies it from *required* to *deferred-optional* for governance
  purposes.
- Represent missing pressure through **schema-modeled field-readiness /
  deferred metadata** (promote today's out-of-contract
  `deferredFields`/`deferredFieldReasons` into the validated contract, paired
  with a per-field readiness status such as `deferred` / `insufficient_data` /
  `unavailable`). `null` for `pressureRateAllowed` then carries an explicit
  machine-readable meaning of *unavailable*, distinct from a numeric `0`.
- A governed promotion is then permitted **without** real pressure values,
  provided every *other* gate item from #171 audit §3 still passes and the
  pressure deferral is explicit and machine-readable.

## 3. Required analysis (answered)

- **Is pressure essential for the first governed `team_week_raw_v0`?** No. The
  lane's purpose is team-state context — pace, EPA, success rate, explosive
  rate, drives, red zone, scoring. Teamstate movement v1 drops fantasy splits
  and forecast-features v1 forbids them; the *core* team-environment signal does
  not depend on `pressureRateAllowed`. Pressure is valuable-but-secondary, not
  foundational.
- **Would blocking on a provider delay the useful lane too much?** Yes —
  potentially indefinitely. No accepted provider is identified, and snap-level
  pressure charting is commonly proprietary/licensing-constrained. Option A
  ties an otherwise-complete, fully-covered, validation-passing source to an
  acquisition with no committed timeline.
- **Is a pressure-free governed source still honest if pressure is explicitly
  deferred and machine-readable?** Yes. This is exactly the doctrine's "narrow
  but not misleading." Honesty depends on the *absence being explicit and
  machine-readable*, not on the field being present-and-empty.
- **Downstream risk if pressure is optional/non-blocking?** The main risk is a
  consumer treating missing/null pressure as `0`. This is mitigated by making
  unavailability schema-modeled (readiness status + deferred metadata) and by a
  downstream contract obligation to surface pressure as `insufficient_data`,
  never zero (§6). Without that machine-readable signal the risk would be real;
  with it, the risk is controlled.
- **Downstream risk if we wait for pressure sourcing?** The governed Teamstate
  environment and Forecast Run 2 stall on a non-core field. Worse, sustained
  pressure-to-ship against a required-but-unavailable field is exactly the
  condition that later tempts a null-to-zero laundering shortcut — the outcome
  the guardrails most want to prevent. Deferring honestly now *reduces* that
  future temptation.
- **Which option better supports Teamstate and Forecast Run 2 while preserving
  provenance and no-leakage?** Option B. It lets a genuinely governed
  pace/efficiency/scoring source exist now with pressure explicitly marked
  unavailable. Forecast Run 2 simply treats pressure as a missing feature (omit
  it or mark it explicitly absent) — which introduces no fabricated feature and
  therefore does not affect the 2024-predictor / 2025-target no-leakage
  boundary.

## 4. Decision

**Adopt Option B: formally defer `pressureRateAllowed` for the
`team_week_raw_v0` lane.**

- The intended contract direction is that `pressureRateAllowed` becomes
  **optional / non-blocking for governance** for this lane, represented via
  schema-modeled field-readiness/deferred metadata, with `null` meaning
  *unknown/unavailable* and **never** zero.
- A future governed `team_week_raw_v0` may be promoted **without** real
  pressure values, provided the pressure deferral is explicit and
  machine-readable and every other gate item from #171 audit §3 is satisfied
  (governance marker, contract that can express it, pinned source bytes,
  validation, coverage, deterministic rebuild, etc.).
- This is **not** a hybrid that re-introduces a block. Option A's real-sourcing
  work is preserved as a **welcome future additive enhancement**: if/when an
  accepted pressure source is integrated (meeting the §2 Option-A bar), the
  field's readiness flips from `deferred` to `available` additively, without a
  breaking change and without ever having gated the lane.

Rationale, in one line: the doctrine says reduce scope rather than fabricate,
and a narrow-but-honest governed source unblocks the real downstream work while
removing the future incentive to launder a null into a zero.

## 5. Rejected alternative

**Option A is rejected as the gate** (not as a future enhancement). Keeping
`pressureRateAllowed` required would hold a complete, fully-covered,
validation-passing 2024 source hostage to a provider that is not identified and
may be unlicensable, with no timeline — delaying governed Teamstate environment
and Forecast Run 2 for a non-core field, and increasing the long-run risk of a
zero-fill shortcut under delivery pressure. Its sourcing work remains valuable
and is retained as the additive path in §4, just not as a precondition.

## 6. Downstream implications

These describe obligations a *future* implementation must honor. **No
downstream repo is changed by this PR.**

### Teamstate

- Must read the field-readiness/deferred metadata and treat
  `pressureRateAllowed` as `insufficient_data` / unavailable — **never** zero,
  never backfilled, never estimated.
- Movement v1 and forecast-features v1 already do not depend on pressure, so the
  core lane is unaffected.
- A read-only adapter must preserve and surface the deferral/readiness status
  rather than dropping or re-labeling it.

### Forecast (Run 2)

- Pressure is an **unavailable feature**: omit it from the Run 2 feature set or
  represent it as explicitly missing. Do not synthesize, impute, or zero it.
- Because no feature is fabricated, the deferral does not affect no-leakage
  checks (the 2024-predictor / 2025-target boundary is unchanged); Run 2
  proceeds on the available pace / efficiency / scoring features.

## 7. Next safe PR sequence

1. **(this PR)** Decision spec — adopt Option B. No contract/data change.
2. **Contract-revision PR** (separate, explicitly authorized): make
   `pressureRateAllowed` optional / non-blocking for governance for this lane
   and add schema-modeled field-readiness/deferred metadata
   (`deferredFields` / `deferredFieldReasons` + per-field readiness status).
   Backward-compatible / additive; version the change explicitly. May also fold
   in the #171 audit §2.3 governance-marker fields and §2.4 pinned-source
   identifier, or those may be their own PRs.
3. **Rebuild + validation PR** (separate): regenerate the candidate under the
   revised contract; validation asserts `pressureRateAllowed` is null with
   readiness = `deferred`/`unavailable`, plus pinned source bytes and the full
   §10 emission checks.
4. **Promotion review PR** (separate, PR D-style): set the explicit governance
   marker and satisfy the full promotion gate from #171 audit §3.
5. **Future, optional** (Option A path): if an accepted pressure source appears,
   add it additively (meeting the §2 bar) and flip pressure readiness to
   `available` — never a blocker.

Each step is its own PR with its own review. Nothing here promotes, and this
decision must not be folded into the contract-revision or promotion PRs.

## 8. Explicit non-goals

- No pressure data ingestion.
- No artifact rebuild.
- No artifact promotion.
- No contract / code / schema change in this PR.
- No `governed_real_data` claim.
- No null-to-zero laundering; no pressure backfill or zero-fill.
- No Teamstate or Forecast / TIBER-Forecast changes.
- No model training or evaluation.
- No fantasy advice / product / ranking output.
- No path/name/downstream-use governance inference.

## 9. Verification

Run from the TIBER-Data repo root (session already has
`nflreadpy==0.1.5`, `polars`, `pytest`, `jsonschema`, `fastapi`, `httpx`, and
`npm install` deps):

- `npm run typecheck`
- `python3 -m pytest -q` (full Python suite)
- `npx vitest run` (full TS suite)

Results are reported in the PR description. This decision adds only this
Markdown file; it changes no code, schema, artifact, or downstream repository.
