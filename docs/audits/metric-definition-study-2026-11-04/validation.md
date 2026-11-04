# Validation and review record

Prepared 2026-11-04 against TIBER-Data baseline
`c46e9c34fd355bf922bc14eaeeb88fc9c3e77adc`.

## Study checks

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s docs/audits/metric-definition-study-2026-11-04 -p 'test_*.py' -q` | 27 passed: 22 prototype/receipt checks and five probes of unchanged original gold-transform code |
| `python3 -m ruff check docs/audits/metric-definition-study-2026-11-04` | Passed |
| `git diff --check` and `git diff --cached --check` | Passed; staged inventory contains exactly eight files in this audit directory |
| Retained JSON reproduction | Covered by the focused tests: catalog, examples and pinned artifact census equal their producers |
| Existing semantics viewer, `--group opportunity` | Passed; registry reports 37 total entries and eight matching opportunity entries |
| `npm run typecheck` | Passed as the first step of `scripts/pre_pr.sh` |
| `npm run build` | Passed |
| `npm run test -- --exclude test/rosterPlayerTeamMapArtifact.export.test.ts` | 923 tests passed across 18 files |

The focused gold-transform probes use explicitly synthetic inputs. They reproduce
the existing summed-player-route denominator, TPRR calculation, null/zero-route
behavior, partial-input-population behavior, and zero/null/negative team-target
behavior. They do not validate real provider events, completeness, or player
observations. The 22 dependency-free checks can run without the repository's
Python dependencies; the five source probes require Polars and report a skip if
it is unavailable. All five ran here.

## Broader-suite limitations

The unrestricted `scripts/pre_pr.sh` run completed TypeScript checking and
reported the other 18 TypeScript files as passing, but did not complete the
roster export test file. It was interrupted with exit code 130. The later
bounded TypeScript run explicitly excluded that file; this is not a full-suite
pass.

A separate diagnostic used the compiled, unchanged baseline producer and no
large assertion diff. It showed that the roster test's source-backed comparison
compares generated array JSON with the raw source wrapper object at
`data/processed/evidence/roster_player_team_map_2025.source_backed.json`.
`generated_matches_compared_raw_file=false`, `generated_shape=array`, and
`compared_raw_shape=object`. Those values cannot satisfy that existing equality
assertion. The study does not claim this proves the cause of the stall and does
not repair unrelated roster code/tests.

The initial full Python run reached pre-existing historical replay tests with
missing historical git objects in the shallow checkout. A fail-fast diagnostic
reported 421 passing tests before the first missing-history failure. Repository
history was then retrieved and the complete Python suite was run again with
`python3 -m pytest -q --maxfail=1` under a 240-second limit. It progressed past
70% with two reported skips and no reported failures before the time limit.
That run did not complete. There is no full Python-suite pass or complete
pre-PR signoff. The focused study tests completed separately as stated above.

Dependencies were installed from the existing manifests to run checks; neither
manifest nor lockfile was changed. The existing roster comparison and the
broader Python execution limit remain outside this study's repair scope.

## Publication boundary

- Only files under this audit directory may be added by this change.
- Production sources, existing tests, contracts, data, exports, dependency
  manifests, governance versions, and consumer wiring remain unchanged.
- The pinned census reads git objects rather than mutable worktree files.
- No football-docs server/provider data or new upstream player feed was used.
- Builder contradiction checks are complete. Independent exact-head review is
  pending; no independent approval or clean GitHub CI result is claimed.
- Draft PR preparation does not authorize merge, source admission, promotion,
  activation, deployment, or a fantasy action.
