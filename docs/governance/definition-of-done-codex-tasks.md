# Definition of Done — Codex Tasks

A Codex task is done only when all criteria below are met.

## Done criteria
- Change is **deterministic** and reproducible.
- Change is **bounded** to approved scope.
- Change is **contract-safe** (no silent schema drift).
- Change is **honest about source coverage** (no fabricated continuity).
- Required validation checks are executed and recorded.
- Handoff includes explicit boundary notes for missing inputs.

## Not done
Any of the following means the task is not done:
- Unsupported data windows were implied or extended.
- Representative rows were created without true source rows.
- Validation failures were ignored or undocumented.
- Repo-purpose boundaries were reinterpreted without approval.
