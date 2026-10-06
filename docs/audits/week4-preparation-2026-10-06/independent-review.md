# Independent Week 4 Data review — PR #281

Disposition: **CLEAN WITH NON-BLOCKING NOTES**. No actionable findings.

Reviewer: independent Codex sub-agent `/root/week4_data_review`, separate from the packet author. Review completed: `2026-10-06T11:43:10.583805+00:00`.

Reviewed exact head: `ca31f5052061e854b3df8ad46e555506f1f7712d`. Reviewed tree: `7d3f8a4c2ce889258fa6be9eea48c5274c577012`. GitHub PR metadata independently confirmed this head and the 15-file change against base `0d9f82a8d0225602faea4887adf314983ee25a3a` before review.

Candidate: `307204e4c8123e8b1f66d8dabbacfb5310ad84b72abfa935b15f0fd4e5016de9`. Source and schedule support: `0f99ff5a2293044c41d5de3c2601c02baa6e9daf`.

## Evidence and checks

Read AGENTS.md and TRUTH_SOURCES.md; classified this as provenance/source audit and downstream handoff review. A separate no-hardlink clone kept the reviewed tree unchanged. All 13 inventory members' byte sizes, SHA-256 hashes, Git blob IDs and exact support-commit contents matched. The seven raw support members, fixed CC BY 4.0 license, attribution, source URLs, receipt semantics and chronological acquisition/build witnesses were inspected. The intake/build/publication code is unchanged from the pinned implementation base.

The unchanged offline Data preparation reproduced the complete candidate byte-for-byte into a separate scratch directory. No reviewed golden or raw input was overwritten. Reproduction occurred `2026-10-06T11:42:34.803870+00:00` through `2026-10-06T11:42:35.031056+00:00`.

Independent CSV inspection confirmed 1,110 scope rows, 1,109 resolved native players, one anonymous source observation, 32 unique reciprocal team-game rows and 16 games exactly matching pinned schedule membership. Every candidate source-row identity and observed field was checked against its CSV source row. All carry and credited-target sums matched team denominators, including the anonymous row. All other reconciliation fields matched except the recorded 22 receiving-air-yard conflicts. The proposed native shortlist rows match exactly; this does not qualify the Sleeper join.

Tests: **40 passed, 33 subtests passed**. Reviewed clone status remained clean.

## Non-blocking notes and remaining gates

- Receiving air yards must remain excluded from first consumer use; no source conflict was rewritten.
- Anonymous evidence contributes to denominators but creates no player identity. Source population is not an active-roster census.
- Sleeper/native mappings remain unadmitted proposals; Tre Harris alias verification and current selected-cohort confirmation remain separate.
- This review authenticates retained bytes and recorded witness chronology. It does not claim independent observation of the original build, fresh provider metadata verification, or historical pre-cutoff availability.
- Schedule membership is complete; finality remains unknown and full_week_final stays false.

The Data packet is suitable for the next bounded producer-binding preparation and later explicit source/purpose acceptance review. This review is not admission or an execution grant. No provider acquisition, ROP/TTS real-input invocation, merge, deployment, Site update or repository write occurred. Paired machine record: `independent-review.json`.
