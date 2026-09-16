# Weekly review repair R2 — 2026-09-15 UTC

Joe authorized verification and bounded repair of the three P2s reported on Data #273 / Fantasy #386, followed by fresh reviews. Data task classes: data artifact and downstream handoff. No new acquisition, source admission, candidate publication, merge or deployment.

Data #273 at b7863581d53327f4196ba959c6b12c7352c4a6c0:
- Confirmed schedule reuse can ignore a broken receipt. A shared schedule receipt validator now checks schema, source family/URL, asset ID, byte/hash binding, fixed license attribution, offset-bearing retrieval clocks/order, limitations shape and fixture exclusion. Both acquisition reuse and offline preparation call it; valid reuse preserves original receipt bytes.
- Confirmed publication can accept broken revision metadata. Validate sequential integer revision numbers, predecessor linkage, and digest syntax before artifact reads, unchanged return or append. A corrupt inventory is rejected without modifying its bytes or creating a new revision.

Fantasy #386 at 85f7b50f74732a61d90a2c2d69c42e558a8b11c0:
- Confirmed coverage can list games without player observations. Offline preview now requires exact equality between observed-game IDs and all decoded player-row game IDs, before schedule reconciliation and before skill-position display filtering. Upstream team-only coverage without identified player support is rejected by this preview, not rewritten into player evidence.

Validation: 31 weekly Data tests and 69 Fantasy adapter/route/public-profile tests pass. The two Data regression tests fail before repair; four new Fantasy malformed-coverage cases fail before repair. Existing pinned source bytes pass offline preparation; existing candidate still displays 332 skill-position observations, 15/16 scheduled games and unknown finality. No raw files, stored receipts, candidate revisions, scoring rules or runtime admission changed. Existing revisions retain their original builder hashes; this pass does not regenerate or publish them.

Files: Data schedule intake, publication validator, publication tests and paired R2 audit; Fantasy weekly decoder/tests, R2 audit and agent logs. Audit trigger: fresh independent review pending on updated remote heads. Both PRs remain unmerged and unactivated.
