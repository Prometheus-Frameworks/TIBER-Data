# Weekly review repair R8 — 2026-09-15

Task class: data artifact/downstream handoff validation repair. Joe authorized the bounded repair/push/re-review loop, stopping before merge. Accepted Data #273 P2 `4020572558` against `750d68c61e209327c44e65bb32d64dd50719a373`.

The schedule receipt validator parsed `release_asset_updated_at` but did not require it to precede retrieval completion. A direct retained-receipt mutation reproduced acceptance before repair. Schedule validation now requires both asset update <= retrieval completion and retrieval start <= completion, matching the player/team receipt rule. The shared validator protects fresh acquisition, retained receipt reuse, and offline publication preparation.

Validation: 37 weekly unittest tests pass. The new release-after-retrieval test failed before repair. Existing raw support, candidate revisions, and limitations are unchanged. Touched: schedule intake validator, publication tests, this audit, and `HANDOFF.md`.

Missing: fresh independent exact-head review. Internal clock consistency does not authenticate source metadata or certify finality. No acquisition, admission, runtime activation, merge, or deployment.
