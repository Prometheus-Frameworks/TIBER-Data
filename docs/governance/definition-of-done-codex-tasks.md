# Definition of Done — Codex Tasks (TIBER)

A task is complete only when all items below are satisfied.

## 1) Boundary integrity

- Source-of-truth inputs are named explicitly.
- Any missing support is declared explicitly.
- Scope is reduced when support is missing.

## 2) Contract safety

- No silent schema/contract drift.
- Any contract change is intentional and documented.

## 3) Deterministic implementation

- Scripted generation path is documented.
- Artifacts are reproducible from committed scripts and inputs.

## 4) Validation

- `scripts/pre_pr.sh` passes.
- Task-specific checks (if any) are run and logged.

## 5) Honest handoff

- PR summary states:
  - what changed,
  - what source supports it,
  - what remains unsupported,
  - and explicit non-goals.
