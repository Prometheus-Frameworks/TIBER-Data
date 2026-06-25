# PR D: 2024 team_week_raw_v0 Source Candidate Promotion Review

## Status

**NOT PROMOTED.** This review begins from the assumption that the candidate
artifact is not promoted, and stays not-promoted unless this document states
an explicit, justified decision to the contrary. See §13 for the decision.

This document is the human-directed promotion review required by
`docs/data/team-week-raw-v0-2024-source-artifact-spec.md` §9 and §10 (PR D)
and by `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §11, for the
candidate artifact produced by TIBER-Data #168.

## 1. Candidate artifact path

`exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json`

## 2. Validation report path

`exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json`

## 3. Manifest path

`data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json`

## 4. Reviewed merge SHA

`4dd17e5a1114ab7ba9594806934e3e54d4697c22` (squash-merge of PR #168, "build:
emit 2024 team_week_raw_v0 source candidate", verified against `main` at the
time of this review).

## 5. Review date

2026-06-25.

## 6. Reviewer/operator note

This review was performed by an AI coding agent (Claude Code) acting on
explicit operator instructions under TIBER-Data issue #169, applying the
locked decision framework and hard guardrails stated in that issue against
the live contents of the candidate artifact, validation report, manifest,
and the locked rules in `docs/data/team-week-raw-v0-2024-pr-c-preflight.md`
§8/§10/§11 and `docs/data/team-week-raw-v0-2024-source-artifact-spec.md` §9.
It is a structured documentation review, not an autonomous governance
authority — no field was reclassified, no contract was amended, and no
candidate output was modified to reach a particular outcome. All findings
below were re-verified directly against the repository's current files
rather than assumed from the issue text.

## 7. Validation summary

Re-ran no code; re-read the committed validation report directly. As of the
reviewed merge:

- `allPassed: true`, `rowCount: 544`, `teamCount: 32`.
- 14/14 named checks pass: `all_32_teams_present`,
  `expected_weeks_present_per_team`, `expected_team_game_row_count`,
  `no_duplicate_team_week_rows`, `valid_team_and_opponent_codes`,
  `reciprocal_opponent_consistency`, `rate_fields_bounded_0_1_or_null`,
  `required_finite_numeric_fields`, `pressure_rate_allowed_null_and_deferred`,
  `seconds_per_play_block_metadata_if_applicable`,
  `epa_split_block_metadata_if_applicable`, `source_refs_present`,
  `retrieval_metadata_complete`, `non_governed_status`.
- `expected_team_game_row_count` confirms the triple equality
  `expectedTeamGameRows == actualTeamGameRows == rowCount == 544`.
- `non_governed_status` check itself records
  `provenanceStatus: partial_real_data`, `governanceStatus: ungoverned` as
  the *passing* condition — i.e. the validation report's own success
  criterion for this check is that the artifact is **not** claiming
  governance. Validation passing is therefore evidence of an honest
  non-governed artifact, not evidence of promotion-readiness.
- Coverage block in the artifact confirms `isFullLeague: true`,
  `isFullRegularSeasonCalendar: true`, `missingTeams: []`,
  `unexpectedTeams: []`, weeks `1..18` only, `byeWeeksHandled: true`.
- Per-team row counts were independently recomputed from the artifact rows
  in this review: every one of the 32 teams has exactly 17 rows (18-week
  window minus exactly one bye), confirming `544 = 32 × 17` and corroborating
  `byeWeeksHandled: true` without relying solely on the metadata's own claim.

Per `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §11, build success
and validation success are explicitly **not** governance signals by
themselves, and this review treats them only as evidence inputs, not as the
decision.

## 8. Source lineage summary

From `metadata.inputSources` (artifact) and the lineage manifest, both
re-read directly in this review:

| Source | Type | Retrieval | Package | Snapshot/retrieval time |
| --- | --- | --- | --- | --- |
| `nflverse-data:pbp/play_by_play_2024` | `nflverse` | `nflreadpy.load_pbp([2024])` | `nflreadpy` 0.1.5 | 2026-06-25T19:20:36Z |
| `nflverse-data:schedules/games` | `nflverse` | `nflreadpy.load_schedules([2024])` | `nflreadpy` 0.1.5 | 2026-06-25T19:20:50Z |

Both sources carry a `sourceUrlOrDatasetId`, a `transformCodePath`
(`scripts/build_team_week_raw_v0_2024_candidate.py`), and non-empty
`sourceRefs`, satisfying the §9 minimum metadata set in the preflight doc.
The manifest's own `governanceStatus`/`governanceSource` fields are
`ungoverned` / `not_set`, and its `notes` array states explicitly: "No
governed_real_data claim is made or implied by this manifest" and
"Promotion to governed status requires a separate, explicitly authorized
human review (PR D)." This review is that PR D.

## 9. Governance metadata review

Re-read directly from the candidate artifact's `metadata.governance` block
and the manifest:

- `metadata.governance.governanceStatus: "ungoverned"`
- `metadata.governance.governanceSource: "not_set"`
- `metadata.governance.notes: "No human promotion review has been performed. Build success and validation passing do not constitute governance."`
- Manifest: `governanceStatus: "ungoverned"`, `governanceSource: "not_set"`.

Per `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §11 and
`docs/data/team-week-raw-v0-2024-source-artifact-spec.md` §9, promotion to
`governed_real_data` requires an **explicit governance marker**
(`governanceSource: explicit_marker`-style value) set by a human promotion
review — never inferred from build success, validation passing, or a
plausible artifact path. No such marker exists in either the artifact or
the manifest as of this review. The artifact and manifest are internally
consistent with each other and with `provenanceStatus: partial_real_data`.

## 10. Search/check for hidden governed claims

This review grepped the full repository (not only the candidate's own
files) for `governed_real_data`, `governanceStatus`, and `governanceSource`
to check for any stray or premature governance claim outside the files
already reviewed above. Every match found is one of:

- A guardrail/negation statement (e.g. "must not be treated as
  `governed_real_data`", "No `governed_real_data` claim is made or implied",
  "never `governed_real_data` until all promotion criteria pass").
- A schema/vocabulary definition listing `governed_real_data` as one of five
  allowed enum values (`src/contracts/v1/teamWeekRawV0.ts`,
  `docs/contracts/team-week-raw-v0.md`) without applying it to this
  candidate.
- A test fixture (`tests/test_build_team_week_raw_v0_2024_candidate.py`)
  that sets `provenanceStatus = "governed_real_data"` deliberately to assert
  the build script's own guard **rejects** that value for a non-governed
  build (`scripts/build_team_week_raw_v0_2024_candidate.py` line ~820 asserts
  `provenance_status != "governed_real_data" and governance_status !=
  "governed"`), i.e. a regression test that a false governance claim cannot
  slip through, not an actual claim.
- The build script's own emitted provenance/governance notes (already
  covered in §7-9 above), which are negations.

**No hidden, implicit, or path-inferred `governed_real_data` claim was
found anywhere in the repository for this candidate.** Every reference to
`governed_real_data` found by this search is either a vocabulary
definition, an explicit denial, or a test that enforces the denial.

## 11. Pressure deferral finding

Two distinct facts must not be conflated, and this review states them
separately:

1. **Schema validity**: In `src/contracts/v1/teamWeekRawV0.ts`,
   `pressureRateAllowed: nullableNumberSchema` is `z.number().nullable()`
   **without** `.optional()`. This means the key must be present on every
   row, but `null` is an explicitly valid value for it. A row with
   `pressureRateAllowed: null` on every row **passes Zod schema validation
   cleanly** — there is no schema-level contradiction in the current
   candidate artifact.
2. **Governance rule (the actual blocker)**: Independent of schema
   validity, `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §8 states
   plainly: "Promotion to `governed_real_data`
   (TIBER-Data #162 governance section, TIBER-Teamstate #50 §5) is
   **blocked** while `pressureRateAllowed` remains a contractually-required
   field that is null-deferred for every row. This block is not lifted by
   documenting the deferral in a promotion record, by a plausible artifact
   path, by build success, or by passing validation... only un-deferring the
   field... or a formal contract revision can remove this block."

This review independently re-verified, by reading every row of the
candidate artifact, that **0 of 544 rows** have a non-null
`pressureRateAllowed` value — all 544 are explicit `null`. This matches
`metadata.deferredFields: ["pressureRateAllowed"]` and the corresponding
`deferredFieldReasons` entry ("no confirmed governed pressure-rate source as
of PR C preflight"), and matches the validation report's
`pressure_rate_allowed_null_and_deferred` check (`nonNullRows: []`).

**Finding**: the candidate artifact correctly implements the §8 deferral
(no invented pressure values, deferral recorded in metadata, validation
checks for it). But the §8 promotion **block itself remains in force**: it
is a locked governance rule, not a schema-parse failure, and it has not
been lifted by anything in #168 or by this review's own findings. Neither
of the two conditions that could lift it (an additional accepted
pressure-charting source, or a formal contract revision making the field
optional for this lane) has occurred. This review does not perform either
action — both are explicitly out of scope per the issue's hard guardrails
("do not weaken #166/#167 derivation rules", no contract revision is
authorized by this PR).

## 12. Sample row sanity summary

This review pulled a small cross-section of rows directly from the
committed artifact (not from any external source) to sanity-check that the
"real 2024 data" claim is plausible on its face:

| Team | Week | Opponent | pointsFor | pointsAgainst | offensivePlays | epaPerPlay | drives | redZoneTrips | redZoneTdRate | secondsPerPlay | pressureRateAllowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KC | 1 | BAL | 27 | 20 | 50 | 0.208 | 10 | 3 | 0.333 | 23.55 | null |
| DET | 1 | LAR | 26 | 20 | 61 | 0.106 | 11 | 4 | 0.5 | 24.39 | null |
| LAR | 5 | GB | 19 | 24 | 76 | -0.086 | 9 | 3 | 0.667 | 21.83 | null |
| SF | 18 | ARI | 24 | 47 | 73 | 0.009 | 12 | 3 | 0.667 | 21.31 | null |
| BUF | 9 | MIA | 30 | 27 | 59 | 0.151 | 8 | 4 | 0.5 | 24.24 | null |

Observations:

- KC 27–20 over BAL in Week 1 and DET 26–20 over LAR in Week 1 match the
  publicly known 2024 Week 1 results (Chiefs–Ravens Thursday opener;
  Lions–Rams Sunday opener), which is consistent with this being real 2024
  data rather than fixture/sample data.
- All rate/ratio fields fall within plausible bounds (`redZoneTdRate` in
  `0..1`, `secondsPerPlay` in a realistic ~20-25s/play range, `epaPerPlay`
  in a realistic small-magnitude range including negative values).
- `pressureRateAllowed` is `null` on every sampled row, consistent with the
  artifact-wide deferral confirmed in §11.
- No row in the sample (or in the full 544-row sweep performed for §7) shows
  an out-of-window week, a non-canonical team code, or an unmapped `LA`
  code — consistent with the `all_32_teams_present` /
  `valid_team_and_opponent_codes` checks.

This is a sanity spot-check, not an independent statistical audit of all
544 rows against an external dataset; it found no anomalies and no reason
to suspect a defect in #168's output.

## 13. Explicit promotion decision

**Decision: Do not promote.** The candidate remains `partial_real_data` /
`ungoverned`.

Of the three framed options:

- ~~Partial promotion only~~ — does not apply. The `team_week_raw_v0`
  contract's `provenanceStatus` enum
  (`fixture_scaffold | sample | partial_real_data | governed_real_data |
  unknown_provenance`) has no explicit governed-subset status (e.g. no
  "governed except pressure" value), and this review does not have
  authorization to invent one. The precondition for this option is not met.
- ~~Contract revision required before promotion~~ — not undertaken by this
  review. A contract revision (formally making `pressureRateAllowed`
  optional/non-blocking for this lane) is one of the two valid paths to
  eventually lift the §8 block, but deciding and making that revision is
  explicitly out of scope for a docs-only promotion review and is called
  out as a hard guardrail ("do not weaken #166/#167 derivation rules"). This
  review recommends it as a follow-up (§15) rather than performing it.
- **Do not promote (selected)** — the candidate artifact remains
  `partial_real_data` / `ungoverned` until `pressureRateAllowed` is sourced
  from an accepted provider or the contract is formally revised. This is
  the only option consistent with §8's explicit, locked block and with the
  absence of any hidden or implicit governance claim (§10).

This decision is reached because: (a) the §8 promotion block is locked and
explicitly states that documenting the deferral, build success, or
validation passing does not lift it; (b) no new pressure-rate source or
contract revision has occurred since #168; (c) no governance marker
(`governanceSource: explicit_marker`) exists in the artifact or manifest;
and (d) no evidence was found in this review that would justify overriding
the issue's preferred conservative outcome.

**No field of the candidate artifact, validation report, or manifest was
modified by this review.** This review is a decision record, not a build
step.

## 14. Allowed downstream posture for Teamstate

Per `docs/data/team-week-raw-v0-2024-source-artifact-spec.md` §10, Teamstate
consumption (PR E in that spec's PR sequence) is conditioned on "the
governed or explicitly allowed real source artifact." This review grants
the latter, narrowly:

- **Allowed**: TIBER-Teamstate may treat this artifact as an explicitly
  allowed `partial_real_data` / `ungoverned` **candidate** input — e.g. for
  wiring up a read-only adapter, schema-compliance testing, or non-production
  development against real-shaped 2024 data — provided Teamstate's own
  consumer code preserves and surfaces the `partial_real_data` /
  `ungoverned` status rather than re-labeling or hiding it, and does not
  treat `pressureRateAllowed: null` as a zero-pressure observation.
- **Not allowed**: Teamstate must not treat this artifact as `governed`,
  must not use it as the sole input to any production team-environment
  profile or scoring output that implies governed-data confidence, and must
  not silently backfill or estimate `pressureRateAllowed`.
- This review makes **no Teamstate code changes** and performs **no PPM
  work**; it only states the posture that a future, separately-scoped
  Teamstate-side change would need to honor.

## 15. Follow-up recommendation

1. Open a future, separately-scoped PR to either (a) identify and integrate
   an accepted pressure-charting source with its own source refs and
   retrieval metadata, un-deferring `pressureRateAllowed` per §8's first
   path, or (b) formally revise the `team_week_raw_v0` / PR A source
   contract to make `pressureRateAllowed` optional or otherwise non-blocking
   for this lane, per §8's second path. Either path requires its own
   explicit authorization and is not decided by this review.
2. Once either path lands, re-run a promotion review (a new PR D-style
   review, not a re-opening of this one) against the then-current candidate
   artifact before any `governed_real_data` claim is made.
3. Until then, any Teamstate-side consumption work should be scoped and
   reviewed against the posture in §14, not against an assumption of
   governance.
