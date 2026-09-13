# Nineteen historical Team identities — branch preparation, 2026-09-13

Task classes: data artifact and downstream handoff. TIBER-Data owns canonical
identity and source admission; Fantasy owns only the bounded descriptive transform.

Joe accepted the reviewed nineteen-edge proposal in the operator conversation
with “Okay sounds good”, following independent review and the explanation of
historical versus current teams. The separate receipt records that provenance
honestly: no GitHub operator comment URL or receipt timestamp is invented.
The acceptance covers this branch preparation and matching Fantasy integration
preparation. Merge and production release remain separate decisions.

## Evidence and change

The 75 baseline V2 rows are retained unchanged and exactly nineteen rows are
appended. All eight pinned evidence inputs retain their reviewed bytes (the
superseded crosswalk is read from the baseline commit). The previous four-row
and three-row receipts and archived proposals remain unchanged. No football
source was acquired, refreshed, inferred or reclassified by this implementation.

| Player | Sleeper ID | GSIS ID | Match / confidence | Recorded 2025 weeks | Historical team |
|---|---|---|---|---|---|
| Cedric Tillman | 10444 | 00-0038979 | name_exact / medium | 12 | CLE |
| Xavier Hutchinson | 10218 | 00-0038618 | name_exact / medium | 16 | HOU |
| Charlie Kolar | 8127 | 00-0038046 | name_exact / medium | 13 | BAL |
| Isaiah Davis | 11571 | 00-0039798 | name_exact / medium | 16 | NYJ |
| Ray Davis | 11575 | 00-0039875 | name_exact / medium | 17 | BUF |
| Dallas Goedert | 5022 | 00-0034351 | gsis_direct / high | 15 | PHI |
| David Montgomery | 5892 | 00-0035685 | gsis_direct / high | 17 | DET |
| Terry McLaurin | 5927 | 00-0035659 | gsis_direct / high | 10 | WAS |
| Tua Tagovailoa | 6768 | 00-0036212 | espn_bridge / high | 14 | MIA |
| Michael Pittman | 6819 | 00-0036252 | espn_bridge / high | 17 | IND |
| DeVonta Smith | 7525 | 00-0036912 | name_exact / medium | 17 | PHI |
| Alec Pierce | 8142 | 00-0037664 | name_exact / medium | 15 | IND |
| Garrett Wilson | 8146 | 00-0037740 | name_exact / medium | 7 | NYJ |
| Malik Willis | 8161 | 00-0038128 | name_exact / medium | 4 | GB |
| Tyjae Spears | 9508 | 00-0039032 | name_exact / medium | 13 | TEN |
| Tre Tucker | 10213 | 00-0038563 | name_exact / medium | 17 | LV |
| Devaughn Vele | 11834 | 00-0039424 | name_exact / medium | 9 | NO |
| George Holani | 12048 | 00-0039299 | name_exact / medium | 10 | SEA |
| Omarion Hampton | 12507 | 00-0040666 | name_exact / medium | 9 | LAC |

The raw candidate evidence is retained in the receipt. Fourteen name-only
matches remain medium; three direct GSIS and two ESPN bridge matches are high.
Montgomery and McLaurin's raw GSIS leading whitespace is retained, with trimming
used solely for agreement checks against the already-reviewed canonical IDs.
Candidate team and generation clock remain dated identity metadata. In particular,
Montgomery's historical DET and Pittman's historical IND records are not rewritten
as their current Sleeper teams. The V2 row `source_updated_at` is the candidate
construction clock, not a verified provider update time.

The cohort has 248 observations in each weekly lane. The 94 unrecorded calendar
slots remain unknown; nine observations beyond week 18 per lane remain excluded.
Recorded weeks are not certified games played. The receipt retains per-field
nonnull denominators and observed zero weeks. No current roles, health, roster
eligibility, points, rankings, regression probabilities or forecasts are created.

Antonio Williams / 13301 remains outside the approved cohort. The manager's rookie
context is recorded as such; no 2025 NFL history or identity is manufactured.
Roster membership, ownership, injury pressure and manager cut decisions are not
settled by this admission.

## Validation and review boundary

94 focused tests passed across the new admission, prior admissions/proposals and
V2 schema suites. Deterministic replay and optimized CLI replay passed. The old
materializer now refuses both CLI modes while the newer receipt exists, so it
cannot drop nineteen accepted rows. Its importable function still replays the
archived 75-row stage. Receipt, source, edge, confidence, scope and release-authority
mutations fail closed; the original 75 rows remain identical.

The initial legacy-test runs were blocked by missing objects in the shallow
checkout. Exact historical repository objects were restored before the passing
run. Dependencies were installed in a local test-only target; no repository
dependency changed. No new football data acquisition occurred.

The paired JSON is a **builder mechanical audit**, not independent implementation
review. The earlier independent review found no material issues in the source
proposal; its immutable proposal and review hashes are retained. It does not
certify these implementation changes. Independent implementation review is pending.

## Replay and handoff

```sh
python scripts/materialize_team_roster_identity_admission.py --check
python scripts/promote_identity_crosswalk_rows.py --check
python -m pytest -q tests/test_team_roster_identity_admission.py tests/test_team_identity_admission.py tests/test_draft_review_admitted_identity.py tests/test_team_identity_proposal.py tests/test_draft_review_evidence_admission.py tests/test_identity_crosswalk_v2.py
```

A checkout needs the historical Git objects referenced by the earlier admission
replays. The new materializer disables lazy Git fetching and checks current input
hashes before writing. Consumer work must pin the resulting Data commit and both
new artifact hashes; the existing 75 consumer profiles must remain identical.
No merge, production release or fantasy transaction has been performed.

Historical source attribution: [nflverse contributors](https://github.com/nflverse/nflverse-pbp),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). TIBER filters the existing
2025 regular-season window and aggregates recorded observations. No endorsement
is implied. The retained terms assessment is dated 2026-09-07; original acquisition
terms receipt, source acquisition/update clocks, release hash and package version
remain unavailable. No new terms assessment occurred.
