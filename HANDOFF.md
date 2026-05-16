# TIBER-Data — Working Handoff

## Repo purpose in one sentence

TIBER-Data stores canonical contracts and deterministic football data artifacts for downstream repos.

## Current agent workflow

Typical loop:
1. Lamar defines scope and boundary
2. Codex implements the narrow change
3. Claude audits when needed
4. merge only if the repo remains honest

## When a task arrives

Ask:
1. Is this a contract task, a data artifact task, or a repo-governance task?
2. Does this repo already hold the source truth needed?
3. If not, should scope be reduced or should the task move elsewhere?

## If a mistake or uncertainty appears

First call:
- README
- contracts
- export code
- tests
- committed raw support files

If still unclear:
- Lamar decides whether the task is honest
- Claude audits if a builder may have overreached

## Handoff note format

Every material handoff should state:
- active task
- files touched
- audit-trigger status: not triggered, Claude audit happened, Claude audit pending, or Claude audit skipped with reason
- what is now true
- what is still missing
- what must not be assumed

Example:
- Active task: extend supported weekly artifact generation
- Files touched: raw support fixtures, export validation, tests, README
- Now true: W1–W6 supported and fail-closed
- Missing: honest raw support beyond W6
- Must not assume: W7+ exists unless committed support is present
