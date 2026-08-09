# Audit: Sleeper Players Endpoint — Identity-Mapping Eligibility

- **Date:** 2026-08-09
- **Scope:** `https://api.sleeper.app/v1/players/nfl` (the full-players dump), solely as an **identity-mapping evidence source** for the crosswalk candidates artifact.
- **Tracking issue:** [TIBER-Data #241](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/241)
- **Type:** Source audit accompanying a candidate-tier admission. **Process deviation, recorded:** the downloader and first candidate artifact landed on PR #243 *before* this audit existed, violating the audit-first posture (AGENTS.md, external-source rules 1–3). The violation was caught by automated PR review; the operator (H4MMER) explicitly authorized the retain-and-audit resolution on 2026-08-09, enacted by merge of PR #243.
- **Machine-readable companion:** `docs/audits/sleeper-players-endpoint-eligibility-2026-08-09.json`

---

## 1. Verdict

**`external_candidate` — identity-mapping evidence only**, under the constraints in §3. Not a truth source; not eligible for stats, projections, rosters, news, or any non-identity lane under this audit.

## 2. Findings (per the required audit questions)

- **License / access / redistribution:** Public, unauthenticated REST endpoint, documented in Sleeper's developer docs (which request sparing use — the fetcher is designed for at-most-daily invocation). **No data license is declared anywhere.** Per posture rule 4, no declared license means no redistribution rights: fail closed. Consequence honored: **the raw dump is never committed** — the script reads a locally supplied or freshly fetched copy, records its sha256 as provenance, and embeds only the minimal per-player identity fields needed as match evidence (sleeper_id, declared gsis_id/espn_id, name, team, position).
- **Source lineage:** Sleeper's internal player database, which itself aggregates provider identifiers (gsis, espn, yahoo, sportradar, rotowire, et al.). For **sleeper_id itself, Sleeper is the first-hand authority** — no less-intermediated source exists, satisfying posture rule 5 for exactly this field. Its *declared* third-party ids (gsis_id, espn_id) are treated as claims, not truth: the crosswalk builder cross-checks them against the promoted coverage artifact's own provider ids and routes every conflict to human review (including same-row espn_id value conflicts — see PR #243 review fix, commit `ee17b08`).
- **Schema / shape:** ~12,215 player records at audit time; 3,893 carry `gsis_id`, 6,736 carry `espn_id`. Dozens of fields exist (status, depth chart, news timestamps, measurements); **only the identity fields above are in scope.**
- **Public / synthetic / scraped / transformed / paid:** Public app-supporting API, first-party, free, ungated.
- **TIBER overlap:** The promoted `identity_crosswalk` (25 operator-verified rows) and coverage `provider_ids` already embed sleeper/espn identifiers — this source extends an existing identity vocabulary rather than introducing a new domain.
- **Leakage risk:** None in scope — identity facts only, no outcomes, no features.
- **Identity risk:** This audit's entire subject. Mitigations: provider-declared-ID joins preferred over names; three-tier evidence labels (`gsis_direct`/`espn_bridge`/`name_exact`); all ambiguity and all cross-provider conflicts fail to a review CSV; candidates never promote without operator review.

## 3. Constraints of the classification

1. Identity-mapping evidence only; any other Sleeper lane (stats, projections, trending, league data) requires a new audit and issue.
2. Raw dumps stay out of the repository permanently; artifacts carry dump sha256 + fetched_at provenance instead.
3. Candidate tier only (`exports/candidates/`); promotion of any mapping remains a manual operator review.
4. No public redistribution of Sleeper-derived data beyond the minimal per-row match evidence inside candidate artifacts.
5. Fetch cadence: at most daily, per Sleeper's own guidance.
