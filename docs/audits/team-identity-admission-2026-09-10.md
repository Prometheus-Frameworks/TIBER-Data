# Three Team identities — branch admission/promotion preparation

Task classes: data artifact and downstream handoff. This mechanical preparation
implements [the operator's bounded authorization](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/268#issuecomment-5627117154)
following [the reviewed proposal](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/268#issuecomment-5627016520)
at `22e9843df74ced8f2856c6463c86b626a79683d1`. Independent review of the resulting
mechanical commit is still required; this builder audit is not that review.

Exactly Parker Washington (`9487`→`00-0038606`), Drake London
(`8112`→`00-0037238`) and Chris Rodriguez (`10219`→`00-0038611`) are added to the
prepared V2 artifact. Original 72 rows are preserved, producing 75 rows with
23 gsis_direct, 6 espn_bridge and 46 name_exact. New rows stay name_exact/medium.
The schema and identifier vocabulary are unchanged.

A separate `team_identity_admission_v1.json` binds the archived proposal hash,
source pins, proposal review and later authorization. It declares
`accepted_for_branch_preparation`; consumer regeneration, merge, production
deployment and release are explicitly false. Old `evidence_admission_v1.json`
is byte-identical. The crosswalk pins both receipts. No consumer bundle is
regenerated and production still depends on its existing released revision.

The archived proposal MD/JSON are unchanged and remain inactive historical
records. Their current-checkout-only replay description now has a narrow,
explicit exception: the audit reads its superseded 72-row crosswalk from
immutable base `b0c79de5403864796a5701dc42bcda8eafd788ab`. All other input hashes
are checked against current bytes. The materializer uses reviewed commit
`22e9843` for the same historical crosswalk and proposal; missing git objects
fail rather than silently switching inputs. It verifies every other current
source pin, validates the exact typed authority envelope and V2 schema, and
refuses to overwrite anything except the exact base or its own output. The
old 72-row CLI now refuses both check/write while the separate receipt exists;
its pure builder remains available to replay that archived stage.

The preserved historical scope is 2025 weeks 1–18. Recorded outcome and usage
weeks are 16/12/12; these are not certified games played. Parker week 19 is
excluded in both lanes. Rodriguez candidate team JAX stays dated identity
context while weekly observations remain WAS. No missing observations become
zeros, no historical average becomes a projection, and original null clocks,
missing raw Sleeper census, acquisition receipt and dated terms assessment
limitations remain verbatim in the separate receipt. Attribution remains
nflverse contributors, CC BY 4.0, no endorsement implied, with TIBER's filtering
and aggregation identified. No new acquisition or terms review occurred.

Validation: 74 focused tests passed across the three-identity admission,
three-identity proposal, previous four-identity admission, previous evidence
audit and V2 suites. Tests cover exact additive replay, idempotence, immutable
sources, medium confidence, period/denominator/team semantics, typed authority
mutation rejection, source-drift rejection and legacy rollback prevention.
The companion JSON records hashes and byte-preservation facts; review receipts
belong on the PR at the resulting exact commit, avoiding circular self-hashes.

Stop: no Data #269 work, consumer regeneration, merge, deployment or release.
