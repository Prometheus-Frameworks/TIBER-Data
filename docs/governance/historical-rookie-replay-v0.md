# Historical Rookie Replay v0 Governance

## 1) Purpose

Historical Rookie Replay v0 governs how TIBER evaluates rookie-thesis quality using a completed season before enabling live-season trust.

Working posture: **pretend it is 2025**, replay thesis inputs and weekly outcomes, and measure where expectations matched or diverged from completed reality.

For 2026 development, this replay is the gatekeeper layer before trusting 2026 live rookie tracking.

## 2) Doctrine

Historical Rookie Replay v0 follows these rules:

1. **Completed-season replay before live trust.**
   2025 replay validation is required before relying on 2026 live rookie evidence.
2. **Thesis and reality must be inspectable.**
   Pre-draft grade, post-draft context, expected role, and weekly outcomes must be present in canonical replay rows.
3. **No fake continuity.**
   Do not infer unsupported weeks, contexts, or coverage windows.
4. **Evidence status is explicit.**
   Each replay row must resolve to one allowed evidence status.
5. **Bounded v0 scope.**
   v0 defines governance and contracts only; no data fetch/scrape or downstream mutation.

## 3) Initial replay cohort (v0)

- Tetairoa McMillan → Carnell Tate archetype
- Ashton Jeanty → Jeremiyah Love archetype
- Emeka Egbuka → KC Concepcion archetype
- premium TE translation case
- Day 2 WR landing-spot elevation case

This cohort is a bounded validation slice, not a claim of full rookie-class coverage.

## 4) Canonical artifact ownership

- Canonical replay artifact target:
  - `exports/promoted/rookie-replay/historical_rookie_replay_v0.json`
- TIBER-Data owns this contract boundary and associated governance doctrine.
- Downstream repositories may consume promoted replay artifacts but must not invent missing replay evidence.

## 5) Evidence statuses

Each replay row must assign exactly one status:

- `supported`
- `partially_supported`
- `contradicted`
- `needs_verification`
- `stale_or_missing_data`

## 6) Replay evaluation flow (v0)

1. **Freeze replay scope**
   - replay season, cohort membership, and source boundaries.
2. **Attach thesis inputs**
   - pre-draft grade, archetype mapping, post-draft context tags, expected role.
3. **Attach completed outcomes**
   - weekly PPR series, season totals, games played, startable/spike/bust summaries.
4. **Evaluate materialization checks**
   - role, target-share, and environment support.
5. **Resolve evidence status**
   - assign one allowed status with notes/source provenance.
6. **Emit deterministic artifact rows**
   - include source labels and generated timestamp.

## 7) Promotion gate implication

Historical Rookie Replay v0 is a trust gate, not a dashboard feature.

If replay evidence is incomplete, stale, or contradictory at thesis level, 2026 live rookie tracking should remain unpromoted until bounded issues are resolved.

## 8) Non-goals (v0)

This governance phase does **not**:

- fetch data,
- scrape,
- generate artifacts in this PR,
- change fantasy scoring,
- modify downstream repositories.

## 9) Contract reference

Contract definition for this governance phase:

- `docs/contracts/history-rookie-replay-v0.md`
