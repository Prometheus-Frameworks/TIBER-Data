# Audit: Promoted Artifacts Index (TIBER-Data #97)

- **Date:** 2026-07-24
- **Scope:** TIBER-Data only. Read-only contradiction audit of the
  documentation-only index introduced by PR #225 under TIBER-Ops #44.
- **Tracking:** [TIBER-Data #97](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/97);
  [PR #225](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/225);
  [TIBER-Ops #44](https://github.com/Prometheus-Frameworks/TIBER-Ops/issues/44)
- **Review input:** PR #225 head
  `46519949243ff8470980fee0450b450a4b6a4be2`, based on
  `85f8a46b924d2e051729b78af25fcfc5b677ba69`
- **Type:** Audit-only. No artifact, schema, contract behavior, generator,
  validator, promotion, or downstream change.
- **Machine-readable companion:**
  `docs/audits/promoted-artifacts-index-2026-07-24.json`
- **Audit trigger:** `AGENTS.md` requires the auditor function because the
  change adds a file under `docs/contracts/**` and changes provenance and
  support-claim wording.

## 1. Executive verdict

**Pass after one documentation correction.** The index is a complete
15-file inventory of the committed `exports/promoted/**` surface and preserves
the distinction between directory location and governed provenance. Its
ownership support-window claim initially collapsed 19 roster observations into
a week-18 snapshot. The corrected index now reports the committed distribution:
4 rows at 2025 week 18, 8 at week 19, 5 at week 20, and 2 at week 22, followed
by 7 rows backed by 2026 draft facts and 1 fixture row.

No other contradiction, invented producer, widened support window, or quiet
promotion was found.

## 2. Files inspected

| File or surface | Auditor use |
| --- | --- |
| `AGENTS.md` | Task classes, non-negotiable boundaries, and audit trigger |
| `TRUTH_SOURCES.md` | Truth hierarchy and fail-closed support rules |
| `README.md` | New navigation entry and repository-level wording |
| `docs/contracts/promoted-artifacts-index.md` | Complete index under review |
| `exports/promoted/**` | Exact committed inventory and artifact declarations |
| Linked schemas and repository documentation | Version, provenance, status, and bounded-support evidence |
| `exports/promoted/player_ownership/player_ownership_latest.json` | Exact row/source distribution for the corrected support window |

## 3. Auditor checks

| Check | Result | Evidence |
| --- | --- | --- |
| Committed inventory parity | **Pass** | 15 regular files exist under `exports/promoted/**`; the index contains the same 15 paths with no missing or extra entry. |
| Payload readability | **Pass** | All 14 committed `.json` files parse; the single `.jsonl` event ledger parses as one JSON row. |
| Local documentation links | **Pass** | Every local Markdown target added by the PR resolves to a committed path. |
| Directory/provenance separation | **Pass** | The index explicitly says `exports/promoted/` is a location, not a provenance guarantee; fixture and provisional states remain visible. |
| Producer claims | **Pass** | Producers are named only when repository evidence supports them; `player_ownership_aliases.json` remains `unknown`. |
| Support boundaries | **Pass after correction** | No row window is expanded. The ownership cell now states the exact heterogeneous row distribution rather than a single week-18 snapshot. |
| Scope drift | **Pass** | No file under `exports/**`, `data/**`, `schemas/**`, `src/**`, or downstream repositories changed. |

## 4. Ownership distribution

Direct inspection of the 27 `players` rows in
`player_ownership_latest.json` produced:

| Source evidence | Rows |
| --- | ---: |
| `nflreadpy_load_rosters_weekly_2025`, week 18 | 4 |
| `nflreadpy_load_rosters_weekly_2025`, week 19 | 8 |
| `nflreadpy_load_rosters_weekly_2025`, week 20 | 5 |
| `nflreadpy_load_rosters_weekly_2025`, week 22 | 2 |
| `nfl_draft_results_2026_nbcsports_profootballtalk` | 7 |
| `fixture_demonstration_only` | 1 |
| **Total** | **27** |

The 19 roster-backed rows remain explicitly provisional and stale. The audit
does not reinterpret them as current roster truth, infer week-21 support, or
claim full-player-universe coverage.

## 5. Conclusion and authority boundary

Audit conclusion: **no contradiction found after the ownership-window wording
correction.** The index is deterministic, bounded, documentation-only, and
honest about source coverage.

This audit emits no promotion or merge decision and does not authorize artifact
mutation, producer reassignment, support expansion, downstream availability,
deployment, or product behavior. Final merge authority remains with the
operator.
