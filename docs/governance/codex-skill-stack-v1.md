# Codex Skill Stack v1

## Purpose
Define the minimum Codex capability stack for deterministic, contract-safe work in TIBER-Data.

## Required stack
1. **Contract awareness**
   - Reads existing contracts before editing exporters or artifacts.
   - Fails closed when contract support is missing.
2. **Deterministic builder behavior**
   - Uses reproducible inputs and stable generation paths.
   - Avoids speculative backfills or inferred continuity.
3. **Validation-first execution**
   - Runs repo pre-PR checks before handoff.
   - Treats failed checks as blocking.
4. **Scope discipline**
   - Restricts changes to task-defined boundaries.
   - Escalates missing source truth instead of widening coverage.

## Non-goals
- This document does not define product UX policy.
- This document does not authorize schema expansion.
