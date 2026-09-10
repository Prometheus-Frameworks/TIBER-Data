# Team historical identity proposal — Data #267

Status: **proposed, inactive**. Preparation and independent review were authorized
in the live Work conversation on September 10, 2026. This is an agent-recorded
scope receipt, not operator admission. Review, a branch push, or merging proposal
documentation does not activate these mappings. No promotion or consumer rebuild
is included.

Task class: provenance/source audit and downstream handoff preparation. Allowed
surfaces are this audit pair, a read-only checker, focused tests, and an appended
HANDOFF entry. Existing candidates, sources, 72 promoted records, contracts and
the accepted historical-use receipt remain byte-identical.

## Exact proposal

| Player | Sleeper | GSIS | Tier / confidence | Recorded outcomes / usage weeks | Historical team |
| --- | --- | --- | --- | --- | --- |
| Parker Washington | 9487 | 00-0038606 | name_exact / medium | 16 / 16 | JAX |
| Drake London | 8112 | 00-0037238 | name_exact / medium | 12 / 12 | ATL |
| Chris Rodriguez Jr. | 10219 | 00-0038611 | name_exact / medium | 12 / 12 | WAS |

The third candidate's Sleeper name is **Chris Rodriguez**, while its canonical
name includes **Jr.** Its candidate team is JAX, a dated identity-context value;
the weekly observations remain WAS. Neither spelling normalization nor team
agreement is newly used to infer identity. These are the existing candidate
edges under review. Each occurs uniquely by provider and canonical ID in the
full 1,106-row candidate set and does not collide with any of the 72 promoted
rows or the retained candidate conflict CSV. Coverage name, position and ESPN
context agree. Both Sleeper-declared GSIS and ESPN IDs are absent, so coverage's
ESPN value cannot establish a provider-ID match. The original raw Sleeper dump
is unavailable; its digest is preserved, and the original normalized-name census
was not rerun.

## Source pins and time semantics

Current remote main and checkout base: `b0c79de5403864796a5701dc42bcda8eafd788ab`.
The companion JSON pins candidates, full promoted crosswalk, coverage, conflict
CSV, two weekly artifacts, accepted receipt and reused audit helper by SHA-256.
This checker reads current checkout bytes and fails on any input drift; it does
not silently substitute an archived version. No source builder or network fetch
is part of replay. The existing #263 checker remains unchanged.

Candidate generation: `2026-08-08T18:17:13.819524+00:00`. Proposed V2 rows retain
`2026-08-08T18:17:13Z` at the existing validator's precision. That field records
candidate generation, **not** source acquisition or provider update. Unknown
source clocks, release hash and package version stay null. The source-use terms
assessment remains September 7; this work makes no new rights determination.

## Weekly inspection and proposed permission delta

All subjects have unique season/week/GSIS rows. Their joined usage and outcomes
agree on historical team, opponent and position, with no missing usage rows.
The companion JSON lists exact weeks and per-field recorded, nonnull, null and
zero week coverage. The 16/12/12 denominators differ; they are observations,
not certified games played, and missing calendar weeks imply no bye/DNP/injury.
Parker's week 19 is explicitly excluded in both lanes. The window is 2025 weeks
1–18 under the documented regular-season boundary; game_type/game_id are absent.
The full-source inspection still reports nine position conflicts for other
players; none is silently repaired or attached to these proposed identities.

The proposed delta is **exactly three identity edges**. If subsequently accepted,
the existing pinned historical scope and attribution requirements must continue
unchanged. The JSON carries that scope verbatim from the accepted receipt for
review, but `consumer_allowed=false`, `operator_admission_decision=null` and
`effective_admission=false` keep this proposal inert. A later accepted receipt
must bind these specific edges, reviewed commit, hashes and explicit operator
decision; the existing receipt does not already authorize them.

Counts come from the null-preserving outcomes lane; usage contributes weekly
target share and air-yards share only. Totals require complete inputs, means
state nonnull denominators, and average weekly share is not season share.
Ambiguous air-yards totals, routes, snaps, red-zone data and rush share remain
unavailable. This grants no league point totals, current roles or injuries,
roster eligibility, ownership, rankings, projections or transactions.

Attribution remains **nflverse contributors**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[source](https://github.com/nflverse/nflverse-pbp), with TIBER filtering/aggregation
identified and no endorsement implied. Existing acquisition-receipt limitations
remain. This is retained committed evidence; no new acquisition occurred.

## Reproduction and next decision

```
python scripts/audit_team_identity_proposal.py --check
python -m pytest tests/test_team_identity_proposal.py tests/test_draft_review_evidence_admission.py tests/test_identity_crosswalk_v2.py -q
```

The focused checks verify inert exact replay, all three V2 rows in a purely
in-memory 75-row artifact, collision rejection, snapshot drift, denominator
null/zero handling and week 19 exclusion. No materializer is executed.
Independent exact-head review is required and will be recorded in the linked PR.
Only after review may the operator separately accept or reject these exact
medium-confidence edges. Admission, materialization, consumer regeneration,
merge and production release remain unexecuted and separately gated.
