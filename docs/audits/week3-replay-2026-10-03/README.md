# Week 3 provenance repair — fresh retained-byte replay

Joe's October 3 instruction to unblock the Vikings target-allocation research authorizes bounded blocker repair. This is a provenance/source audit and downstream handoff preparation, not source admission or a football producer run.

The accessible committed audit and issue records contain no original generation witness for candidate `f3366ac1c2192641c6e94ba7c756ed2e12ba73b37550619ae143deaeab9f9902`. No original executor storage was found in this workspace. This does not prove the witness is absent from all environments. Its original generation time remains unknown.

## New evidence

The adjacent build receipt witnesses **a new offline replay and isolated materialization on October 3**, using the unchanged #273 implementation and original #277 retained raw support. It is explicitly not a recovered September 30 clock. A new temporary revision stream returned `candidate_revision_written`; its bytes equaled the selected candidate. Repeated publication was unchanged; a second build was byte-identical. No repository candidate, index, raw receipt or current pointer was changed.

`manifest.json` binds all 13 dependencies: player/team/schedule source files and receipts, both license files, candidate/index, and all four intake/build/publish implementation files. Every member was compared to its exact Git revision. The publisher independently compares each raw member to support commit `2b58e2c22ccd2430041afcfbd143b057830878f0`, which remains an ancestor of #277 head `eac3b9bc22cf1fa230b233a09f5e031a2a9b409a`. There was no provider retrieval.

The receipt's `build_completed_at` may be proposed as the generation time of this **freshly materialized instance**. Review and explicit downstream adoption must preserve that meaning. It must never be described as the original candidate's generation time, a pregame availability clock, finality proof or source-use acceptance.

## Verification

Run from a complete checkout containing the selected #277 ancestry:

```sh
python docs/audits/week3-replay-witness-2026-10-03.py --output-dir /tmp/tiber-week3-replay-independent
python -m unittest discover -s tests -p 'test_weekly_publication_v0.py' -q
python -m unittest discover -s tests -p 'test_weekly_boxscore_candidate_v0.py' -q
```

The output directory must not already exist. Fresh run clocks differ; candidate/member identities must not. Implementer results: 22 publication tests and 18 boxscore tests passed. No full-suite result is claimed. The publication suite intentionally tests a missing Git object and prints its expected diagnostic.

## What remains

Independent review of this exact repair and its replay semantics is pending. A complete downstream retained input/review binding still needs the reviewed repair identity; ROP's real Week 3 selector remains closed. The Teamstate shape inspector remains unadmitted. No ROP, Teamstate or Role State output was run.

Vikings research needs a separately identified cohort and purpose: full-game credited targets can be inspected after qualification, but post-Jefferson targets need an authenticated play-by-play window and exit boundary. Snaps/routes require their own permitted witnesses. This weekly candidate cannot supply those missing fields.

Any future #277 merge must preserve source ancestry through a normal merge commit. Source admission, purpose acceptance, real producer execution, cohort activation, Forecast, runtime, merge and deployment are not performed by this repair. Candidate finality remains unknown, corrections open and receiving-air-yard conflicts excluded.

## Handoff

Files touched: this audit directory and the adjacent read-only replay audit script. Now true: a truthful new replay witness and complete member manifest exist. Still missing: independent exact-repair review and downstream adoption/purpose binding. Must not assume: replay recovers original time or establishes post-exit allocation. Audit trigger: independent audit pending.
