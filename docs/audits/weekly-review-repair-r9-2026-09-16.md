# Weekly review repair R9 — 2026-09-16

Task class: data artifact/downstream handoff validation repair. Joe authorized the bounded repair/push/re-review loop, stopping before merge. Accepted Data #273 P2s `4020954441` and `4020954445` against `5ccb352a335202123d0fa1cbb250e93ebd93a7ae`.

Declared row counts are now checked, when present, against CSV records after byte length and digest validation. Player/team mutations cover incorrect integers and booleans. Receipts that omit the optional historical metadata remain valid; no count is invented.

Publication preparation now rejects either half of the optional schedule directory/commit pair before reading any support bytes. This prevents a supplied commit or directory from being silently ignored and producing unavailable coverage.

Validation: 38 weekly unittest tests pass. Six row-count/argument-pair cases failed before repair. Existing raw support, candidate revisions, and limitations are unchanged. Touched: box-score validator, publication preparation, focused tests, this audit, and `HANDOFF.md`.

Missing: fresh independent exact-head review. Row-count consistency is not independent source corroboration. No acquisition, admission, runtime activation, merge, or deployment.
