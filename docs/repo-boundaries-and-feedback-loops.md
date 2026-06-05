# TIBER-Data Repo Boundaries and Feedback Loops

## Purpose

This document defines boundary doctrine for how TIBER repositories can influence each other without creating recursive, self-reinforcing loops.

TIBER-Data owns canonical contracts, schema semantics, provenance expectations, and cross-repo language. TIBER-Data does **not** own final player opinions, product rankings, or promotion decisions.

## Anti-recursion rule (non-negotiable)

**No repo should be allowed to use its own downstream output as upstream truth.**

This rule is mandatory across the TIBERverse. It prevents a model opinion from being treated as evidence and then reused to justify the next model opinion.

If a downstream output is ever reused upstream, it is invalid **unless** it has been converted into a new source-backed artifact with independent provenance and explicit contract semantics.

## Layer definitions

### 1) Reality / friction layers

Reality/friction layers represent observed football context or source-grounded artifacts.

Examples include:

- TeamState inputs and environment context
- Role & Opportunity source-grounded signals
- Rookies/prospect context with explicit provenance
- Verified TIBER-Data artifacts and governed contracts

Requirements for this layer:

- preserve provenance and source attribution
- preserve uncertainty and support limits
- avoid fabricated continuity when support is missing
- keep contracts deterministic and bounded

### 2) Projection / incentive layers

Projection/incentive layers transform upstream context into expected outcomes.

Example:

- Point Prediction Model

These outputs are useful, but they are not raw evidence. They are derived opinions conditioned on assumptions, objective functions, and modeling choices.

Requirements for this layer:

- treat projections as derived signals, not source truth
- retain clear lineage to upstream inputs
- never relabel projection outputs as source-grounded facts

### 3) Adjudication / grading layers

Adjudication/grading layers combine multiple signals to produce a stronger final opinion.

Example:

- FORGE

FORGE should resolve disagreement between upstream signals and operate as an explicit arbitration layer. It must not blindly echo one repo's output or collapse multi-signal adjudication into model-copy behavior.

Requirements for this layer:

- require multi-signal reasoning and conflict resolution
- preserve traceability of which inputs influenced final grades
- reject circular evidence paths

### 4) Product / decision surfaces

Product/decision surfaces expose conclusions to users or agents.

Examples:

- TIBER-Fantasy promoted lanes
- comparison endpoints
- rankings and trade tools

Product surfaces should display conclusions, confidence, and supporting evidence. By default, they do **not** become new upstream evidence.

Requirements for this layer:

- surface decision outputs with confidence and support context
- separate presentation artifacts from canonical evidence artifacts
- block automatic feedback of product outputs into upstream modeling inputs

## Loop validity examples

### Good loop (valid)

TeamState + Role & Opportunity + Rookies + TIBER-Data contracts
→ Point Prediction
→ FORGE adjudication
→ TIBER-Fantasy product surface
→ human/operator review

Why valid:

- upstream source-grounded layers feed downstream derived layers
- adjudication remains a separate function from raw evidence capture
- human/operator review provides governance before any policy changes
- no downstream output is automatically promoted to upstream truth

### Bad loop (invalid by default)

Point Prediction likes player
→ FORGE boosts player
→ TIBER-Fantasy promotes player
→ future Point Prediction/Role & Opportunity logic treats that promotion as evidence

Why invalid:

- downstream conclusion is being recycled as upstream evidence
- system loses contact with source-grounded football reality
- repeated recursion can amplify initial model bias into false certainty

Exception path:

- only permissible if the downstream result is converted into a **new, source-backed artifact** with independent provenance, explicit contract meaning, and governed ingestion rules

## Ownership and scope in TIBER-Data

TIBER-Data is responsible for:

- canonical contract definitions
- schema semantics and validation boundaries
- provenance expectations and support-window honesty
- shared cross-repo data language

TIBER-Data is not responsible for:

- final player takes or rankings
- product promotion policy
- model-specific scoring logic in downstream repos

## Implementation guidance for agents and repo maintainers

When adding or revising integrations:

1. classify each input/output by layer (reality, projection, adjudication, product)
2. verify that all upstream truth claims are source-backed and provenance-labeled
3. fail closed when support is missing; do not infer continuity
4. block any path where a product or downstream model output is reused as upstream evidence without governed conversion
5. document any sanctioned exception with contract shape, provenance requirements, and review owner

If source truth is missing, reduce scope.
