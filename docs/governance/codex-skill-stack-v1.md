# Codex Skill Stack v1 (TIBER)

This document defines a minimal, high-signal skill stack for Codex in TIBER repos.

It is designed for deterministic delivery, explicit boundaries, and low operator overhead.

## Scope

- Applies to implementation agents operating in this repository.
- Focuses on repeatable execution, not speculative behavior.
- Defers any unsupported source windows rather than inferring continuity.

## Skill 1 — `tiber-boundary-check`

Use before coding.

### Required prompts/checks

1. What exact source-of-truth files support this change?
2. What boundary is explicitly unsupported today?
3. What scope reduction is required if support is missing?

### Hard-stop triggers

- No source-backed artifact exists for a requested season/week/window.
- Requested change expands support claim without matching raw support.
- Contract/schema shape changes without explicit approval in task scope.

### Required output

- `Exists:` list of concrete files/artifacts that support the change.
- `Missing:` list of inputs required for broader scope.
- `Honest-now:` smallest complete change possible now.

## Skill 2 — `tiber-data-change-playbook`

Use for data-contract and export updates.

### Standard sequence

1. Run boundary check.
2. Identify script(s) or builder path to edit.
3. Add or update deterministic validation.
4. Regenerate affected artifact(s) only.
5. Run diff checks and tests.
6. Document exact supported boundary in PR notes.

### Mandatory no-go behavior

- Do not create representative rows when true rows are absent.
- Do not widen season/week coverage unless raw support exists.
- Do not silently add contract fields.

## Skill 3 — `tiber-pr-writer`

Use after checks pass.

### Title guidance

- `feat(data): ...` for additive source-backed artifacts.
- `fix(export): ...` for deterministic export corrections.
- `docs(governance): ...` for policy/process only.
- `test(validate): ...` for validation/test expansion.

### PR body sections

1. **Source of truth** — files and provenance used.
2. **Determinism** — scripts/commands run and reproducibility statement.
3. **Boundary statement** — what is supported vs unsupported after this PR.
4. **Validation** — tests/checks executed.
5. **Non-goals** — what this PR intentionally does not do.

## Operator rollout (solo-friendly)

1. Install/use these three skills first.
2. Wire `scripts/pre_pr.sh` as a default pre-commit check path.
3. Expand only after 2–3 weeks of stable usage.

## Success criteria

A successful Codex run under this stack is:

- deterministic,
- bounded,
- test-validated,
- explicit about missing source truth,
- and aligned with repo contracts.
