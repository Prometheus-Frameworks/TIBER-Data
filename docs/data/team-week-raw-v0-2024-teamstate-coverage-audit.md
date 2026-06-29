# team_week_raw_v0 2024 — Governed Teamstate Coverage Audit (Forecast Run 2 gate)

**Issue:** TIBER-Data #181 — *Data: provide complete governed Teamstate coverage for Forecast Run 2 gate*
**Scope:** upstream coverage verification only. No Forecast change, no Forecast Run 2 rerun, no FORGE work, no fantasy/product output.
**Verdict:** **Complete governed 2024 Teamstate source coverage already exists in TIBER-Data.** The artifact is 32/32 teams, 544/544 played team-game rows, governed by explicit marker, with full source/validation/lineage provenance. The earlier Forecast 3-team failure is a **downstream handoff issue**, not a TIBER-Data coverage gap (see §7).

## Core answer

> Can TIBER-Data provide a complete governed 2024 Teamstate source artifact that TIBER-Teamstate can consume and Forecast can later evaluate against its coverage gate?

**Yes — it already does.** No new coverage artifact needs to be produced. The governed artifact below satisfies every TIBER-Data-side requirement of the Forecast coverage gate. The remaining work is entirely downstream: TIBER-Teamstate must emit its Forecast-facing artifact *from this governed source* rather than from a partial scaffold/candidate.

---

## 1. Current artifact inventory

| Field | Value |
| --- | --- |
| artifact family | `team_week_raw_v0` |
| artifact path | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json` |
| artifact id (envelope) | `team_week_raw_v0` |
| season | 2024 |
| row grain | team-**game**-week (one row per team per played game; bye weeks are non-game weeks, not emitted) |
| row count | 544 |
| team count | 32 |
| week coverage | weeks 1–18 present; each team has exactly 17 played-game rows (its bye week is absent by design) |
| governance status | `governed` / `governanceSource: explicit_marker` / `provenanceStatus: governed_real_data` |
| source refs | `nflverse-data:pbp/play_by_play_2024`, `nflverse-data:schedules/games` (each with sha256 checksum) |
| validation refs | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json` (`allPassed: true`, 16 checks) |
| lineage refs | `data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json` |
| generated_at | `2026-06-27T13:42:06+00:00` |
| promoted_at / review | `2026-06-27` — explicit human promotion review, PR D, `docs/reviews/team-week-raw-v0-2024-promotion-review-pr-d.md`, TIBER-Data #179 / #180 |

**Contract of record:** `docs/contracts/team-week-raw-v0.md`.

Related supporting artifacts (not the governed source, listed for completeness):
- `exports/fixtures/team_week_raw/team_week_raw_v0.sample.json` — 4-row scaffold fixture (2025 W8: DET/PIT/TEN/MIA); **not** league-complete, explicitly labeled fixture.
- `scripts/build_team_week_raw_v0_2024_candidate.py` — deterministic builder (requires nflverse/polars to retrieve source).
- `scripts/promote_team_week_raw_v0_2024_candidate.py` — idempotent fail-closed promotion (re-verifies the data gate, stamps the explicit governance marker, rewrites byte-identical output).
- `scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py` — **this audit**, dependency-free re-verification of the committed governed artifact.

## 2. Coverage verification

Verified directly from the committed artifact (see `scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py` and its tests):

| Check | Result |
| --- | --- |
| 32 / 32 NFL teams present | ✅ all 32 (ARI…WAS); `missingTeams: []`, `unexpectedTeams: []` |
| expected 2024 played team-game rows | ✅ 544 / 544 |
| each team has 17 played games | ✅ all 32 teams = 17 rows |
| no duplicate team-week rows | ✅ `duplicateKeys: []` |
| no missing team-week rows | ✅ no team short of its 17 played games |
| team codes normalized to NFL set | ✅ source `LA` → `LAR`; Washington `WAS`; all team + opponent codes in the canonical 32 |
| deterministic ordering | ✅ rows ordered by `(week, teamCode)` |

**Calendar-slot vs played-game note (important for the downstream join).** A full regular season is `32 × 18 = 576` calendar team-week slots, but only `32 × 17 = 544` *played* team-games. This artifact uses the **played-game grain**: 544 rows, weeks 1–18 represented, each team missing exactly its one bye week. There are **no `isByeWeek` rows** — byes are represented by absence, and `metadata.coverage.byeWeeksHandled = true`. Any downstream join keyed on a dense `team × week` (expecting 17 *or* 18 contiguous weeks) must treat a team's bye week as an expected gap, not missing coverage. The 544 target the Forecast gate expects is satisfied.

## 3. Field readiness

Mapping uses the contract field names (already camelCase). The downstream offensive-environment fields named in the issue are present under these names:

| Issue field | Artifact field | Readiness |
| --- | --- | --- |
| `epaPerPlay` | `epaPerPlay` | available |
| `successRate` | `successRate` | available |
| `redZoneTdRate` | `redZoneTdRate` | partial_nulls (zero-red-zone-trip rows are null) |
| team key | `teamCode` | available |
| season / week | `season`, `week` | available |
| pressure | `pressureRateAllowed` | **deferred** — null on every row, marked `fieldReadiness.pressureRateAllowed = "deferred"` and in `deferredFields`; null means *unknown, never zero* |
| fantasy splits | `fantasyPointsForQB/RB/WR/TE`, `fantasyPointsAllowedQB/RB/WR/TE` | null on every row (not sourced in this lane) |

Additional available offensive-environment fields: `passRate`, `neutralPassRate`, `rushRate`, `passEpaPerPlay`, `rushEpaPerPlay`, `explosivePlayRate`, `secondsPerPlay`, `pointsPerDrive`, `pointsFor`, `pointsAgainst`, `drives`, `redZoneTrips`, `offensivePlays`, `neutralPlays`, `sacksAllowed`, `turnovers`, `opponentCode`, `gameId`.

## 4. Null semantics

Per-field counts over 544 rows (full table in `team_week_raw_v0_2024_teamstate_coverage_audit.json → fieldNullReport`):

| Field group | non-null | null | reason | classification | gate risk |
| --- | --- | --- | --- | --- | --- |
| `teamCode`, `season`, `week`, `opponentCode`, `gameId` | 544 | 0 | keys | available | none |
| offensive environment (`epaPerPlay`, `successRate`, `passRate`, `rushRate`, `neutralPassRate`, `passEpaPerPlay`, `rushEpaPerPlay`, `explosivePlayRate`, `secondsPerPlay`, `pointsPerDrive`, etc.) | 544 | 0 | full real coverage | available | none |
| `redZoneTdRate` | 533 | 11 | 11 rows had **0 red-zone trips** → ratio undefined | partial_nulls | low — legitimate, not a coverage hole |
| `pressureRateAllowed` | 0 | 544 | no confirmed governed pressure source (PR C preflight §8) | **deferred** | only if Forecast *requires* this cell non-null; contract says treat as unavailable feature, never zero |
| fantasy splits ×8 | 0 | 544 | not sourced in this lane | absent | only if the Forecast-facing contract requires them — should be excluded/explicitly null, not zero-filled |

Guarantees enforced by the audit (all PASS):
- **No silent zero-fill.** `deferred_fields_never_zero_filled` confirms no deferred field carries any value (including `0`) on any row.
- **No invented pressure.** `pressureRateAllowed` is null everywhere and marked deferred.
- **No unavailable→zero conversion.** `redZoneTdRate` nulls are exactly the 11 zero-red-zone-trip rows; they are null (undefined), not 0.

## 5. Governance and provenance

| Requirement | State |
| --- | --- |
| explicit governance marker | ✅ `governance.governanceStatus = governed`, `governanceSource = explicit_marker`; agrees with `provenanceStatus = governed_real_data` (governed claim fails closed otherwise) |
| source refs | ✅ two nflverse sources with `sourceRefs` |
| validation refs | ✅ `validationReportPath` present in both artifact metadata and manifest; report `allPassed: true` (16 checks) |
| lineage refs | ✅ `lineageManifestPath` present in artifact + manifest |
| generated_at | ✅ `2026-06-27T13:42:06+00:00` |
| promotion status | ✅ `promotion.decision = governed_real_data`, reviewed `2026-06-27`, reviewRefs to PR D / #179 |
| validation command / report | ✅ see §"Reproduction" below |
| deterministic reproduction | ✅ promote re-run is byte-identical; source bytes pinned by sha256 checksums (nflverse URLs are mutable rolling assets, so the checksum is the pin) |

Governance is **not** inferred from path or name — `promote_*` carries the marker in metadata, consistent with the chain's no-path-inference rule. Provenance is complete; **no fail-closed follow-up is required on the TIBER-Data side.**

## 6. Handoff to TIBER-Teamstate

| Handoff element | Value |
| --- | --- |
| source path | `TIBER-Data/exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json` |
| expected contract / version | `team_week_raw_v0` (`docs/contracts/team-week-raw-v0.md`) |
| field mapping | camelCase row fields consumed directly (see §3); offensive environment fields are the Forecast-facing signal |
| null policy | deferred/absent fields stay null — **never zero-fill, never backfill**; surface deferred pressure as `insufficient_data`/unavailable |
| validation report | `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json` |
| coverage audit report | `exports/candidates/team_week_raw/team_week_raw_v0_2024_teamstate_coverage_audit.json` |
| fields explicitly excluded from / unavailable to Forecast | `pressureRateAllowed` (deferred), 8 fantasy-split fields (absent in this lane) — pass through as unavailable, do not fabricate |
| constraints TIBER-Teamstate must preserve | (a) consume **all 544 rows / 32 teams**, not an excerpt; (b) preserve `(week, teamCode)` keying and treat each team's bye week as an expected gap; (c) keep deferred/absent fields null; (d) accept governance only from the explicit marker (its `loadTeamWeekRawV0Governed` / `teamWeekRawV0GovernedAdapter` already do this) |

TIBER-Teamstate already has the consumption surface for this: `src/ingest/loadTeamWeekRawV0Governed.ts`, `src/adapters/teamWeekRawV0GovernedAdapter.ts`, and the Forecast-facing emitter `src/governed/runTeamWeekRawV0ForecastRun2Artifact.ts`. That emitter takes a governed artifact **path argument** and, without `--excerpt`, validates against the real **544-row** expectation. The handoff is: point it at this governed file (full mode, not `--excerpt`).

## 7. Forecast gate readiness projection (no Forecast run)

| Gate dimension | Projection |
| --- | --- |
| team coverage | **32 / 32** — artifact has all teams |
| scored-row match coverage | should improve materially: Forecast scored rows that map to any 2024 NFL team can now join (previously only BAL/CIN/PHI existed in the artifact reaching Forecast) |
| non-null cell coverage | **High** for the offensive-environment feature set: keys + ~20 offensive fields are 100% non-null; only `redZoneTdRate` has 11/544 legitimate nulls. **Blocker risk only if** the Forecast non-null-cell gate counts `pressureRateAllowed` or the 8 fantasy-split fields as required cells — those are deferred/absent by design and must be excluded from the gate's required set, not zero-filled |
| known blockers | None on the TIBER-Data side. Downstream: Forecast's non-null-cell gate must scope "required cells" to the available offensive-environment fields and exclude the deferred pressure + absent fantasy fields |

### Likely handoff gap: TIBER-Data → TIBER-Teamstate → Forecast

The earlier failure (3/32 teams: BAL, CIN, PHI; ~82% null cells → train-fold-mean imputed; `failed_sanity_control`) is **not** explained by TIBER-Data coverage, which is complete. The most likely gap is **temporal/source-selection downstream**:

- This 544-row governed artifact was **promoted 2026-06-27** (#179 / #180). The first Forecast Teamstate Run 2 comparison evidently consumed a **pre-governance partial source** — a small scaffold/candidate/excerpt (the committed sample fixture is itself only 4 rows / 4 teams) — not this artifact.
- A 3-team, mostly-null Forecast-facing artifact is the signature of TIBER-Teamstate emitting from `--excerpt`/scaffold input or an older candidate, after which Forecast imputed the missing ~82% of cells via train-fold mean — exactly the observed pathology.

**Concrete next step (downstream, not this issue):** TIBER-Teamstate re-emits its Forecast-facing artifact by running `runTeamWeekRawV0ForecastRun2Artifact` against this governed 544-row file in full mode (no `--excerpt`), confirms 32/32 teams and the 544-row coverage expectation, and only then is Forecast's coverage gate re-evaluated. No TIBER-Data change is required for that.

---

## Reproduction

Dependency-free (no nflverse/polars needed — re-verifies the committed governed artifact):

```bash
# Coverage + governance audit (this report), fail-closed:
python3 scripts/audit_team_week_raw_v0_2024_teamstate_coverage.py

# Audit tests:
python3 -m pytest tests/test_audit_team_week_raw_v0_2024_teamstate_coverage.py -q

# Idempotent governance re-verification (rewrites byte-identical output):
python3 scripts/promote_team_week_raw_v0_2024_candidate.py
```

Full builder/promotion test suite (requires nflverse/polars/httpx for the source-retrieval URL test only):

```bash
python3 -m pytest tests/test_build_team_week_raw_v0_2024_candidate.py \
                  tests/test_promote_team_week_raw_v0_2024_candidate.py -q
```

## Outcome / next step

- **Ready for TIBER-Teamstate consumption.** Complete governed 2024 Teamstate source coverage exists in TIBER-Data (32 teams, 544 played team-game rows, full provenance), with no fake zero-fill and honest deferred/absent-field semantics.
- **No missing TIBER-Data artifact, coverage, or governance work** is required before Forecast can satisfy its Teamstate coverage gate.
- The remaining work is **downstream**: TIBER-Teamstate must emit its Forecast-facing artifact from this governed 544-row source (full mode, not excerpt), preserving null semantics and bye-week gaps, before Forecast re-evaluates its gate.
