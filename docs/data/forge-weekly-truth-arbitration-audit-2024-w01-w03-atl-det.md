# FORGE truth-arbitration audit (2024 W1–W3 ATL/DET proof slice)

Scope lock:
- season `2024`
- weeks `1,2,3` only
- 8-player ATL/DET proof cohort only
- ATL/DET team context rows only
- no contract/FORGE/slice changes

## Fields audited

Player comparison fields (raw support lane):
- `targets`
- `receptions`
- `receiving_yards`
- `receiving_tds`
- `air_yards`
- `fantasy_points_ppr`

Team comparison fields (raw support lane):
- `team_pass_attempts`
- `team_rush_attempts`
- `team_points`
- `team_air_yards`

Upstream team mapping used by scaffold builder:
- `team_pass_attempts <- attempts | pass_attempts | team_pass_attempts`
- `team_rush_attempts <- carries | rush_attempts | team_rush_attempts`
- `team_points <- total_points | points | team_points`
- `team_air_yards <- passing_air_yards | air_yards | team_air_yards`

## Evidence used (repo-local + execution boundary)

1. Legacy raw support rows are present and inspectable in-repo for W1–W3 (`weekly_player_stats.offline_fixture.json`, `team_week_context.offline_fixture.json`).
2. Upstream scaffold selection/mapping logic is present and explicit in-repo (`src/ingest/forge_weekly_upstream_support_scaffold.py`).
3. Comparison scripts for support and derived lanes are present and executable.
4. In this environment, the upstream scaffold raw artifacts are not committed, and public-source pull is blocked (export fails with `No public data available ... offline fallback is disabled`), so a fresh in-repo numeric replay of upstream values is not possible in this run.
5. Existing project context for PR34 confirms:
   - cross-lane identity mismatch is surfaced (not hidden),
   - Amon-Ra id mismatch is `legacy=00-0037834` vs `upstream=00-0036963`,
   - material player/team stat divergence remains after mapping fixes.

## Mismatch arbitration by bucket

### 1) Identity mismatch (Amon-Ra St. Brown)
- Observation: same player name/team/week row aligns, but ids differ across lanes.
- Current bucket: **legacy lane likely stale / hand-authored / non-public-truth**.
- Why: offline fixture provenance/history already documents legacy support expansions as repo-held artifacts with incomplete deterministic provenance for later weeks; id drift is consistent with that risk pattern.
- Truth call: upstream id appears more likely to reflect public-source identity semantics for this proof slice.

### 2) Player stat value divergence (Amon-Ra W1–W3; also seen across cohort)
- Observation: reported material differences in core player stat fields between lanes for same `(week, name, team)` keys.
- Current bucket: **legacy lane likely stale / hand-authored / non-public-truth** (primary), with **unresolved remainder** until upstream snapshots are committed/replayed in-repo.
- Why:
  - the scaffold player mapping is mostly direct column transfer (targets/receptions/yards/td/air_yards/fantasy points),
  - that leaves little transformation surface to create large deltas inside the scaffold itself,
  - so large deltas are more consistent with source-lane truth differences than with this narrow mapping layer.

### 3) ATL/DET team context divergence (W1–W3)
- Observation: reported material differences remain after field-name coalescing fixes.
- Current bucket: **upstream lane likely using different stat surface or source convention** (primary), with **unresolved remainder**.
- Why:
  - known mapping bug surface (field aliases) was already tightened,
  - if large deltas persist after alias fixes, mismatch is more likely upstream-vs-legacy stat definition/aggregation semantics (not a simple key-map miss),
  - exact residual split (semantic vs hidden bug) cannot be finalized here without committed upstream raw snapshots.

### 4) Remaining mapping bug risk
- Current bucket: **unresolved (low confidence, not cleared)**.
- Why: code review does not show an obvious high-impact transformation bug in the supported fields, but replayable upstream artifacts are absent in this repo snapshot for direct row-for-row proof.

## Proof-slice truth stance (blunt)

- For identity, upstream looks closer to public-source truth for Amon-Ra in W1–W3.
- For player/team numeric values, the legacy fixture lane should be treated as potentially stale/non-authoritative for arbitration purposes.
- Team-context deltas no longer look like a simple field-map typo; they look more like source-surface semantic differences, pending final row-level replay evidence.

## Unresolved items that block final closure

1. Commit or reproducibly generate the upstream W1–W3 scaffold raw artifacts in-repo for this environment.
   - manual promotion path now documented/scripted via `scripts/promote_forge_weekly_upstream_proof_snapshot.py`
2. Capture a persistent row-level diff table for the 8-player cohort + ATL/DET team rows, with per-field delta counts.
3. Re-check residuals after those artifacts are present to separate:
   - confirmed source-semantic deltas
   - any remaining true mapping defects
