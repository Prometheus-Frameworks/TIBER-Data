# Weekly intake and publication — 2026-09-14

Reviewed local preparation only. No remote publication, source admission, scheduler, merge or deployment.

## Result

- Repeatable bounded nflverse player/team and released-schedule CSV intake with release digests, fixed audited license bytes and immutable raw receipts.
- Offline publication requires exact committed source bytes. Fixture/demo flags and unsupported receipt families fail closed.
- Candidate-only revision inventory preserves old bytes. Actual repeated publication returned `unchanged`; correction and corruption tests pass.
- Latest current candidate: `3395a281e21b4db9947e6598a89cdeff5884d53358c66059b7b11267f6a6782a`. Source-support commits and all revision links are in the paired JSON.
- Current coverage: 15 of 16 scheduled games; missing `2026_01_DEN_KC`. Game finality remains unknown.

## Validation

28 Data tests passed. Same builder replayed all 18 completed-season 2025 REG weeks: 272 games, 18,522 identified source observations, schedule membership matched in every week. All 371 metric conflicts concern receiving air yards; all other selected field reconciliations matched. Current candidate has 20 air-yard conflicts. Consumer excludes air yards.

This is a raw weekly evidence replay, not a full Evidence Layer promotion declaration, fantasy scoring backtest, role/pace baseline or proof of historical pre-cutoff availability. The older no-schedule replay report remains an intermediate audit record; the schedule replay is the final bounded coverage check.

Independent review found receipt-lane, preview-provenance and offline-license P2 issues; all repaired and re-reviewed with no remaining material findings in scope. Final added intake/no-op and QB/provenance regressions passed after that focused review. The Fantasy integration reads 332 QB/RB/WR/TE observations as `preview_not_admitted`; runtime remains unavailable.

## Handoff

Follow `docs/contracts/weekly-boxscore-publication-candidate-v0.md` for commands and semantics. Data owns source facts and denominators. Fantasy's paired offline adapter owns generic full-PPR scoring and exploratory buckets. No current-team rewrite, route estimate, ownership/eligibility inference or transaction occurs.

Before users can see weekly evidence: accept exact source/artifact scope and limitations; implement/review a separately pinned admission/consumer activation; then UI and controlled refresh scheduling. A new revision never inherits acceptance automatically. Final-week labeling additionally requires final-status evidence or a separately reviewed explicit finality policy.
