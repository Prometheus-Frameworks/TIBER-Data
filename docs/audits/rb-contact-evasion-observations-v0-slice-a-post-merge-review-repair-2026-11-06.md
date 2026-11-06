# RB contact-evasion observations v0 (Slice A) — post-merge independent-review repair record — 2026-11-06

> Status: review-and-repair record for the Slice A contract; not a source admission, ingest, artifact, promotion, or consumer activation
> Tracking issue: TIBER-Data #234
> Pull request reviewed: TIBER-Data #259 (merged 2026-08-25 as squash `4498d5efd053e6bbc87f5f28214b0509550ad653`)
> Reviewed head (findings produced): `83b7e41ccf7481b3a7d08f3d4cd9e66e748bba77`
> Repair base: `main` at `c46e9c33` (2026-11-06)
> Related governance advisory: TIBER-Ops #74 (program-alignment: merge-authority receipt and #234 terminal decision not materialized)

## Answer first

PR #259 merged with **four unresolved `chatgpt-codex-connector` review threads** created 2026-08-25T00:24:19Z,
eight minutes after the operator-account exact-head review declared the head clean. Verified on 2026-11-06
against the live PR: all four threads remain unresolved, none was addressed by PR #260 (Slice B, which pinned
Slice A unchanged) or PR #261, and the three code findings reproduce against `main` through the public evaluator.

| Thread | Badge | Finding | Status at `main` before repair | Disposition |
| --- | --- | --- | --- | --- |
| r3848531165 | P1 | A digest-pinned snapshot is admitted when `retention_and_reproduction` is `unknown` (only `prohibited` rejected) | **reproduced** — missing row, snapshot, valid digest, retention unknown → `valid: true` | repaired |
| r3848531172 | P1 | Definition drift keyed globally by `metric_id`, so two providers cannot both observe one canonical metric | **reproduced** — second provider with its own source-native definition → `METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID` | repaired |
| r3848531175 | P2 (the dispatch described it as P1) | Uniqueness grain omits the source namespace; two owners reusing one `snapshot_id` collapse into a false duplicate | **reproduced** — distinct owner/product, same snapshot id → `DUPLICATE_OBSERVATION_GRAIN` | repaired |
| r3848531179 | P1 | No committed `docs/audits/` artifact for the Slice A contract change; auditor review recorded as pending | **confirmed** — `docs/audits/` held only the Slice B bundle-gate record | this record |

This record does **not** constitute an independent audit of the repaired head. It records who produced the
findings (the Codex connector review), the reproduction, the repair disposition, and the residual boundaries.
Final exact-head audit status is **pending fresh independent review of the repaired head**.

## Task class and boundary

Contract task under AGENTS.md (touches `src/contracts/**`, `docs/contracts/**`, matching tests and fixtures),
plus a repo-governance record (this audit pair, `HANDOFF.md`). Audit trigger: **fired** (contract change under
`src/contracts/**`; grain/identity semantics touched). No shape change: the JSON Schema is byte-identical and
the schema version stays `rb_contact_evasion_observations_v0.4.0`. No reason code was added or removed.

Not done, deliberately: no source accessed, probed, classified, or admitted; nothing under `exports/**` read or
written; no candidate or promoted artifact; no Slice C; no model activation; no consumer activation; no merge.
`README.md` unchanged (no coverage or support claim changes).

## Pinned evidence

| Object | Exact ref | Purpose |
| --- | --- | --- |
| PR #259 head reviewed by the connector | `83b7e41ccf7481b3a7d08f3d4cd9e66e748bba77` | findings produced here |
| PR #259 squash on `main` | `4498d5efd053e6bbc87f5f28214b0509550ad653` | Slice A as merged; Slice B's authorized base |
| `main` at repair time | `c46e9c33` (merge of PR #284) | repair base; all three attacks reproduced here |
| Connector review | PR #259 review 5013780978, 2026-08-25T00:24:19Z | thread ids r3848531165, r3848531172, r3848531175, r3848531179 |
| Operator-account exact-head review | PR #259 review 5013744839, 2026-08-25T00:16:23Z | declared clean; explicitly did not authorize merge |
| Governance advisory | TIBER-Ops #74 | records that #259–#261 merged without a materialized merge-authority receipt or #234 terminal decision |

## Reproduction (before editing, at `main`)

Through the barrel-exported `evaluateRbContactEvasionObservationsV0`:

```text
K1  P5 with measurement -> missing/not_measured, retention -> unknown        valid:true   codes: []
K1c same with retention -> prohibited                                        valid:false  [CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION]
K2  P1 + second provider (new owner/product/snapshot, own definition)        valid:false  [METRIC_DEFINITION_DRIFT_UNDER_STABLE_ID]
K3  P1 + second owner/product reusing the same snapshot_id                   valid:false  [DUPLICATE_OBSERVATION_GRAIN]
```

## Findings and repair disposition

### r3848531165 (P1) — unknown retention admitted a digest-pinned snapshot

`checkSourceAndEvidence` rejected a content digest only when retention was `prohibited`. Snapshot provenance is
retained, rebuildable material and requires a digest; a missing row stores no value, so the stored-value
retention rule had nothing to gate, and `unknown` was silently read as permission — contradicting the contract
doc's own rule that unknown dispositions fail closed everywhere.

**Repair.** The digest rule now requires the affirmative `permitted` disposition: any recorded `content_digest`
with retention `prohibited` **or** `unknown` fires `CONTENT_DIGEST_NOT_PERMITTED_BY_RETENTION`. Because a
snapshot requires a digest, this closes the snapshot path for every measurement status. No new code: the
existing code's semantics were completed rather than widened.

**Evidence.** N50 `n50_snapshot_digest_with_unknown_retention.json` (shape-valid, exactly one code). Exact-attack
lock plus prohibited and permitted controls (P5 as committed, and its missing variant, both valid). A
`rights_blocked` snapshot under unknown retention is rejected. New cross-product provenance × digest × retention
disposition × measurement status (2 × 2 × 3 × 2 = 24 cases) asserts code-set equality.

### r3848531172 (P1) — definition drift keyed globally by `metric_id`

`checkDefinitionDrift` keyed its map on `metric_id` alone, so a second provider's legitimately different
`source_native_metric_name` / `definition_ref` / `definition_version` for the same canonical metric was rejected
as drift. The contract's stated purpose for the rule is one provider changing what *its own* stable id means.

**Repair.** Drift is keyed by source identity × metric: `[owner, product, metric_id]`. The violation detail names
the provider. N4 (one provider, two definitions) is unchanged and still rejected.

**Evidence.** P10 `p10_two_providers_same_canonical_metric.json` (two owner × product identities, one
`metric_id`, two definition versions, valid). Exact-attack lock; N4 lock; drift attributed to the drifting
provider when another provider is present; same owner under a different product admitted.

### r3848531175 (P2) — uniqueness grain missing the source namespace

`rbContactEvasionGrainKey` carried `snapshot_id` without `owner`/`product`. The schema places no
global-uniqueness requirement on `snapshot_id`, so two distinct providers could not both record the same
player × window × metric if their locally meaningful snapshot ids coincided.

**Repair.** The exported grain key now includes `source.owner` and `source.product` before `snapshot_id`. N20
(same owner × product × snapshot, repeated grain) is unchanged and still rejected. The documented grain and the
`DUPLICATE_OBSERVATION_GRAIN` detail text were updated to match.

**Evidence.** P11 `p11_distinct_providers_share_snapshot_id.json` (identical `snapshot_id` across two
providers, valid, distinct grain keys). Exact-attack lock; same owner × different product admitted; N20 and the
renamed-duplicate lock unchanged; key differs by owner alone and by product alone.

### r3848531179 (P1) — missing committed Slice A audit artifact

AGENTS.md requires the auditor function and committed audit output for changes under `src/contracts/**`,
`schemas/**`, and `docs/contracts/**`. PR #259 committed none; its body recorded "Auditor review pending".

**Disposition.** This paired `.md` / `.json` record under `docs/audits/` follows the repository's dated-paired
convention. It does not fabricate an independent auditor identity: the findings were produced by the Codex
connector review, the repair and its evidence were produced by the builder function in this session, and
independent exact-head review of the repaired head remains pending.

## Slice B consequence

PR #260's gate test `test_slice_b_did_not_modify_slice_a_contract_files` pinned every Slice A file to the Slice A
squash commit by `git diff`, which no legitimate Slice A change could survive, and which silently skipped on
shallow clones. It is replaced by `test_slice_a_surface_changes_only_through_its_committed_digest_manifest`,
which binds the exact bytes of all 66 Slice A surface files to the committed manifest
`tests/fixtures/rb_contact_evasion_slice_a_surface_digests.json`. A Slice A change must now update the manifest
in the same reviewed change, and a gate-only change cannot touch Slice A without the manifest diff showing it.
The corpus-count guard moved from 9/49 to 11/50. No gate behavior changed.

## Verification (repaired head, local)

| Check | Before | After |
| --- | --- | --- |
| `vitest run test/rbContactEvasionObservationsV0.contract.test.ts` | 748 passed | **791 passed** (+43) |
| `pytest tests/test_rb_contact_evasion_observations_v0.py` | 81 passed | **84 passed** (+3) |
| `pytest tests/test_rb_contact_evasion_bundle_gate.py` | 292 collected | **295 passed** (Slice A guard rewritten; +3 fixture parametrizations) |
| `tsc --noEmit` | clean | clean |
| `ruff check` (both Python test files) | clean | clean |
| `git diff --check`, JSON validity of new fixtures and manifest | — | clean |

**Mutation evidence** — each mutation applied to the real implementation, focused suite run, implementation
restored byte-for-byte (sha256 verified):

| Mutation | Tests killed |
| --- | --- |
| `revert_digest_rule_to_prohibited_only` | 9 |
| `key_drift_globally_by_metric_id` | 5 |
| `key_drift_by_owner_only` (drops product) | 1 |
| `drop_owner_product_from_grain` | 5 |
| `drop_owner_only_from_grain` | 1 |
| `drop_product_only_from_grain` | 2 |

Six mutations, all killed, no zero-kill holes.

Full-suite results and any pre-existing unrelated failures are recorded in the PR description with the exact
commands run.

## Residual boundaries

- **Producer declarations are consistency-checked, not verified.** `owner`, `product`, `snapshot_id`, and the
  permission dispositions remain producer-declared until an admitted source registry exists; none does. Two
  "providers" are two declared identities, not two verified sources.
- **The digest is still format-checked, never recomputed.** Requiring `permitted` retention before accepting a
  digest closes a rights gap, not a bytes gap.
- **Grain namespace is owner × product.** A provider that renames its product between snapshots is two
  namespaces; the contract does not reconcile provider identity across time.
- **Governance gap recorded in TIBER-Ops #74 is not repaired here.** No merge-authority receipt or #234
  terminal decision exists in canonical state for #259–#261; that is an operator action, outside this task
  class. This record neither ratifies nor reverses those merges.
- **This record is not an independent audit of the repaired head.** Fresh independent exact-head review is
  required before the audit trigger can be marked complete and before any merge.

## Authorization boundary

This record authorizes no source access, collection, ingestion, candidate row, artifact, promotion, consumer
activation, model activation, or merge. The source, promotion, and consumer hold stands. #234 remains open; the
repair sits on an unmerged branch for operator review.
