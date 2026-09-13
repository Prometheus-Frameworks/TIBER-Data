# Nineteen-player historical promotion receipt v1

The separate `exports/promoted/draft_review/team_roster_identity_promotion_v1.json`
records the operator's 2026-09-13 grant of bounded historical consumer use and
activation implementation. It does not rewrite the earlier preparation receipt
or its authorization flags. The two receipts describe distinct decisions.

## Scope and authority

- Exactly the nineteen previously reviewed Sleeper-to-GSIS edges; Antonio
  Williams / `13301` is excluded. No new identity matching or source acquisition.
- The original 75 identities, all nineteen prepared rows, source bytes,
  confidence, historical teams and recorded-week validation remain unchanged.
- Consumer scope remains retrospective descriptive 2025 weeks 1–18. Recorded
  weeks are not certified games; absent weeks remain unknown. Historical teams
  are weekly source teams, not current Sleeper teams.
- `historical_consumer_use_authorized` and
  `consumer_activation_changes_authorized` are true. `merge_authorized`,
  `deployment_authorized` and `production_release_authorized` are false. The
  latter includes previews. Review and separate authorization are required
  before activation merge or deployment.
- Conversation acceptance is transcribed exactly with a null public receipt
  URL. No GitHub acceptance, review result or release receipt is invented.

## Validation contract

The offline materializer binds every input to merged Data commit
`c0a7d1e98161c23f64f67c075f81eb71d6ba693a` and an exact SHA-256, also rejecting
working-file drift. It replays the earlier preparation validator, including
identity agreement and source-window checks, before producing this receipt.
The JSON authority envelope must equal deterministic replay; unknown fields,
numeric substitutes for booleans, changed scope, identities, hashes or grants
are rejected. Existing differing output is never silently overwritten.

Consumers must pin the receipt bytes and producer commit, verify its link to
the unchanged preparation receipt/crosswalk, preserve all embedded source
limitations, and admit only the exact cohort. A status string, directory name,
PR merge, environment switch or manager note alone grants no historical use.
The corresponding Fantasy change pins this separate receipt in its offline
bundle and its whole-bundle runtime integrity gate.

## Source limitations

The receipt retains the original consumer scope, historical validation and
limitations verbatim. Fourteen name-exact matches remain medium confidence;
three direct GSIS and two ESPN bridge matches remain high. The aggregate window
contains 248 recorded observations in each lane; 94 absent calendar slots are
unknown, and nine post-window observations per lane remain excluded.

Attribution: nflverse contributors, CC BY 4.0, no endorsement implied. Terms
assessment remains dated 2026-09-07; original acquisition terms receipt and
source acquisition/update clocks remain unavailable. No league fantasy points,
projections, regression predictions, current role/health/eligibility, ownership,
rankings or transaction authority are created. Neither the receipt nor a
consumer activation establishes any roster cut or other manager action.

## Replay

Run `python scripts/materialize_team_roster_identity_promotion.py --check` from
the repository root with the existing validation dependencies and pinned Git
objects available. This performs no network acquisition or production action.
Independent implementation review is recorded separately from mechanical replay.
