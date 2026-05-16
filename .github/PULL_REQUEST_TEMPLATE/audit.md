# Claude Audit Checklist

Use this checklist when a TIBER-Data change may need contradiction review.

## Audit triggers

- [ ] PR adds or changes a contract under `src/contracts/v1/`
- [ ] PR touches `data/raw/**` or `exports/promoted/**`
- [ ] PR expands a supported season, week, or window claim
- [ ] PR adds large generated JSON artifacts
- [ ] PR adds builder code without matching test coverage
- [ ] PR changes README, support claims, or provenance wording
- [ ] PR feels technically correct but semantically suspicious

## Audit status

- [ ] No audit trigger fired
- [ ] Claude audit happened
- [ ] Claude audit is pending
- [ ] Claude audit was skipped with reason:

## Boundary check

- [ ] Change remains deterministic, bounded, documented, contract-safe, and honest about source coverage
- [ ] No data contracts or artifacts were changed unless explicitly in scope
