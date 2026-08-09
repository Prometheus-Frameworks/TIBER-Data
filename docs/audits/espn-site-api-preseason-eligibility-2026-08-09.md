# Audit: ESPN Site API — Preseason Box-Score Eligibility

- **Date:** 2026-08-09
- **Scope:** `https://site.api.espn.com/apis/site/v2/sports/football/nfl/{scoreboard,summary}`, solely as a **preseason box-score evidence source** (issue #242's blind spot: nflverse publishes no preseason play-by-play and Sleeper's preseason stats endpoint serves an empty object).
- **Tracking issue:** [TIBER-Data #242](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/242)
- **Type:** Source audit accompanying a candidate-tier admission. **Process deviation, recorded:** the fetcher and first captured game landed on PR #243 *before* this audit existed, violating the audit-first posture (AGENTS.md, external-source rules 1–3). Caught by automated PR review; the operator (H4MMER) explicitly authorized the retain-and-audit resolution on 2026-08-09, enacted by merge of PR #243.
- **Machine-readable companion:** `docs/audits/espn-site-api-preseason-eligibility-2026-08-09.json`

---

## 1. Verdict

**`external_candidate` — preseason box-score evidence only**, under the constraints in §3. **ESPN is not, and does not become, an approved truth source** (TRUTH_SOURCES.md unchanged); every snapshot self-declares this in its `consumer_safety` block.

## 2. Findings (per the required audit questions)

- **License / access / redistribution:** Public, unauthenticated, **undocumented** endpoints (widely used community-side; no developer program, no published data license; ESPN site terms govern). No declared license → no redistribution rights: fail closed. Consequences honored: snapshots persist **extracted game facts only** (scores, per-player stat lines, ESPN athlete ids for identity) — no article text, no media, no styling assets; artifacts are candidate-fenced for internal analytics and barred from public redistribution.
- **Source lineage:** ESPN's own live game data pipeline; first-hand for the games it covers. For August preseason there is currently **no less-intermediated machine-readable alternative** in the repo's integrated upstreams (posture rule 5 check: nflverse — none; Sleeper — empty), which is the admission's entire justification.
- **Schema / shape:** Scoreboard: events with `season.type` (1 = preseason), status, competitors, scores. Summary: `boxscore.players[].statistics[]` grouped by category with label/value arrays. First capture: 1 game, 103 player lines. The fetcher hard-filters `season.type === 1` — regular-season games are structurally excluded from this admission.
- **Public / synthetic / scraped / transformed / paid:** Public unofficial API; verbatim numeric facts, minimally transformed (label→value zip), free.
- **TIBER overlap:** None for preseason (the gap being filled). `espn_id` already exists in coverage `provider_ids`, enabling governed identity joins.
- **Leakage risk:** Low and structural: preseason evidence is usage/role signal, not season outcomes. Guard: `consumer_safety.not_allowed` forbids joining these rows into REG `season_type` artifacts.
- **Identity risk:** ESPN athlete id + display name only; snapshots deliberately perform **no name-based resolution** — downstream joins must route through the identity crosswalk. Reliability risk is availability, not correctness: partial fetches now mark the artifact `partial: true` and exit nonzero (PR #243 review fix, commit `ee17b08`).

## 3. Constraints of the classification

1. Preseason (`season.type === 1`) only; any regular-season ESPN usage requires a new audit and an explicit TRUTH_SOURCES.md decision.
2. Candidate tier only; promotion of any snapshot requires a separate operator source-policy review.
3. No public redistribution of snapshot artifacts; internal analytics evidence only.
4. Identity joins via the crosswalk exclusively; never by display name.
5. Seasonal lifetime: the admission is re-reviewed before each August; scheduled runs stop at final preseason week.
