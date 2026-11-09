# Metric-definition inspection implementation handoff

Prepared 9 November 2026. Implementation candidate; unmerged and unactivated.

## Scope and authorization

Joe's decision authorized a separate Data-only implementation PR following the
assessment of study PR #285. The study PR remains separate and unmerged.

Task classes: data artifact/inspection metadata, provenance/source inspection,
and supporting documentation. Allowed changes are the existing semantic
registry/viewer, read-only helper, generated semantic views, matching tests,
development check wiring, and this audit/documentation. Canonical metric
contracts, producers, production observations, promoted exports, source
admission, scoring, runtime service routes and downstream consumers are excluded.

Baseline: `35fc692b67d2e218b3033e7e30688e03c367de58`.
No existing field definition, status, null policy or formula was repaired.
The 37 existing entries retain their semantics; two entries gain exact-ID links.

## What is now true

- One editable inspection descriptor section lives in Data's existing registry.
  Generated JSON/Markdown are views, not parallel editable authority.
- Seven receiving-usage inspection IDs expose formulas and unresolved bindings,
  including the gold compatibility alias that retains the summed-player-route
  denominator under the name `route_participation`.
- Exact lookup, explicit family selection, incompatible/unresolved comparisons,
  missing concepts, source-pin/digest checks, and generated-view drift checks work
  locally without a service or upstream data access.
- Coverage receipts independently reproduce the pinned 6,326-row route gap and
  the six fixture-only populated rows. Populated upstream target share retains
  its unresolved formula binding. Season type and source clocks remain unknown
  where the artifact does not supply them.
- Every result denies consumer authorization. Definition identity is separate
  from observation comparability, source qualification and canonical approval.

## Validation

| Command/check | Result |
| --- | --- |
| `npm run test:metric-definition-inspection` | 19 Node checks passed; no skips |
| `python -m pytest tests/test_metric_definition_source_parity.py tests/test_build_player_weekly_usage_source_backed_2025.py tests/test_api.py -q` | 27 passed, including 12 source-parity cases |
| `python -m ruff check tests/test_metric_definition_source_parity.py` | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed |
| `npm run test -- --exclude test/rosterPlayerTeamMapArtifact.export.test.ts` | 966 tests passed across 18 files |
| `npm run test -- test/rosterPlayerTeamMapArtifact.export.test.ts --testNamePattern='^(?!.*supports source_backed lane).*'` | 11 passed; the known source-backed comparison case was deliberately excluded |
| `--definitions list --check-generated` | JSON and Markdown exactly reproduce their registry source |
| Legacy viewer filters | Opportunity remains 8 of 37; status and consumer filters pass |
| `node --check` for viewer/helper; `git diff --check` | Passed |
| Protected-surface comparison against baseline | No changes to contracts, derive/transform/export code, raw/processed observations, promoted exports or web runtime |

The 977 bounded TypeScript passes above are not full-suite signoff. A separate
diagnostic of the unchanged roster producer reproduces the pre-existing equality
mismatch: generated JSON is an array, the compared raw JSON is a wrapper object,
and equality is false. The excluded test is not repaired here. The full Python
suite and unrestricted `scripts/pre_pr.sh` have not been completed for this
candidate. No GitHub CI pass is claimed.

The Python source probes use synthetic inputs only. The compatibility-alias
probe replaces the unrelated vacated-target helper with explicit synthetic null
context: its unchanged legacy `how='outer'` join is rejected by this environment's
Polars 2.1.0. The actual compatibility builder and route alias execute unchanged.
This isolates the mapping; it is not full compatibility-pipeline qualification.

## Contradiction audit and remaining gates

Builder contradiction audit completed: attempted fixture promotion, lost fixture
labels, source digest/working-tree drift, nonexistent pins/symbols, stale generated
views, ambiguous names, incomplete formulas, unit mismatch, and conflicting alias
components are rejected or explicitly unresolved. Numeric coverage counts never
certify observations. Known gold target-zero behavior remains visible.

Independent review of the exact implementation head is pending. Builder checks
are not independent review. Operator acceptance, any baseline-blocker disposition,
canonical definition approval and any downstream integration remain outstanding.

Do not assume that route observations exist, this catalog improves forecast
accuracy, a named consumer is wired, or documentation grants source rights or
source admission. No merge, activation, metric repair, source acquisition, ROP
recalculation or ranking change is part of this handoff.

Machine handoff: [audit.json](audit.json).
Interface and later gates: [inspection documentation](../../metric-definition-inspection.md).
