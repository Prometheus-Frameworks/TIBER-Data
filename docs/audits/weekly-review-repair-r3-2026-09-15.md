# Weekly review repair R3 — 2026-09-15

Task class: data artifact and downstream handoff. Bounded repair of #273 finding 4010985592.

Verified on published head 561727290a371a76381a383856b55b065fb0c4b3 (see exact head in paired JSON). A positive substituted schedule asset ID passed reuse validation. Intake now compares the saved ID with fetched metadata after the existing before/after stability check. A mismatch fails closed without rewriting the saved receipt. Identical bytes under a replacement release asset also require explicit reconciliation; reuse does not silently reattribute the snapshot.

Touched: schedule intake, matching publication regression test, this paired audit. Regression failed before repair; all 31 weekly tests pass after repair. Existing valid reuse still preserves receipt bytes and original retrieval clocks. No network acquisition was run; tests use committed bytes and mocked metadata.

What remains missing: independent review is pending. Offline structural validation alone does not authenticate the asset against GitHub. Existing source candidate bytes, source limitations, support pin and coverage are unchanged. No admission, activation, merge or deployment is implied.
