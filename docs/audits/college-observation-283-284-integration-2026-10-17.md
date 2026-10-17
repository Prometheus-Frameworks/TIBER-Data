# College observation PRs #283 / #284 integration decision

Inspection: 2026-10-17, approximately 22:31–22:36 UTC. This is a bounded
integration audit and operator handoff, not a new independent code review,
source qualification, provider admission, data promotion, or deployment grant.

## Recommendation

**#283 is code-ready at its unchanged independently reviewed head. Hold the
merge until the production-deployment boundary is established and Joe gives
final approval. Merge #283 before #284. #284 is not merge-ready.**

An ordinary merge into `main` must not be described as deployment-free. The
Railway production service follows this repository's `main`; its latest
successful deployment is the current `main` commit, itself a docs-only merge.
No deployment settings were changed. The read API does not separately expose
the current Enable/Disable autodeploy switch, so suppression is not established.

## Task class, authority, and allowed surfaces

- Active task: integration audit of two existing college-observation contract
  repairs; no implementation changes are needed on the inspected evidence.
- Classes: contract task plus repository-governance/audit handoff.
- Instructions: `AGENTS.md`, `TRUTH_SOURCES.md`, `HANDOFF.md`, and
  `docs/TIBER_DOCTRINE.md` at `main@0d9f82a8d0225602faea4887adf314983ee25a3a`.
  No nested AGENTS.md, CODEOWNERS, or GitHub Actions workflow files were found
  in that tree. AGENTS.md is unchanged at the #283 head.
- Data owns canonical observed-fact contracts; fantasy scoring, league state,
  provider admission, source acquisition, and downstream activation remain
  outside this assignment. Issue #265 is an architecture proposal, not an
  authority grant for those operations.
- Joe retains the final merge decision. The existing independent Codex review
  is reused; this audit does not claim an additional independent review.
- Files created by this handoff: this MD file and its paired JSON, on an
  isolated audit branch. Neither PR's code/document head is modified.
- Audit-trigger status: triggered for both contract surfaces; #283 independent
  exact-head review completed; this integration receipt is committed separately
  to preserve that reviewed head. #284's P1 remains open and its post-integration
  audit/review is pending.

## Current exact pins and merge controls

| Surface | Observed state |
| --- | --- |
| `main` | `0d9f82a8d0225602faea4887adf314983ee25a3a` |
| #283 | `d3a2bec2b7d0f69cf9881371caf48e10fbb1f230`; open, non-draft, unmerged, mergeable; REST mergeable state `clean` |
| #284 | `e2c41d1e9efd704c175aac3b5120510461a06274`; open, unmerged; restored to draft during this task |
| Both targets | `main`, initially the exact base above |
| Head checks | Zero check runs, zero commit statuses, zero PR-triggered workflow runs returned on each exact head |
| Branch controls | Branch endpoint reports `protected=false`, required-status enforcement off and empty contexts/checks; rulesets collection returns `[]` |
| Protection limitation | Detailed protection endpoint returns 403 to the integration; this is not an audited inventory of every administrative setting |
| Merge methods | Merge commit, squash and rebase allowed; repository auto-merge disabled; no PR auto-merge request present |
| Formal reviews | #283 has no formal APPROVED submission; its completed no-findings review is a verified bot conversation receipt. #284 has COMMENTED reviews and an unresolved P1 |

No required GitHub check is observed. Empty check lists are **not passing CI**.
GitHub's mechanical mergeability does not supersede the semantic, deployment,
or operator gates in this handoff.

## #283 evidence and validation

Independent review receipt:
https://github.com/Prometheus-Frameworks/TIBER-Data/pull/283#issuecomment-6233812448

The review summary's machine-readable record binds completed/no-findings review
to the full current head `d3a2bec2b7d0f69cf9881371caf48e10fbb1f230`.
There are no inline review threads on #283. No repeat independent review was
requested and no code correction is indicated by this integration inspection.

The complete diff against current `main` is two files, 199 insertions:

- `src/contracts/college_player_game_observations_v0.py`: 52 insertions;
- `tests/test_college_player_game_observations_v0_scope_cycles.py`: 147 insertions.

There is no schema, contract-document, fixture, source-data, generated-output,
provider, deployment-config, or downstream change. The three repairs bind game
expectation evidence to declared scope, reject related-observation cycles, and
retain unmistakably synthetic attribution identities. Existing shape gates
remain authoritative; validation does not prove source authenticity.

Fresh local validation used Python 3.12.14, pytest 9.1.1, Ruff 0.17.1 and
jsonschema 4.26.0 in an isolated environment:

| Check | Reviewed head | Unchanged base |
| --- | --- | --- |
| `python -m pytest -q tests/test_college_player_game_observations_v0*.py` | 93 passed | 86 passed (new regression module absent) |
| Ruff check on the two changed files | Passed | Not rerun |
| Ruff format check on the two changed files | Passed | Not rerun |
| `git diff --check BASE HEAD` | Passed | Not applicable |
| Historical landing-context module | 25 passed, 1 skipped | 25 passed, 1 skipped |
| One RB bundle-gate representative test | Setup error: repository-local TypeScript compiler absent | Same setup error and reason |

The PR author's earlier full `pytest tests` receipt reports 292 RB bundle-gate
errors from missing `node_modules/typescript` and one historical landing-context
failure, with an identical failure set before and after the original repair.
That is **not a full-suite pass**. This task did not rerun the entire suite or
independently reproduce that exact 292+1 count. It reproduced the TypeScript
environment failure on both exact revisions, verified the affected code/tests
and dependency declarations are unchanged by #283, and found the historical
module passes in this full-history checkout (apart from its explicit sibling
Rookies-checkout skip). Do not carry the old historical failure forward as a
current observed failure, or turn these bounded checks into global certification.

The three original #275 P2 threads remain open intentionally until the repair
lands. They are repaired by #283, not additional unexplained findings on #283.
After merge, reply with the actual merge commit and regression evidence, then
resolve those three threads. The other two #275 threads are already resolved.

## Production-deployment gate

Read-only Railway observations:

- Project: `03bd21d1-eafa-42e8-af4a-7ccb7340a04f` (`TIBER-data`).
- Environment: `9bb58819-c3ed-424e-962a-4d08b6931ad3` (`production`).
- Service: `093caa5b-155e-48c6-9106-36ff935f2732` (`TIBER-Data`).
- Live config: source repo `Prometheus-Frameworks/TIBER-Data`, branch `main`,
  `checkSuites=false`; no staged changes or watch patterns were returned.
- Latest deployment `712c58e1-5ecc-468a-a270-75f7621d649e` is `SUCCESS`, created
  2026-10-06T10:53:00.453Z, commit `0d9f82a8d0225602faea4887adf314983ee25a3a`,
  the docs-only #274 merge. Earlier history also contains the #279 merge.
- Railway's official autodeploy documentation says connected-branch pushes
  automatically deploy unless disabled. It documents an explicit Disable control.
  No commit-message skip mechanism was established by the documentation read:
  https://docs.railway.com/deployments/github-autodeploys

Inference: a normal `main` merge is expected to trigger production rebuild/deploy;
current suppression is unproven. A no-production-effect merge therefore needs a
separately authorized, verified deployment control before the merge. Do not change
hosting settings or use an undocumented skip token under this task. No deployment,
restart, variable read, setting change, acquisition, private-data operation,
provider/consumer activation, or merge was performed.

## Exact integration sequence

1. Establish and verify a no-deployment merge path for the production service;
   retain the current successful deployment. Any hosting change requires its own
   explicit scope. Joe gives final approval for #283 at the exact reviewed head.
2. Immediately before merging, recheck `main`, #283 head/state, checks/reviews,
   and the deployment control. If anything material changed, stop and re-evaluate.
   Prefer a normal merge commit to preserve the reviewed head's ancestry; no
   force, bypass, auto-merge, provider work or production activation.
3. Merge #283 only after those gates. Record the actual merge commit, verify its
   validator content, and confirm no new production deployment occurred. Resolve
   the three repaired #275 P2 threads using that merge commit.
4. Keep #284 targeting `main`. Once #283 is actually merged, bring that merged
   `main` into `claude/data-265-expectation-doc` without force-pushing over another
   worker. Merely leaving its target named `main` is not the branch update promised
   in the P1 response. Record the resulting exact head and base/merge-base.
5. Verify that #284's remaining diff against the updated `main` is docs-only
   (the two-line rule, unless a bounded documented correction is necessary).
   Do not duplicate the validator patch into the documentation diff.
6. Verify the rule against the merged validator, rerun the college-observation
   tests at the updated documentation head, and check the specific existing tests:
   `test_expectation_evidence_binds_to_declared_game_scope` and
   `test_season_scoped_expectation_evidence_covers_its_season`. Confirm unrelated
   season/game refs fail, every expected game has an admitting ref, valid scoped
   and source-wide refs remain usable, and explicit zero-game scope is preserved.
7. Reply to #284's P1 with actual merged implementation SHA, new branch head,
   diff and test evidence. Obtain the necessary independent review of that updated
   integration, then resolve the finding only when the prerequisite is genuinely
   satisfied. Restore ready status after clean verification/review.
8. Present #284's resulting exact head and deployment boundary to Joe for a
   separate final merge approval. Today's work does not approve that future head.

P1 finding:
https://github.com/Prometheus-Frameworks/TIBER-Data/pull/284#discussion_r4271124695

## Handoff state

Now true: existing #283 review reused, focused tests independently replayed,
ordering repaired by restoring #284 to draft, and the operational merge risk
made explicit. Both inspected code/document heads remain unchanged.

Still missing: verified deployment isolation, final operator approval of #283,
its actual merge, #284's subsequent branch update and exact-head integration
review, factual resolution of the P1 and old P2 threads, and separate #284 approval.

Must not assume: either PR is merged, global CI is green, source authenticity is
qualified, fixtures are real observations, college coverage is available, any
provider is admitted, or a downstream production consumer is activated.
