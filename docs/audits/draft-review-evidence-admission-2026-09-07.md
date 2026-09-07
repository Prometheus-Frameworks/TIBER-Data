# Draft Review evidence admission proposal — 2026-09-07

**Recommendation:** accept four specifically enumerated identity mappings at
their existing `name_exact` / medium evidence tier, and permit a narrowly scoped
retrospective reader of the two pinned 2025 historical artifacts described below.
This is a prepared proposal. **No admission, promotion, merge or consumer
activation has occurred.** `consumer_allowed` remains false in the companion
[machine-readable proposal](draft-review-evidence-admission-2026-09-07.json).

Tracking: [Data #263](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/263)
and [Fantasy #360](https://github.com/Prometheus-Frameworks/TIBER-Fantasy/issues/360).
The operator authorized preparation and independent review of these dependencies
in the live Work conversation on September 7. This document records the agent's
preparation; it is not an operator-authored admission receipt. A clean review or
merging proposal documentation does not itself grant admission.

## Scope and ownership

This is a provenance/source audit and downstream handoff preparation under
[AGENTS.md](../../AGENTS.md), [TRUTH_SOURCES.md](../../TRUTH_SOURCES.md),
[Evidence Layer v0](../governance/evidence-layer-v0.md), and the
[cross-repository boundary doctrine](../repo-boundaries-and-feedback-loops.md).
Data owns the proposed identity and evidence-use boundary. Fantasy owns its
later request-bound reader, UI and operator context. Existing V1/V2 contracts
and all promoted/candidate/source data files remain unchanged. The audit JSON
version identifies this proposal format; it is not a new production contract.

The Data base is `6fd0754e74a63f940ae3fa74140715f1e03b4840`; the Fantasy base is
`8e2da54a572038d889d02c85fb5e84fad712aedb`. Both remote main refs were rechecked
on 2026-09-07 before preparation. Every inspected data input and relevant
producer/schema is SHA-256 pinned in the JSON. The checker reads these files
offline, emits an audit to stdout, and cannot perform promotion or activation.

## 1. Four proposed identity admissions

| Player | Sleeper ID | Proposed V2 GSIS | Method / confidence | 2025 historical team |
| --- | --- | --- | --- | --- |
| Jaylen Waddle | `7526` | `00-0036613` | `name_exact` / medium | MIA |
| Quinshon Judkins | `12512` | `00-0040784` | `name_exact` / medium | CLE |
| Cam Skattebo | `12481` | `00-0040715` | `name_exact` / medium | NYG |
| Chuba Hubbard | `7594` | `00-0036555` | `name_exact` / medium | CAR |

The four complete proposed records are nested under `identity.proposed_records`
in the JSON. They are derived from the existing candidate artifact using the
same row semantics as `scripts/promote_identity_crosswalk_rows.py`. No new
identity is minted, and no new name match is performed. These are V2's GSIS
vocabulary, not V1 slugs or a claim to resolve every TIBER identity namespace.

Checks against the exact committed artifacts establish:

- Each selected Sleeper ID and GSIS identifies exactly one candidate record.
- None collides in either direction with the existing 68 promoted V2 rows.
- None occurs in the committed conflict CSV by GSIS or matched provider ID.
- Each GSIS resolves one 2025 REG coverage row with agreeing position and ESPN
  evidence. Coverage itself has no Sleeper ID for these subjects.
- All four have null Sleeper-declared GSIS and ESPN fields. Their match tier
  must stay `name_exact`; admission cannot relabel them provider-verified.
- A virtual 72-row artifact, constructed only in a test, passes the unchanged
  V2 schema/validator. All existing promoted rows remain untouched.

The candidate's full generation clock is
`2026-08-08T18:17:13.819524+00:00`. Proposed V2 `source_updated_at` values retain
that **candidate-generation** time at the existing validator's second precision,
`2026-08-08T18:17:13Z`. They do not describe a Sleeper provider update. That
provider clock is unknown. Waddle's candidate team is DEN; that dated identity
context must not overwrite his historical MIA records or establish current
membership.

The original Sleeper dump hash is retained in the candidate's provenance, but
the raw dump is unavailable in this audit. Consequently the original full
normalized-name uniqueness census was **not rerun**. The committed candidate
and conflict artifacts are the evidence being reviewed. This limitation is
compatible with a deliberately accepted medium-confidence mapping; it is not
proof of an exact provider-ID agreement. The
[existing source audit](sleeper-players-endpoint-eligibility-2026-08-09.md)
permits only minimal identity evidence and requires operator promotion review;
it does not license a raw directory redistribution.

Zay Flowers (`9997` → `00-0039064`) is an already-promoted reference subject and
requires no new identity admission. No other candidate mapping is in scope.

## 2. Proposed historical consumer permission

| Exact existing input | SHA-256 | Total records | 2025 weeks 1–18 |
| --- | --- | ---: | ---: |
| `data/processed/evidence/player_weekly_usage_2025.source_backed.json` | `30a8e17370270e2fa5d055c7a771f19af2fe7bd89282cd2373f7704a492412cb` | 6,326 | 6,043 |
| `data/processed/evidence/player_weekly_ppr_outcomes_2025.source_backed.json` | `f241112115c9a625abead3410db89db6b4a8b603ce1dd663a45ff0697563e3a2` | 6,394 | 6,106 |

Both wrappers identify `nflreadpy.load_player_stats` and the committed producer.
The [usage source audit](../data/player-weekly-usage-source-audit-2025.md),
[usage lane](../data/player-weekly-usage-source-backed-2025.md),
[outcomes lane](../data/player-weekly-ppr-outcomes-source-backed-2025.md), and
[FORGE historical source plan](../forge-2025-ppr-source-artifact-plan.md)
establish existing source-backed lineage. Their presence is substantive evidence;
an absent legacy manifest does not erase it. Nevertheless the current canonical
weekly exports each contain only six explicitly labeled offline fixtures. This
proposal does not replace those exports or classify their rows as real.

The proposed permission is an explicit exception for **these exact processed
snapshot bytes**, consumed by Fantasy Draft Review for descriptive 2025
historical evidence. It is not a blanket admission of nflreadpy, a new source
ingest, a pipeline promotion, or permission to use a future changed file. The
later effective admission receipt must bind these hashes, this field/window
policy, approved identity version/hash, operator decision and independent review.

Allowed observations:

- From outcomes: targets, receptions, rushing attempts, receiving/rushing/
  passing yards and touchdowns, and interceptions, preserving null values.
- From usage: source-reported weekly target share and air-yards share. Negative
  air-yards share and values greater than one are valid in this snapshot and
  must not be clamped. Target share remains bounded to zero through one.
- Historical identity, team and opponent as source context, distinct from
  current Sleeper membership and eligibility. Display strings remain data.

Allowed derivations: deterministic count sums and explicitly named rates or
averages over the selected calendar window, only with complete required inputs
and disclosed nonnull denominators. A mean of weekly shares is an **average
weekly share**, not a season share. Partial sums must identify their supported
weeks and cannot masquerade as complete-season totals. Compare the same window
and show each player's recorded weeks; disclose a matched-week subset if used.

The usage producer has legacy missing-to-zero defaults for targets, receptions,
carries and air yards. Every usage key exists in outcomes, and the first three
counts agree exactly with the null-preserving outcomes lane. Use **outcomes**
as their consumer source. Air yards lacks this independent corroboration, so
**the entire air-yards-total field and its dependent aggregates are excluded**
from this first permission. The source-reported air-yards share has a separate
null-preserving mapping and remains eligible under the policy above.

Routes, participation, snaps, red-zone work, team carries and rush share remain
unavailable. No full league fantasy points or partial scoring subtotal is
granted: fumbles lost, sacks taken, two-point conversions and other components
are absent. The legacy PPR formula is not this league's scoring profile. No
ranking, forecast, regression probability, current role claim or transaction
authority follows from historical evidence.

## 3. Time, coverage and discrepancies

Only season 2025, weeks 1–18 is eligible. This is the existing documented
regular-season week boundary; `game_type` and `game_id` are absent from these
wrappers. Weeks 19–22 are excluded rather than presented as regular-season data.
Neither source has duplicate season/week/player keys. Missing weeks do not
establish byes, injuries, inactivity or zero usage.

Outcomes has 63 additional regular-season records without usage. Preserve
independently supported outcomes and return unavailable usage for these keys.
Nine regular-season joined records have conflicting position labels; the JSON
lists every one. The two sources agree on team/opponent and the shared counts.
A joined derivation must require exact season/week/GSIS identity and agreement
on context and position; conflict blocks the joined derivation without erasing
independent source observations. Do not silently choose a position or normalize
team aliases. None of the five acceptance subjects has a position discrepancy.

| Inspection subject | Recorded regular-season weeks | Historical team |
| --- | ---: | --- |
| Zay Flowers | 17 | BAL |
| Jaylen Waddle | 16 | MIA |
| Quinshon Judkins | 14 | CLE |
| Cam Skattebo | 8 | NYG |
| Chuba Hubbard | 15 | CAR |

These are diagnostic GSIS inspections; the four proposed identities are not
yet authorized roster attachments. They are recorded weeks, not certified
games played. The JSON preserves each actual week list.

Acquisition/publication/update clocks, original release bytes/hash and package
version are missing. Leave them null. The inspection date and git commit are
receipts for this retained snapshot, not substitutes for those clocks. The
proposed label is “2025 historical evidence from the pinned TIBER-Data snapshot.”
This supports retrospective description; it cannot prove what was knowable at
a 2025 decision cutoff or describe current 2026 usage/health/team state.

## 4. Public-use terms evidence and attribution

Primary terms documentation for the already-integrated provider was inspected
on **2026-09-07 UTC** as part of this permission proposal. No player dataset,
raw directory, new source feed or release asset was fetched in that check.

The [nflreadpy documentation](https://nflreadpy.nflverse.com/) identifies
nflverse-data as its stats source and describes most nflverse data as CC BY 4.0,
with an FTN exception and a July 2025 qualifier. The
[player-stats producer repository](https://github.com/nflverse/nflverse-pbp)
identifies its player-stats role and declares CC BY 4.0; the
[data repository](https://github.com/nflverse/nflverse-data) also declares that
license. These are data-source evidence, distinct from the loader's MIT software
license. This dated inspection does not recreate an original acquisition receipt.

**Assessment:** these primary declarations, together with the committed
`nflreadpy.load_player_stats` lineage, support proposing a CC BY 4.0 basis for
this limited historical stats use. This is an inference about the retained
snapshot's stated lineage, not an assertion that every nflverse dataset shares
the same rights. [nflreadr's terms](https://nflreadr.nflverse.com/) also retain
underlying owners' terms; any concrete contradictory source-specific terms
must block the affected public use rather than being overridden by this packet.

Following the [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/),
the later UI and copied agent packet must credit nflverse contributors, link
the source and license, identify TIBER's filtering/aggregation, preserve supplied
notices, and avoid implying endorsement or imposing additional restrictions on
the licensed material. A suitable source label is:

> Data: nflverse contributors (CC BY 4.0), accessed through nflreadpy; retained
> TIBER-Data 2025 snapshot. Filtered and summarized by TIBER; original source
> acquisition/update times unavailable.

Attach the exact source paths, commit and hashes as well. This proposed grant
excludes FTN, participation, snap/PFR, Fantasy Points, FFC ADP, player imagery
and raw Sleeper redistribution. New source bytes or a refresh require their own
scope and evidence; this receipt cannot authorize them automatically.

## 5. Verification and independent review

Reproduce without network or source-builder execution:

```sh
python scripts/audit_draft_review_evidence_admission.py --check
python -m pytest tests/test_draft_review_evidence_admission.py tests/test_identity_crosswalk_v2.py -q
```

The focused suite checks exact replay/inert status, proposed V2 row compatibility,
candidate/reverse/promoted/conflict-CSV collisions, canonical coverage mismatch,
byte drift, null versus zero, negative/above-one air-yards shares, missing usage,
position disagreement and duplicate weekly keys. The check is an audit utility;
it does not implement or certify the future public reader.

Audit triggers: identity semantics, source-use proposal, and downstream handoff.
An independent reviewer must inspect the resulting exact commit. Their durable
report and any repair/re-review results belong in the PR conversation. Builder
checks are not represented as independent review.

## 6. Smallest subsequent operator decision

The operator can accept or reject **these four medium-confidence edges** and
**the exact historical descriptive scope above**, citing the reviewed proposal
commit and source hashes. Acceptance would settle the evidence-use decision;
it would not merge a PR, deploy, assert implementation completion or authorize
other mappings/sources. Until that explicit decision exists, admission remains
null and Fantasy's four attachments remain blocked.

If accepted, the next mechanical change would prepare an additive V2 update
preserving all 68 existing records, pin the four-row selection and its receipt
so regeneration cannot remove it, and bind the later Fantasy consumer to the
accepted artifact and permission. The existing promoter selects only the old
FORGE/V1 cohort: rerunning it unchanged would omit these four rows. That is a
known implementation dependency, not something this audit silently repairs.
The original Fantasy slice remains authorized once its evidence dependencies
are effective. Any merge still needs its own explicit operator authorization;
this work retains **no merges and no production deployment**.
