# TIBER-Data — Agent Operating Contract

This file is the operating contract for **any** agent, model, or automated worker acting in this repository, now or in the future. It is deliberately model-agnostic: it describes functions and rules, not a specific model stack. Specific models or personas may fill any function below; none of them *are* the contract.

This repo is the canonical source of truth for football data contracts, deterministic data artifacts, provenance expectations, architecture governance documents, and governed handoff surfaces.

It is not a repo for speculative model behavior, scoring tweaks, product UX decisions, final rankings, fantasy scoring policy, or downstream model logic.

## Core rule

If source truth is missing, reduce scope.
Do not fabricate continuity.
Do not silently extend coverage.
Do not "complete the pattern" unless the repo actually contains the support to do so.

## Non-negotiable rules

1. **If source truth is missing, reduce scope.** Never widen a supported season/week/window claim without committed raw support (see `TRUTH_SOURCES.md`).
2. **Do not fabricate.** No invented rows, IDs, continuity, coverage windows, source labels, or provenance. No inventing provenance after the fact.
3. **Do not silently promote.** Fixture, demo, scaffold, or candidate data never becomes governed truth without an explicit, reviewed promotion step. `exports/promoted/` is a location, not a provenance guarantee — row-level `source` labels are the truth.
4. **No downstream recursion.** Downstream product or model output must not become upstream evidence unless explicitly converted into a new source-backed artifact with independent provenance and contract semantics (see `docs/repo-boundaries-and-feedback-loops.md`).
5. **Null/unknown beats fake defaults.** When source support is absent, emit `null`/`unknown` with honest status, never a plausible-looking value. Missing status is `unknown`; it is never inferred from absent rows.
6. **Contracts change explicitly.** Breaking changes are versioned. Never change a contract to fit bad data.

## Agent functions (model-agnostic)

Any capable model may serve any function. What matters is that the function's duties and skepticism are performed, and that no single change skips the functions the change requires.

### Architect / boundary keeper
- defines repo boundaries, scope, and integration boundaries
- writes or revises contracts/doctrine
- judges whether a proposed change is honest and whether it belongs in this repo or another repo
- is skeptical about: fake continuity, overclaimed support windows, contract drift, quiet schema changes, repo-purpose confusion

### Builder / implementer
- makes bounded, deterministic changes under existing contracts, tests, and fail-closed validation
- wires scripts, file generation, and export logic
- must not: invent source data, widen supported ranges without raw support, create "representative" rows, or reinterpret repo scope
- when uncertain, stops and marks the exact boundary: what exists, what is missing, what can be completed honestly right now

### Auditor / contradiction checker
- performs mid-flight and pre-merge audits
- checks scope drift, false support claims, provenance gaps, identity/crosswalk risk, and downstream/upstream recursion risk
- is invoked when a change is "technically correct but semantically suspicious," or when a builder may have over-completed the task
- audit outputs are committed artifacts (see `docs/audits/`), typically a paired human-readable `.md` and machine-readable `.json`

### Operator / maintainer
- makes the final review/merge decision
- records, at each material handoff: what is now true, what is still missing, what must not be assumed (see `HANDOFF.md`)
- owns promotion decisions; no agent self-promotes its own output to governed truth

## Task classification gate

Classify every task **before** implementation. Each class has an allowed surface and standing assumptions it must not make.

| Task class | May touch | Must not assume |
|---|---|---|
| **Contract task** | `src/contracts/**`, `schemas/**`, `docs/contracts/**`, matching tests | that existing data satisfies the new shape; that a contract change may bend to fit bad data; that consumers can absorb unversioned breaking changes |
| **Data artifact task** | `data/**`, `exports/**`, builder scripts, matching tests/docs | that fixture/scaffold rows are real; that coverage extends beyond committed raw support; that `promoted/` location implies governed provenance |
| **Provenance / source audit task** | `docs/audits/**`, `docs/data/*audit*`, read-only scripts and reports | that Hub/vendor/dataset-card metadata is sufficient provenance; that an audit may mutate the artifacts it audits |
| **External dataset audit task** | `docs/audits/**` (inventory/classification artifacts only) | that anything may be downloaded, mirrored, purchased, or ingested; that a paid/gated or unlicensed dataset is usable |
| **Repo-governance / documentation task** | `README.md`, `AGENTS.md`, `HANDOFF.md`, `TRUTH_SOURCES.md`, `docs/governance/**`, doctrine docs | that docs may create new doctrine casually, widen support claims, or contradict canonical governance docs |
| **Downstream handoff task** | handoff artifacts under `data/gold/**` / `exports/**`, handoff docs, `HANDOFF.md` | that downstream repos' needs justify inventing upstream truth; that a handoff implies the consumer's pipeline "works" |

If a task spans classes, it inherits the constraints of every class it touches. If a task fits no class, stop and escalate to the architect/operator function before building.

## External source / dataset posture

Outside data (public datasets, scraped data, Hugging Face datasets, Kaggle exports, paid/gated datasets, anything with unclear lineage) is **audit-first, ingest-never-by-default**:

1. **Inventory and audit before anything else.** Record license, access mode, redistribution terms, source lineage, schema, row counts, leakage risk, and identity risk (player/team naming, IDs, aliases, season/week keys, duplicate semantics).
2. **Classify before any mirroring is even proposed**, using this vocabulary:
   - `external_candidate` — eligible for a later, separately authorized governed experimental mirror
   - `schema_reference_only` — card/preview vocabulary may inform contract design; data itself is not usable
   - `benchmark_reference_only` — relevant only to eval/benchmark design; cite, do not mirror
   - `future_research_only` — no current TIBER relevance; parked
   - `rejected` — excluded with recorded rationale
3. **No ingestion, download, purchase, or governed mirror happens under the audit itself.** Any follow-up requires a new, narrowly scoped issue.
4. **Fail closed on license conflicts.** No declared license means no redistribution rights. A license tag that contradicts the access mode (e.g. MIT tag on a paid gate) is unresolved, not permissive. Relabeled scraped content keeps its upstream obligations.
5. **Prefer first-hand upstreams.** If a dataset repackages a source this repo already integrates (e.g. nflverse via `nflreadpy`), derive in-house instead of importing a middleman.

Worked precedent: `docs/audits/huggingface-nfl-dataset-eligibility-2026-07-05.md`.

## Audit triggers

A change requires the auditor function before merge when it:

- adds or changes a contract under `src/contracts/**`, `schemas/**`, or `docs/contracts/**`
- touches `data/raw/**`, `exports/promoted/**`, or candidate/generated artifacts
- expands a supported season, week, or window claim
- changes source, provenance, or support-claim wording anywhere (including `README.md` and governance docs)
- touches player/team identity semantics or crosswalks (e.g. `exports/promoted/identity_crosswalk/**`)
- proposes admitting, mirroring, or reclassifying any external dataset
- changes downstream handoff semantics or handoff artifacts
- adds large generated JSON artifacts, or builder code without matching test coverage
- feels technically correct but semantically suspicious

## Handoff expectations

Every material handoff states (format detail in `HANDOFF.md`):

- active task
- files touched
- what is now true
- what is still missing
- what must not be assumed
- audit-trigger status: not triggered, audit completed, audit pending, or audit skipped with reason

## Canonical documents

This file points at doctrine; it does not duplicate or compete with it. When this file and a canonical governance doc disagree, the governance doc wins and this file should be fixed.

- `TRUTH_SOURCES.md` — what counts as truth; fail-closed rules; forbidden moves; escalation rule
- `HANDOFF.md` — working handoff format and current handoff state
- `ARCHITECTURE.md` — canonical architecture entry point
- `docs/TIBER_DOCTRINE.md` — contract philosophy, inspectability, S-tier contract checklist
- `docs/repo-boundaries-and-feedback-loops.md` — layer definitions and the anti-recursion rule
- `docs/governance/cross-repo-governance-v0.md` — canonical state, observability, outcome calibration, world modeling; ownership matrix
- `docs/governance/evidence-layer-v0.md` and `docs/contracts/evidence-layer-v0.md` — evidence statuses, promotion gates, artifact targets
- `docs/governance/architecture/tiber-architecture-document-v1.0.md` and `docs/governance/architecture/tiber-architecture-quick-reference-v1.0.md` — architecture doctrine
- `README.md` — repo surface map and current artifact/coverage claims

## Operating posture

Before changing files, identify:

- what this repo is responsible for;
- what task class is active;
- what files/surfaces are allowed;
- what source truth exists;
- what support boundary must not be crossed.

If source support is missing, stop, reduce scope, or move the task to an audit/handoff path. Do not compensate with plausible placeholders, inferred continuity, or undocumented assumptions.

## Success condition

A good change in TIBER-Data is:
- deterministic
- bounded
- documented
- contract-safe
- honest about source coverage
