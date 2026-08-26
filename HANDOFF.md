# TIBER-Data — Working Handoff

## Repo purpose in one sentence

TIBER-Data stores canonical contracts and deterministic football data artifacts for downstream repos.

## Current agent workflow

Typical loop:
1. Lamar defines scope and boundary
2. Codex implements the narrow change
3. Claude audits when needed
4. merge only if the repo remains honest

## When a task arrives

Ask:
1. Is this a contract task, a data artifact task, or a repo-governance task?
2. Does this repo already hold the source truth needed?
3. If not, should scope be reduced or should the task move elsewhere?

## If a mistake or uncertainty appears

First call:
- README
- contracts
- export code
- tests
- committed raw support files

If still unclear:
- Lamar decides whether the task is honest
- Claude audits if a builder may have overreached

## Handoff note format

Every material handoff should state:
- active task
- files touched
- audit-trigger status: not triggered, Claude audit happened, Claude audit pending, or Claude audit skipped with reason
- what is now true
- what is still missing
- what must not be assumed

Example:
- Active task: extend supported weekly artifact generation
- Files touched: raw support fixtures, export validation, tests, README
- Now true: W1–W6 supported and fail-closed
- Missing: honest raw support beyond W6
- Must not assume: W7+ exists unless committed support is present

## Current handoff — #236 historical landing-context design/evidence pilots

- Active task: design the minimum cutoff-aware historical landing-context
  candidate interface and reproduce bounded April 2023 evidence/gaps for BAL,
  IND, and LAR, stacked on the #237 identity candidate.
- Files touched: a candidate-only source-assertion fixture and draft schema,
  deterministic builder/validator, focused tests, three pilot artifacts and
  bundle manifest/validation, a source availability report, interface/handoff
  documentation, and this handoff. No governed schema or promoted path changed.
- Audit-trigger status: independent final artifact audit completed before draft
  PR handoff. Three read-only reviews established source gaps, temporal/team
  boundaries, frozen-pilot discrepancies, and the minimum validator surface,
  then verified strict commit/blob/hash replay, source-row fidelity, resolved
  missingness paths, cutoff semantics, typed available/unavailable branches,
  and fail-closed ownership/terminal boundaries. The final focused suite passed
  26/26 and the full repository suite passed 565 with 1 skipped.
- What is now true: all three pilots bind by exact GSIS through #237 version and
  hash; draft assignments are projected without names or later history; 2022
  single-team player-season rows are reproducible but stay unadmitted because
  source availability by cutoff is unproven; multi-team rows are excluded from
  diagnostic subtotals; raw 2022 Rams `LA` stays blocked rather than silently
  normalized; complete team/vacated values and roster, transaction, QB,
  coaching, offense, and injury families remain explicit nulls; interpretations
  are structurally empty.
- What is still missing: operator ownership decisions, immutable cutoff-safe
  roster/transaction/coaching/injury sources, team-split multi-team usage, a
  supported 2022 Rams alias if desired, exact pick-time policy, a durable
  GSIS-to-governed-TIBER-ID edge, operator acceptance, and any later promotion
  proposal.
- What must not be assumed: candidate presence is not interface readiness;
  prior-season usage is not returning roster/depth truth; partial subtotals are
  not team totals; null vacancy is not zero; the EOD cutoffs are proxies; frozen
  Rookies references are not Data fact authority; no ownership or terminal
  decision was made; no model, Forecast, promotion, or Rookies mutation is
  authorized.

## Current handoff — #237 2023 rookie identity crosswalk candidate

- Active task: TIBER-Data #237 builds a versioned, candidate-only 80-player
  2023 QB/RB/WR/TE identity census across pinned Rookies GSIS/slug assertions,
  exact-GSIS TIBER-Data source-player identities, the explicit unresolved
  governed TIBER canonical namespace, and fail-closed Forecast row
  conflicts.
- Files touched: a pinned source-assertion snapshot, deterministic builder and
  validator, focused tests, candidate crosswalk/conflict/manifest/validation
  artifacts, the identity contract, paired audit reports, and this handoff.
- Audit-trigger status: independent final artifact audit completed before draft
  PR handoff. Read-only reviews informed the source pins, conflict scope, and
  alias boundary, then verified the TIBER namespace split, explicit override
  lineage, bounded impact inventory, source-scoped team policy, and exact
  Forecast-row fingerprint binding. The final re-audit found no blocker.
- What is now true: all 80 census rows are represented; exact GSIS resolves 76
  promoted Data source-player IDs (68 in 2023 REG, eight first observed later),
  while four stay explicit nulls; the distinct governed `tiber_player_id`
  namespace stays null and blocked for all 80 because V1 has no admissible GSIS
  edge; all eight audited Forecast 2023-subject rows use explicit non-name
  fingerprint overrides marked `needs_operator_review` and stay conflict-blocked;
  five raw-ID collisions are separately ledgered; Puka's
  Forecast `00-0038543` claim remains distinct from governed `00-0039075`;
  `LAR` is canonical with a directed source/date-scoped `LA→LAR` rule; and
  downstream consumers must verify crosswalk version `0.1.0` plus SHA-256.
- What is still missing: an operator-owned durable GSIS-to-`tiber_player_id`
  edge, operator review of Forecast subject overrides, any promotion/governance
  decision, and the operator's disposition for already-emitted Forecast artifacts.
- What must not be assumed: structural validation does not resolve or admit a
  Forecast edge; the bounded #236 pilot may use only the manifest-bound
  GSIS-to-Data-source-player edge; proposed Rookies slugs are not promoted IDs;
  neither the four missing Data records nor V1 descriptors permit minted or
  name-joined TIBER IDs; no Forecast, Rookies, governed
  schema, or promoted export was mutated; and no rerun, correction,
  supersession, or promotion is authorized.

## Current handoff — NFL Draft results v1 contract foundation

- Active task: implement issue #112 by adding the first-pass canonical NFL Draft results contract, one-year fixture validation path, and documented promoted export boundary.
- Files touched: `src/contracts/v1/nflDraftResults.ts`, `src/contracts/v1/index.ts`, `test/fixtures/nfl_draft_results_2026.contract_fixture.json`, `test/nflDraftResults.v1.test.ts`, `docs/data/nfl-draft-results-v1.md`, `README.md`, `HANDOFF.md`.
- Audit-trigger status: Claude audit pending/required by repo policy because this change adds a contract under `src/contracts/v1/` and documents promoted export semantics.
- What is now true: the v1 row contract validates required draft result fields, positive pick integers, ISO timestamps, nullable source URLs, and explicit unresolved-player-ID provenance states; the future promoted path is documented as `exports/promoted/nfl_draft_results/nfl_draft_results_{year}.json`.
- What is still missing: repo-held official NFL Draft result source files with clear provenance and any promoted official draft result artifacts.
- What must not be assumed: the fixture row is not an official draft fact, no year has full draft coverage, TIBER-Data does not own TIBER-Rookies scoring or prospect interpretation, and FORGE does not consume raw draft facts from this PR.

## Current handoff — #181 governed Teamstate coverage audit for Forecast gate

- Active task: audit/verify complete governed 2024 Teamstate source coverage for the Forecast Run 2 coverage gate (TIBER-Data #181). Upstream coverage only; no Forecast change, no Run 2 rerun, no FORGE, no product output.
- Files touched: `docs/data/team-week-raw-v0-2024-teamstate-coverage-audit.md`, `scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py`, `tests/test_audit_team_week_raw_v0_2024_teamstate_coverage.py`, `exports/candidates/team_week_raw/team_week_raw_v0_2024_teamstate_coverage_audit.json`, `HANDOFF.md`.
- Audit-trigger status: this change *is* a Claude audit (read-only verification + durable report); no artifact rows were produced or mutated.
- What is now true: TIBER-Data already holds a complete governed 2024 `team_week_raw_v0` source — 32/32 teams, 544/544 played team-game rows, explicit governance marker, source/validation/lineage provenance, deterministic ordering, honest deferred (`pressureRateAllowed`) and absent (fantasy split) nulls with no zero-fill. A dependency-free audit + tests re-prove this from the committed artifact.
- What is still missing: nothing on the TIBER-Data side. The Forecast 3-team failure is a downstream handoff gap — TIBER-Teamstate must emit its Forecast-facing artifact from this governed 544-row source (full mode, not `--excerpt`/scaffold).
- What must not be assumed: this does not claim Teamstate or Forecast "works"; it does not run Forecast; it does not source pressure or fantasy splits; deferred/absent fields stay null and must never be zero-filled downstream.

### Current handoff — #220 2015–2020 candidate-build design accepted; implementation inactive

- Active task: TIBER-Data #220 completed the documentation-only design frontier for a bounded 2015–2020 REG `player_season_coverage_v0` candidate. The accepted design is `docs/design/player-season-coverage-v0-2015-2020-candidate-build-spec.md`, accepted at PR #221 head `17d50febffbf087e7faec31157bc406a561a5fd4`, design blob `27aae171cb7b4138b272af32e42e06bb147900b2`. This is a design result only; candidate implementation remains inactive.
- Files touched: the accepted design document and this `HANDOFF.md` state synchronization. No builder, test, source, schema, validator, data, export, manifest, report, README, promoted artifact, Forecast file, or other repository file changed.
- Audit-trigger status: independent design review completed through five hardening rounds. Findings addressed included multi-file publication and rollback semantics, test-matrix consistency, first-run absence restoration, structural source-fingerprint binding, value-level hashing across both source frames and identity inputs, residue preflight, exact 1.0 identity joins, and removal of the publishable provisional-identity path.
- What is now true: an implementation-ready specification exists for a new bounded historical builder producing exactly 2015–2020 REG candidate rows. It requires nflreadpy `0.1.5`, exact agreement with the accepted #218 structural fingerprint, thirteen deterministic source-content hashes, exact 1.0 identity joins, no provisional published identities, weeks 1–17 independently for every season, `full_season` at 14 or more observed week numbers, games above 16 only through source-backed multi-team evidence and never above 17, unchanged schema and validator reuse, phase-0 residue preflight, journaled set publication, deterministic output, fail-closed drift handling, and the normative test matrix. Its terminal decision is `may_activate_player_season_coverage_2015_2020_candidate_build`.
- What is still missing: a separate explicit G2 operator decision activating implementation. No historical builder, tests, candidate rows, manifest, validation result, or build reports exist. Candidate execution, independent artifact audit, candidate acceptance, promotion proposal, promotion, and Forecast availability each remain separate gates.
- What must not be assumed: G1 acceptance is not implementation authority and does not mean a candidate exists. The promoted player-season window remains 2021–2025 REG only. “2015–2025 is available” remains prohibited. No promotion, Forecast, ADP, rebound research, rankings, projections, advice, or product behavior is authorized.

### Current handoff — #222 G2 candidate-builder implementation accepted; G3 run inactive

- Active task: TIBER-Data #222 completed the implementation-only G2 frontier for the bounded 2015–2020 REG `player_season_coverage_v0` candidate builder. The implementation was accepted at PR #223 head `dff6597ee3bcd9f0255e34c1ad02534c26ea9402`; builder blob `0c7fe1bb5885c75a09d7d461bbb7ce480b1fe3e9`; offline-test blob `9a10deac2f32266a1c73f465b5a5fa0ba115422f`. G3 network-backed candidate execution remains inactive.
- Files touched: the bounded historical builder, its offline test module, and this `HANDOFF.md` state synchronization. No candidate artifact, manifest, validation result, build report, data file, export, schema, validator, accepted audit script, accepted design document, 2021/2022–2025 builder, promotion manifest, README support claim, Forecast file, or other repository file changed.
- Audit-trigger status: independent review completed through three Codex rounds. Six findings were corrected before acceptance: mandatory post-G5 hash locking, partial-temp tracking, backup-cleanup handling, successful-publication exit semantics, damaged-manifest fail-closed behavior, and complete phase-one cleanup accounting. Final Codex review was clean at the accepted implementation head; all six review threads are resolved.
- What is now true: an independently reviewed offline implementation exists for the bounded 2015–2020 candidate build. It encodes the accepted source fingerprint, thirteen source-content hashes, historical 1–17 week rules, the 14-week full-season threshold, source-backed 17-game handling, exact 1.0 identity joins, unchanged schema/validator reuse, deterministic serialization, residue preflight, journaled set publication, rollback/recovery semantics, promoted-path guards, support-claim guards, and the normative test matrix. Focused tests passed 51/51 and the full repository suite passed 471 with 1 skipped.
- What is still missing: G3 operator authorization for the network-backed candidate run. No live nflreadpy candidate-generation calls have occurred and no candidate rows, artifact, manifest, validation result, or build report exist. Candidate execution, independent artifact audit, candidate acceptance, promotion proposal, promotion, and Forecast availability remain separate gates.
- What must not be assumed: accepted implementation is not candidate evidence, promotion, or consumer availability. The promoted player-season window remains 2021–2025 REG only. “2015–2025 is available” remains prohibited. No Forecast, ADP, rebound research, rankings, projections, advice, or product behavior is authorized.

### Current handoff — #227 bounded 2026 population census v0 candidate

- Active task: implement TIBER-Data #227 as a deterministic, row-preserving candidate census over exactly two governed cohorts: all 610 season-2025 rows from promoted `player_season_coverage_v0` and all 48 rows from TIBER-Rookies' promoted 2026 rookie-transition profile v0.2.
- Files touched: `schemas/bounded_2026_population_census_v0.schema.json`, `scripts/build_bounded_2026_population_census_v0.py`, `scripts/validate_bounded_2026_population_census_v0.py`, `tests/test_bounded_2026_population_census_v0.py`, `exports/candidates/population_census/bounded_2026_population_census_v0.json`, its validation report, `docs/contracts/bounded-2026-population-census-v0.md`, `docs/reports/bounded-2026-population-census-v0-coverage.md`, and this handoff.
- Audit-trigger status: independent audit pending/required because the change adds a contract, cross-repository source provenance, deterministic builder/validator behavior, and a generated candidate artifact.
- What is now true: the candidate contains exactly 658 rows with stable unique `population_row_id` values, source-row hashes, exact repository/commit/path/content pins, explicit team/position/history/identity states, losslessly associated per-field/per-source-ref cutoff evidence, and itemized reconciliation. It reconstructs byte-identically from the immutable source git blobs. No fuzzy or display-name join is used; all 48 rookie source IDs remain canonically unresolved, so cross-source canonical collision evaluation is explicitly unevaluable rather than reported as zero.
- What is still missing: independent artifact/contract audit, operator acceptance/merge, and any separately governed downstream cutoff/admission decision.
- What must not be assumed: this is not a full active-player universe, complete rookie class, IDP census, current roster, promoted artifact, Forecast authorization, ranking, advice, or production activation. The 610 historical teams are 2025 source context only. TIBER-Data #227 does not authorize the parked 2026 Forecast candidate run.

### Current handoff — #228 generic PPR scoring reconciliation evidence

- Active task: reconcile the exact generic full-PPR profile approved in TIBER-Data #228 against every 2021–2025 REG QB/RB/WR/TE row in the promoted `player_season_coverage_v0` artifact, without changing the promoted source or authorizing downstream use.
- Files touched: the versioned reconciliation declaration under `docs/contracts/`, the dependency-free reconciliation builder and tests, candidate per-row/discrepancy/missingness evidence under `exports/candidates/scoring_reconciliation/`, the evidence manifest, the human report, and this handoff.
- Audit-trigger status: independent audit pending/required before merge because the change adds a contract, generated candidate evidence, source/provenance semantics, and a downstream handoff claim. Builder self-review and deterministic tests are complete; they are not represented as independent audit.
- What is now true: the exact promoted source bytes are pinned at `d45f612b207085df00b4b080e4f55ce1abbd060dcbf30b0bee777ff833ddd8ac`; all 3,016 rows have the eight approved profile components and a source total; every row has an explicit full/partial/single-week/missing/irreconcilable completeness state and reconciliation status; after independent cent-scale `ROUND_HALF_UP` normalization, 2,186 source totals match exactly while 830 are preserved mismatches; raw serialization residue is diagnostic only and the v1 nonzero tolerance is 0.00; component-derived generic PPR is complete candidate evidence; source `season_ppr` is not profile-equivalent across the population. The terminal decision is `scoring_reconciliation_evidence_ready`.
- What is still missing: independent artifact/contract review, operator acceptance, and a separate Forecast-side admission decision. The promoted source did not pin the exact historical nflreadpy/nflverse release; a commit-pinned current official producer formula is used only as semantic corroboration.
- What must not be assumed: no promoted byte or source total changed; no mismatch component was inferred; no weekly rows were reconstructed; no scoring-policy disposition, Forecast cutoff/model/run, #170 execution, promotion, deployment, ranking, advice, or league-specific scoring is authorized.

### Current handoff — #234 Slice B rb_contact_evasion_observations_v0 candidate bundle gate

- Active task: implement TIBER-Data #234 Slice B — a deterministic, offline, fail-closed manifest/digest validation gate for future `rb_contact_evasion_observations_v0` candidate bundles, delegating all semantic judgment to Slice A's canonical compiled evaluator; then repair the independent Codex review's three findings against PR #260 head `4f9591af3ebbcabea965b689e7b95ab8b821d4c1`.
- Files touched: `scripts/validate_rb_contact_evasion_bundle.py` (gate), `scripts/rb_contact_evasion_contract_bridge.mjs` (thin execution bridge), `scripts/rb_contact_evasion_evaluator.tsconfig.json` (build surface), `schemas/rb_contact_evasion_observations_bundle_manifest_v0.schema.json` (manifest shape gate), `tests/test_rb_contact_evasion_bundle_gate.py` (boundary + mutation controls), `docs/contracts/rb-contact-evasion-observations-v0-bundle-gate.md`, `test/fixtures/rb_contact_evasion/bundle/` (reference bundle: manifest + two synthetic artifact copies), `package.json` (`check:rb-contact-evasion-bundle`), the paired review-repair audit under `docs/audits/rb-contact-evasion-observations-v0-bundle-gate-review-repair-2026-08-25.{md,json}`, and this handoff. No Slice A contract, schema, dictionary, reason codes, or fixtures changed; nothing under `exports/**` changed.
- Audit-trigger status: **triggered** (adds a schema under `schemas/` and a validation surface deciding what a future governed artifact may claim). An independent Codex review at head `4f9591af…` produced three findings (two P1 governance, one P2 read-race); those are recorded and repaired in the paired `docs/audits/` record. **Final exact-head audit remains pending fresh Codex review of the repaired head** — this work is not independently reviewed at the repaired head and is not declared so.
- What is now true: the gate is descriptor-bound and fail-closed. It validates the manifest and pinned contract identity before trusting payload claims; pins the artifact id, schema version, and admitted digest algorithm in code (cross-checked against a contract compiled from reviewed source, never from `dist/`); enforces safe relative paths, bundle containment, exact manifest↔bundle bijection, and rejects absolute/traversal/symlink/non-regular paths. Every bundle file is now read through one `O_NOFOLLOW` descriptor whose type and size are validated by `fstat` on that descriptor and read with a bounded read from it, so an oversized replacement, FIFO, device, symlink, or growth after the check fails closed without a stat-then-reopen race and without unbounded reads. Byte size and SHA-256 are checked before JSON parse; malformed JSON with a matching digest is rejected; the committed JSON Schema shape gate is applied; semantic judgment is delegated to Slice A's canonical evaluator with its exact reason codes preserved verbatim; the semantic stage receives the exact verified in-memory bytes and never reopens the pathname. The gate performs no network access and mutates no validated input. P1–P9 remain accepted and N1–N49 remain rejected for their exact existing reason codes through the boundary.
- What is still missing: fresh Codex exact-head review of the repaired head; operator acceptance/merge; and the admitted-source registry, which stays unimplemented because no source is admitted (there is nothing to pin against, and a registry would invent provenance). The `#224` promotion gate is not this gate.
- What must not be assumed: this is not an admitted source, a candidate artifact, a promoted artifact, or a promotion decision; the reference bundle is a synthetic gate fixture, not football evidence; passing the gate proves bytes and file identity, not football truth; `node_modules`, the pinned TypeScript compiler binary, and Node remain trusted and out of scope; and the committed review-repair record is not an independent audit of the repaired head.

### Handoff amendment — #234 Slice B second review round (2026-08-26)

- Active task: repair the two findings from the follow-up independent Codex review of PR #260 at head `96c332149e6411c51ecd6839afbe922a5a1ca499`.
- Files touched: `scripts/validate_rb_contact_evasion_bundle.py`, `tests/test_rb_contact_evasion_bundle_gate.py`, `docs/contracts/rb-contact-evasion-observations-v0-bundle-gate.md`, and the paired `docs/audits/rb-contact-evasion-observations-v0-bundle-gate-review-repair-2026-08-25.{md,json}` (amended with a second-round section), plus this handoff. No Slice A change; nothing under `exports/**`; reference bundle byte-identical.
- Audit-trigger status: **triggered**; final exact-head audit **pending fresh Codex review of the repaired head**.
- What is now true (correcting the prior entry): the descriptor-bound read has **no degraded fallback** — if the platform lacks the primitives required to prove no-follow, component-relative access (`O_NOFOLLOW`, `O_PATH`, `O_NONBLOCK`, `dir_fd`), the gate fails closed with `BUNDLE_DESCRIPTOR_UNSUPPORTED` before reading any bundle bytes; it never opens a full path (the earlier "per-component symlink safety is still enforced by `check_path_safety` upstream" claim was wrong, because manifest reading precedes path safety and a path-check-then-open is itself raceable). The bounded read reads at most the cap plus one byte **in total** into **one** growing buffer returned directly to the caller — peak payload ownership is a single buffer plus one small read chunk (measured ~1.25× the payload), not the ~2× of the previous chunk-list-then-join. Post-`fstat` growth and short reads are still detected.
- What is still missing: fresh Codex exact-head review of the repaired head; operator acceptance; the still-unimplemented admitted-source registry (no source admitted).
- What must not be assumed: passing the gate proves bytes and file identity, not football truth; the platform-capability guard is a hard fail-closed, not a portability shim; the toolchain remains trusted and out of scope.

### Handoff amendment — #234 Slice B third review round (2026-08-26)

- Active task: repair four findings from a Codex exact-head review of PR #260 at head `8d2b9cad0488d649657b43d6b1339a6c92bcc0c7` (two P1, two P2). This review was performed in the operator session and relayed by the operator; there is no GitHub connector review object or thread for it (the connector is not its author).
- Files touched: `scripts/validate_rb_contact_evasion_bundle.py`, `tests/test_rb_contact_evasion_bundle_gate.py`, `docs/contracts/rb-contact-evasion-observations-v0-bundle-gate.md`, and the paired `docs/audits/rb-contact-evasion-observations-v0-bundle-gate-review-repair-2026-08-25.{md,json}` (second-round identity corrected, third-round section added), plus this handoff. No Slice A change; nothing under `exports/**`; reference bundle byte-identical.
- Audit-trigger status: **triggered**; final exact-head audit **pending fresh Codex review of the repaired head**.
- What is now true (correcting the prior entry): once the digest matches, `check_integrity` **freezes** the verified bytes into an immutable `bytes` object and both `verified_bytes` and `raw_bytes` reference that single immutable object, so no later stage can flip a byte in place and change what the evaluator judges — the prior code aliased a mutable `bytearray`, and a reproduced JSON-equivalent whitespace swap between integrity and the semantic stage had let the evaluator receive bytes whose SHA-256 no longer matched the manifest digest. The memory claim is corrected: the bounded reader still owns a single buffer and makes no whole-payload copy (that property is **scoped to the reader**, not the whole lifecycle); the freeze is a deliberate one-time per-artifact copy that is now disclosed rather than hidden behind a single-buffer claim. The capability matrix now proves **zero** `os.open`/`os.read` after the preflight fails by instrumenting the real boundary (the prior test only checked the result text, with a vacuous `secret[:0]` term). The second-round audit's reviewer identity is corrected (operator-relayed Codex review, no GitHub connector object). Stale `pathname stat` / `no whole-payload copy` wording is reconciled across the gate, contract doc, and audit; the evidence cutoff includes 2026-08-26.
- Focused test count: `pytest --collect-only` = **288** node IDs at the repaired head = 284 at `8d2b9ca` (collect-only) + 4 new (1 open/read control + 3 P1 identity regressions). Lineage via collect-only in isolated worktrees: 248 → 263 (+15) → 284 (+21) → 288 (+4). (Corrected in the fourth round: this line originally read "262 → 284 (+22) → 288 (+4)" — the first repair round had undercounted its 15 additions as 14, and the third round compounded the error by trusting the recorded 262 instead of re-counting the base; the second round's "+21" was correct.) Full Python suite 1009 passed / 3 skipped (1005 at the prior head + the 4 new focused tests). Mutation testing: 4 mutations against the real gate, all killed, no degenerate, gate restored byte-for-byte.
- What is still missing: fresh Codex exact-head review of the repaired head; operator acceptance; the still-unimplemented admitted-source registry (no source admitted).
- What must not be assumed: passing the gate proves bytes and file identity, not football truth; the reader is still single-buffer (the round-2 chunk-list/join double representation is gone from the reader), while the integrity freeze deliberately and transiently owns the `bytearray` and its immutable `bytes` copy together — a disclosed, momentary, per-artifact double-payload peak at the freeze, not an undisclosed structural one in the reader; the toolchain remains trusted and out of scope.

### Handoff amendment — #234 Slice B fourth review round (2026-08-26, evidence reconciliation only)

- Active task: correct one P2 evidence-reconciliation finding from a Codex exact-head review of PR #260 at head `8c484931255ea5edb4de7923a30b2d8434b8ebfa`, which **accepted the functional repairs** (mutable-alias freeze, capability no-access instrumentation, corrected reviewer provenance). Operator-relayed, no GitHub connector review object or thread. Comments and governance text only — no gate behavior changed, so no mutation evidence is claimed for this round.
- Files touched: `scripts/validate_rb_contact_evasion_bundle.py` (two stale comments/docstrings), `tests/test_rb_contact_evasion_bundle_gate.py` (module docstring), the paired `docs/audits/rb-contact-evasion-observations-v0-bundle-gate-review-repair-2026-08-25.{md,json}` (lineage corrections + fourth-round section), and this handoff. No Slice A change; nothing under `exports/**`; reference bundle byte-identical.
- Audit-trigger status: **triggered**; final exact-head audit **pending fresh Codex review of the repaired head**.
- What is now true (correcting the prior entries): the focused-test lineage, established by `pytest --collect-only` in isolated worktrees at each historical head, is **248 → 263 (+15) → 284 (+21: 15 parametrized matrix cases + 6 standalone) → 288 (+4)**. The first repair round undercounted its 15 additions as 14 (recording 262 instead of 263); the third round compounded the error by trusting the recorded 262 and deriving "+22" instead of re-counting the base; the second round's "+21" was correct all along. The gate's module comment and `check_integrity` docstring no longer say the read "buffers no more than cap plus one byte" — it reads at most cap + 1 bytes **in total**, with peak reader ownership of one growing buffer plus one bounded read chunk and allocation headroom. The test module docstring no longer says semantic judgment is delegated to a compiled contract under `dist/` — the gate compiles reviewed source into its private temporary build and never trusts ambient `dist/`. The Markdown audit's top-level evidence cutoff is corrected to 2026-08-26.
- What is still missing: fresh Codex exact-head review of the repaired head; operator acceptance; the still-unimplemented admitted-source registry (no source admitted).
- What must not be assumed: a recorded count is not evidence — re-measure at the head in question; the reader is single-buffer while the integrity freeze transiently owns two payload-sized representations, disclosed; the toolchain remains trusted and out of scope.

### Handoff amendment — #234 Slice B fifth review round (2026-08-26, `--json-out` output-publication safety)

- Active task: repair one P2 finding from an **independent GitHub Codex review** of PR #260 at head `e68fc176304699ed5ed815f22836f6b9bb56aea6` (thread `r3864788150`, authored by `chatgpt-codex-connector` — the first genuine connector thread since the first round).
- Files touched: `scripts/validate_rb_contact_evasion_bundle.py` (new `publish_json_out`; `main` rewired), `tests/test_rb_contact_evasion_bundle_gate.py` (8 `--json-out` negative controls + 1 structural test), the paired `docs/audits/…-2026-08-25.{md,json}` (fifth-round section), and this handoff. No Slice A change; nothing under `exports/**`; reference bundle byte-identical.
- Audit-trigger status: **triggered**; final exact-head audit **pending fresh Codex review of the repaired head**.
- What is now true (correcting the prior entry): `--json-out` no longer writes via `Path.write_text()`. Reproduced against the real gate: with `--json-out` a hard link sharing `manifest.json`'s inode, `write_text` followed the shared inode and truncated the validated file (1086→2913 bytes) while the gate returned exit 0; a leaf swapped to a symlink into the bundle after the preflight, and a parent directory swapped to a symlink into `observations/`, likewise corrupted the bundle. The realpath "inside the bundle" preflight cannot see a hard link and is raceable, so it is demoted to a usability guard. Publication now goes through a **fresh staging inode** (`O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW`) created relative to the intended output parent opened with `O_NOFOLLOW|O_DIRECTORY`, then a single `os.replace` of the destination **entry** — `rename` never follows the destination, so a hard-linked/symlinked output is repointed at the new inode while the old (possibly bundle-shared) inode keeps its bytes. A refusal or a failed `os.replace` leaves the bundle and any prior output byte-for-byte unchanged; staging litter is cleaned up relative to the pinned dir_fd only. Output bytes and exit codes are unchanged.
- Focused test count: `pytest --collect-only` = **297** node IDs (288 + 9 new: 8 `--json-out` controls + 1 structural). Full Python suite **1018 passed / 3 skipped**. Mutation testing: **5 mutations** against the real publication, all killed, no degenerate, gate restored byte-for-byte.
- What is still missing: fresh Codex exact-head review of the repaired head; operator acceptance; the still-unimplemented admitted-source registry (no source admitted).
- What must not be assumed: passing the gate proves bytes and file identity, not football truth; a pathname `realpath` check is not a safe write guard (it cannot see a hard link and is raceable) — safe publication is staging-inode-then-atomic-replace bound to an `O_NOFOLLOW` parent; the toolchain remains trusted and out of scope.
