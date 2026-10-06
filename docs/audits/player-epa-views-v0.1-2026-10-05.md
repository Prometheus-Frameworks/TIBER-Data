# Independent archival audit: Player EPA Views v0.1

Disposition: **CLEAN WITH NON-BLOCKING NOTES — archival-only**. The frozen offline package has no identified blocker to its bounded archival retention. This audit is not source-purpose admission, merge authorization, producer acceptance or consumer integration approval. The PR remains unmerged and requires a separate independent review of its final exact commit.

## Independence and binding

A separate auditor agent inspected the repaired package read-only, compared it with the original extraction, reconciled every generated observation directly with the retained CSV without importing the builder, and ran the supplied verification and regression checks. Only this paired audit record was written by the auditor. Audit task class: provenance/source audit under `AGENTS.md`.

Original PR head: `128a45feec7782bb57d6b4dc563409e0197549ca`.
Original archive SHA-256: `a1bd69ce45848339101594a705b5a034b4e67249521a1ad9ac509e2a03d179b2`.
Audited repair archive SHA-256: `4410b0bb78ddd589099654c3869c0b941c1b024caf7262e65f91bf602afa1990` (416,857 bytes).
Final repository README SHA-256: `6581a6c8707f589737628fa0c82f1db9b897fe3a998875845de151b925d2da3c`. Its original-package review statement and later archival-audit status are distinguished and consistent.
The archive manifest's member hashes bind the content. This avoids a self-referential commit claim; the final commit and updated handoff wording receive separate exact-head review.

Governance read: `AGENTS.md`, `TRUTH_SOURCES.md`, `docs/governance/evidence-layer-v0.md`, and `docs/governance/cross-repo-governance-v0.md`. The classification inherits data-artifact and downstream-handoff constraints while authorizing no new acquisition or integration.

## Independent checks and results

- ZIP CRC, archive SHA-256, and every manifest-listed member size/hash: pass.
- Source CSV, original provenance, builder and all three JSON goldens compared against the original package: byte-for-byte unchanged.
- CSV SHA-256: `27a8a464687901340e87873010b3583443619fad723db828f745f71c8086ec9e`; 1,950,079 bytes, 4,379 rows, no duplicate season/type/week/game/team/player keys.
- Independent all-record reconciliation: source identity/team grouping, row counts, observed weeks/game IDs, summed EPA, matching counts, ratios, missingness and QB unavailability all pass. No names are used as join keys; event teams stay separate. Selected identities are nonempty.
- `python verify_player_views.py`: pass. It checks golden digests before a fresh temporary build and comparison.
- `python test_golden_boundary.py`: one regression passes. It verifies clean reproduction, changes builder coverage semantics in a temporary copy, reproduces to a separate output directory, detects golden mismatch, proves golden hashes unchanged, then independently detects a deliberately overwritten golden by manifest digest.

| View | Selected source rows | Output records | Available | Missing operand | Other unavailable |
| --- | ---: | ---: | ---: | ---: | ---: |
| RB EPA/carry | 360 | 478 | 371 | 107 | 0 |
| Receiver EPA/target | 1,282 | 1,715 | 1,292 | 420 | 3 zero denominators |
| QB EPA/dropback | 144 | 195 | 0 | 0 | 195 missing full population |

These counts include player-game and player-team observed-window grains. Rates divide summed unrounded EPA by summed matching counts. Missing operands withhold the aggregate; zero denominators withhold the rate. Negative EPA and actual zero EPA remain valid. Receiving selection includes source RB/WR/TE plus other positions with positive credited targets. Source passing context is not relabeled as full dropback EPA.

| Requested week | Source rows | Observed game IDs |
| --- | ---: | ---: |
| 1 | 1,118 | 16 |
| 2 | 1,107 | 16 |
| 3 | 1,114 | 16 |
| 4 | 1,040 | 15 |

Week 4 lacks ATL–NO. Counts are observed snapshot coverage, not schedule-finality evidence. Output metadata consistently marks partial W4, unknown game finality and no full-week-final certification. Absent rows do not establish zero, DNP, bye, current eligibility or complete player-season coverage.

## Rights and provenance disposition

Classification: `external_candidate`, retained only as an already-authorized offline archive. Existing repository evidence supplies a rights basis for this source family: `data/raw/weekly_boxscore/2026_w01_20260914/receipt.json` names the exact same nflverse-data weekly 2026 player release URL, attributes nflverse contributors and links retained CC BY 4.0 license bytes. The auditor verified `LICENSE.md` SHA-256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`. This is a September receipt for a distinct revision, not an October acquisition receipt. The archive's source URL, attribution, license link and no-endorsement statement remain visible; derived values and builder are clearly identified as changes.

That local first-party source-family evidence supports bounded archival retention; it does not grant blanket rights to other nflverse products or settle future acquisition/current terms. No new source or terms acquisition occurred during the audit. The specific retained comparison receipt cited in original provenance was not recovered as a full October acquisition receipt; its recorded remote metadata match is preserved as an original claim, not retroactively upgraded to an independent witness.

The CSV bytes and internal numerical fidelity are independently verified. Remote asset ID `612530012`, release update `2026-10-05T12:33:41Z`, original release-digest match, W1–W3 prior-snapshot comparison and NGS summary remain historical provenance assertions. They were not re-fetched or independently recomputed here. Original retrieval time remains unknown. Package generation, repair recording and ZIP serialization clocks cannot substitute for source retrieval or historical pre-cutoff availability.

## Unresolved boundaries and handoff

Source IDs and position labels remain source namespaces, not new canonical identity/crosswalk admissions or cutoff-effective roster records. Source aggregate arithmetic is confirmed; custom play exclusions, upstream EPA model semantics and player causal contribution are not reconstructed. The source official-definition link is a reference, not a newly witnessed play-level definition audit. Full QB dropback EPA remains unavailable until a separately qualified population and consistent `epa`/`qb_epa` definition exist.

No producer pointer, ROP/Teamstate/Forecast integration, source promotion, runtime, deployment, schedule or additional acquisition is introduced. The archived builder remains an offline prototype. Existing Data weekly candidate receipts and Research #28 ownership boundaries remain separate.

Now true: required independent semantic/contradiction audit exists for the exact repaired archive, with full-population numerical reconciliation and a rights-evidence disposition. Still missing: final exact-head review, any future source-purpose acceptance, full QB population/definition, full W4 finality and consumer acceptance. Must not be assumed: archival preservation certifies latest NFL data, contemporaneous forecasting availability, governed truth, or any operational activation.

The original manifest's `independent_review: not_performed` records the original package's state; the later repair explicitly points to separate repository audit records. It is not rewritten into a fabricated historical review. Audit-trigger status is **audit completed for archival scope** once this paired record is committed. Operator keeps final merge authority; this task explicitly stops before merge.
