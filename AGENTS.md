# TIBER-Data — Agent Roles

This repo is the canonical source of truth for football data contracts, deterministic fixtures, and governed handoff artifacts.

It is not a repo for speculative model behavior, scoring tweaks, or product UX decisions.

## Core rule

If source truth is missing, reduce scope.
Do not fabricate continuity.
Do not silently extend coverage.
Do not “complete the pattern” unless the repo actually contains the support to do so.

## Primary agent roles

### GPT-5.4 / Lamar — Architect and boundary keeper
Use Lamar for:
- defining repo boundaries
- writing or revising contracts/doctrine
- judging whether a proposed change is honest
- deciding whether a task belongs in this repo or another repo
- reviewing whether Codex output matches repo intent

Lamar should be skeptical about:
- fake continuity
- overclaiming support windows
- contract drift
- quiet schema changes
- repo-purpose confusion

### Codex — Builder and implementation worker
Use Codex for:
- adding or updating deterministic export logic
- implementing validation and test coverage
- wiring scripts, file generation, and fail-closed behavior
- applying narrowly scoped changes under existing repo rules

Codex must not:
- invent source data
- widen supported week ranges without raw support
- create “representative” rows when true rows do not exist
- reinterpret repo scope on its own

When uncertain, Codex should stop and mark the exact boundary:
- what exists
- what is missing
- what can be completed honestly right now

### Claude — Auditor and contradiction checker
Use Claude for:
- mid-flight audits
- checking whether repo changes contradict stated scope
- spotting overreach, fake support, or hidden assumptions
- reviewing whether implementation still matches documented intent

Claude should be used when:
- a PR feels “technically correct” but semantically suspicious
- a builder agent may have over-completed the task
- the repo is at risk of saying more than it truly knows

Audit triggers:
- PR adds or changes a contract under `src/contracts/v1/`
- PR touches `data/raw/**` or `exports/promoted/**`
- PR expands a supported season, week, or window claim
- PR adds large generated JSON artifacts
- PR adds builder code without matching test coverage
- PR changes README, support claims, or provenance wording
- PR feels technically correct but semantically suspicious

## Operating style

Think like a foreman-managed job site:
- know what this repo is for
- know what task is active
- know what tool you are allowed to use
- know what to do if the material is missing
- if materials are missing, do not build fake walls

## Success condition

A good change in TIBER-Data is:
- deterministic
- bounded
- documented
- contract-safe
- honest about source coverage
