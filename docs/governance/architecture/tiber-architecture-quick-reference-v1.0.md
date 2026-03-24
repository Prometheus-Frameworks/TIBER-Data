# TIBER Architecture Quick Reference v1.0

> Status: Active governance document (approved)
>
> Canonical source: `TIBER-Data/docs/governance/architecture/tiber-architecture-quick-reference-v1.0.md`

## Purpose

This is the concise reference for the approved TIBER architecture doctrine.
For full detail, use the canonical architecture document:

- `docs/governance/architecture/tiber-architecture-document-v1.0.md`

## Canonical governance home

**TIBER-Data** is the canonical home for architecture governance documents and cross-repo contract authority.

Other repositories should reference these canonical files and avoid maintaining divergent copies.

## Repository responsibilities at a glance

- **TIBER-Data**: canonical contracts + governance docs
- **TIBER-Fantasy**: downstream product/application consumer
- **TIBER-FORGE**: downstream engineering/integration workspace
- **Point-Prediction-Model**: point-prediction outputs
- **Role-and-Opportunity-Model**: role/opportunity outputs
- **Signal-Validation-Model**: signal validation outputs
- **Age-Curve-Intelligence-Model**: age-curve intelligence outputs
- **ARC**: participating downstream ecosystem repo

## Core rules

1. Canonical contract and governance authority is centralized in TIBER-Data.
2. Cross-repo interfaces are versioned and explicit.
3. Governance docs are referenced from TIBER-Data, not duplicated downstream.
4. Implementation can vary by repo, but must respect canonical interfaces.

Concrete contract reference in this repo: `src/contracts/v1/index.ts`.

## Governance document versioning note

- Major = breaking governance change
- Minor = additive/clarifying governance change
- Patch/editorial = non-doctrinal wording fixes

Current quick reference version: **v1.0**.
