# TIBER-Data Doctrine

> Core thesis: **Preserve contact with reality while increasing system autonomy.**

## Purpose

TIBER-Data is the canonical football data contract layer for the TIBER ecosystem. It defines the trusted schemas, source lineage, versioning, validation, and export expectations that downstream repositories use to build football intelligence.

This repository is not where downstream consumers should reinvent upstream logic, quietly reinterpret field meanings, or fill missing source truth with plausible-looking continuity. TIBER-Data exists so downstream repos, agents, models, interfaces, and future reasoning systems can consume trusted outputs instead of guessing what football reality means.

## Reasoning substrate

TIBER is evolving toward a governed reasoning environment for football intelligence.

Agents and models may reason, synthesize, simulate, rank, explain, and build interfaces. They may do more work with less direct human operation over time. But that autonomy only remains useful if it stays anchored to trusted, inspectable, versioned football reality.

The goal is not AI slop, opaque rankings, or confident downstream inventions. The goal is grounded autonomy: systems that can move faster and reason more deeply because the data substrate is explicit, governed, and auditable.

## Contract philosophy

Contracts are governance, not just schemas.

A useful TIBER-Data contract should make downstream guessing unnecessary. Every important field should carry, directly or through adjacent documentation:

- clear meaning
- type
- range or unit, where applicable
- source or provenance
- versioning expectations
- missing-value behavior

The governing rules are simple:

- No invented values.
- No silent assumptions.
- No downstream repo should be forced to guess what a field means.
- Breaking changes must be explicit and versioned.
- If source truth is missing, reduce scope rather than fabricating coverage.

A contract-safe artifact is allowed to be narrow. It is not allowed to be misleading.

## Inspectability requirements

If a model output, player grade, promoted lane, or signal changes, the system should make it possible to inspect why.

Preferred lineage shape:

```text
raw source → transform → validated artifact → model/output → downstream consumer
```

TIBER-Data should favor artifacts that are both machine-readable and human-auditable. A downstream system should be able to trace what it consumed, which transformation created it, which validation gate accepted it, and what versioned contract governed it.

## Ecosystem analogy

Use the job-site framing consistently:

- **TIBER-Data** = building code / canonical spec
- **TIBER-Teamstate** = environmental infrastructure
- **TIBER-FORGE** = fantasy signal/scoring engine
- **TIBER-Fantasy** = user-facing synthesis layer
- **Promoted lanes** = inspected/approved research surfaces
- **Agents** = operators/trades that must respect the spec

A trade can work quickly, but it cannot ignore the building code. A downstream model can reason creatively, but it cannot silently mutate the reality substrate.

## S-tier contract checklist

Before an artifact is treated as a serious cross-repo contract or promoted output, check for:

- canonical IDs
- explicit season and week scope
- source metadata
- `generated_at` timestamp
- model/version metadata where relevant
- confidence fields normalized consistently
- nulls for unknowns, never fake defaults
- schema validation before export
- compatibility expectations for downstream consumers
- clear deprecation path
- documented owner and purpose for important artifacts

## Engineering posture

TIBER-Data should remain boring in the best sense: deterministic, bounded, documented, contract-safe, and honest about source coverage.

Autonomy increases downstream only when this layer preserves contact with reality upstream.
