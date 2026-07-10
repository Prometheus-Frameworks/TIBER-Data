# Audit: Live Play-by-Play `shotgun`/Formation Field Verification for `formation_summary_v0`

- **Date:** 2026-07-10 (audit run date; issue filed 2026-07-09)
- **Scope:** TIBER-Data only. Read-only, verification-only audit. No artifact, contract, schema, exporter, validator, Teamstate consumer, Fantasy UI change, Forecast feature, model input, promotion decision, or advice/ranking surface is created by this document.
- **Tracking issue:** [TIBER-Data #210](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/210)
- **Predecessors:** [TIBER-Data #208](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/208) / [PR #209](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/209) — `formation_summary_v0` source-boundary spec (`docs/specs/formation-summary-v0-source-boundary.md`), which named this exact verification issue as its required next step and explicitly did not authorize it in advance.
- **Upstream context:** TIBER-Teamstate #75 / PR #76 — `formation_lens_v0`, still blocked from real-data interpretation pending this Data-side chain.

---

## 1. Executive verdict

**The live pull could not be completed in this execution environment. Per the issue's own instruction ("If 2024 cannot be reached in the execution environment, document the failure exactly and stop"), this audit stops here rather than substituting another data source, guessing field behavior, or inferring schema from documentation.**

- **Live load: failed, not attempted-and-skipped.** `nflreadpy.load_pbp(seasons=[2024])` was actually invoked (twice, in two separate sessions — once during the #208/#209 spec work, once again for this issue) and failed both times with an identical, reproducible error (§3).
- **All six numbered questions in the issue remain unanswered by live evidence.** None of §2's field-existence, null-rate, or value-shape questions can be honestly reported as `verified_in_repo` or `verified_live` — see §4 for what could and could not be determined.
- **`under_center` remains blocked. `non_shotgun` remains the correct v0 label.** No evidence — live or otherwise — was obtained in this audit that would justify unlocking `under_center`, so the #208/#209 default posture is preserved by default, not because it was actively re-confirmed.
- **No implementation/dry-run issue is authorized.** The verification gate #209 required has not been passed; this audit did not pass it either. The blocker is unchanged, not narrowed.
- **New, more precise finding not in the prior spec:** the block is on the `github.com` domain generally (including `api.github.com`), not specifically on the `nflverse-data` release-asset path. `raw.githubusercontent.com` and `objects.githubusercontent.com` (the actual asset-serving CDN `github.com` release downloads redirect to) are reachable from this sandbox. `nflreadpy` v0.1.5 hardcodes all four of its data sources (`nflverse-data`, `espnscraper`, `dynastyprocess`, `ffopportunity`) to `github.com` URLs with no alternate-mirror configuration option, so this precision does not open a workaround inside `nflreadpy` itself — but it narrows what a future attempt (in an environment where `github.com` is reachable) needs to solve.
- **Provenance correction (flagged by review, applies to this document and to #209):** the prior spec's claim that `scripts/build_team_week_raw_v0_2024_candidate.py`'s real 2024 candidate "proves `nflreadpy.load_pbp()` succeeded" was inaccurate. That script fetches the release asset directly via `httpx`, not via `nflreadpy.load_pbp()`'s own downloader — see §3.1 for the corrected claim. This repo's real 2024 candidate remains genuine evidence that the release asset URL was reachable in some prior environment; it is not evidence that the specific `nflreadpy.load_pbp()` function call has ever succeeded here.

---

## 2. Execution environment and command attempted

| item | value |
|---|---|
| Environment | Claude Code remote execution sandbox (ephemeral container), outbound HTTPS routed through a policy-enforcing egress proxy |
| `nflreadpy` version | `0.1.5` (installed via `pip install nflreadpy polars pyarrow` for this audit; not a repo dependency change — no `pyproject.toml`/lockfile touched) |
| Command attempted | `nflreadpy.load_pbp(seasons=[2024])` — the exact call the issue recommends and the exact call `src/team_state/loader.py` makes in production. `scripts/build_team_week_raw_v0_2024_candidate.py`'s real 2024 candidate is a related but distinct precedent: it reaches the same release asset via a direct `httpx` call, not via this function (§3.1) |
| Season requested | `2024` only, per the issue's recommendation (same season already cross-referenced by the real `team_week_raw_v0_2024` candidate) — not substituted |
| Result | **Failed both attempts** (this session and the prior #208/#209 session), identical error |

No season substitution was made. No alternate data source was substituted. Both are explicitly disallowed by the issue text without justification, and neither was justified here because none was attempted.

---

## 3. Exact failure

```
nflreadpy.load_pbp(seasons=[2024])
  -> NflverseDownloader.download("nflverse-data", "pbp/play_by_play_2024", season=2024)
  -> GET https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet
  -> requests.exceptions.HTTPError: 403 Client Error: Forbidden
  -> ConnectionError: Failed to download https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet: 403 Client Error: Forbidden for url: ...
```

This is reproducible: it occurred identically in the prior #208/#209 session and again in this session, with no retry-until-success behavior observed. Per this environment's own operating guidance, a 403 from an organization egress policy is reported, not retried in a loop or routed around — this audit made one fresh attempt (appropriate for a new issue/session) plus targeted diagnostics (below), not repeated retries of the same call.

### 3.1 Diagnostic: what exactly is blocked

To characterize the block precisely (not just "the release asset host," as the #208/#209 spec put it), the following read-only reachability checks were run against hosts `nflreadpy` depends on or redirects through:

| host | check | result |
|---|---|---|
| `github.com` (release-asset path) | `HEAD` on the exact `play_by_play_2024.parquet` release URL | **403 Forbidden** |
| `api.github.com` | `GET` on a public release-tag lookup | **403 Forbidden** |
| `objects.githubusercontent.com` | `GET` on root path (no asset path — a reachability probe, not a real fetch) | **404 Not Found** (i.e., the host is reachable; 404 is an expected response to an invalid root path, not a policy block) |
| `raw.githubusercontent.com` | `GET` on a real, small public file (`nflverse/nflverse-pbp/master/teams_colors_logos.csv`) | **200 OK — fully reachable and fetched successfully** |

**Interpretation:** the egress policy in this sandbox blocks `github.com` and `api.github.com` specifically, not GitHub's content-serving CDNs generally. `objects.githubusercontent.com` (the CDN `github.com/.../releases/download/...` URLs redirect to for the actual asset bytes) and `raw.githubusercontent.com` are both reachable. `nflreadpy`'s `NflverseDownloader` (`downloader.py`) hardcodes all four of its `BASE_URLS` to `github.com` paths (`releases/download/` or `raw/master/`) with no way to point it directly at a pre-resolved CDN URL — so this session cannot exploit the CDN reachability to route around the block using the installed package as-is. A future attempt in an environment where `github.com` itself is reachable would not hit this specific obstacle.

This is a session/environment-level egress policy characteristic, not evidence about the nflverse data itself, and not a claim that TIBER-Data's real execution environment has this same restriction. `src/team_state/loader.py` calls `nflreadpy.load_pbp(seasons=[season])` directly and is the accepted production loader, but its own successful execution is not independently evidenced here.

**Correction (flagged by review):** an earlier draft of this document, and of the predecessor spec (`docs/specs/formation-summary-v0-source-boundary.md`), overstated what `scripts/build_team_week_raw_v0_2024_candidate.py`'s real 2024 candidate proves. Re-reading that script (`_retrieve_nflverse_parquet`, `_fetch_source_bytes`, `retrieve_pbp`): it fetches the release asset via a **direct `httpx.Client().get(url)` call against the same URL `nflreadpy`'s downloader would resolve**, not via a call to `nflreadpy.load_pbp()` itself — the `nflreadpy_loader=f"nflreadpy.load_pbp([{SEASON}])"` argument passed into `_retrieve_nflverse_parquet` is only a descriptive label recorded in `retrievalMethod` metadata ("httpx GET ... (same nflverse release asset as nflreadpy.load_pbp(...))"), not evidence that function was invoked. The real 2024 candidate is genuine proof that the `github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2024.parquet` **release asset was reachable via `httpx`** in that prior session/environment — it is **not** proof that `nflreadpy.load_pbp()`'s own `requests`-based downloader (`NflverseDownloader._download_file` in `nflreadpy/downloader.py`) has ever successfully run in this repo. Both hit the same URL, but through different HTTP client code paths, so one succeeding does not establish the other did.

---

## 4. Answers to the issue's six questions

Every answer below is qualified by verification status, per this repo's fail-closed posture (`TRUTH_SOURCES.md`) and the vocabulary established in `docs/specs/formation-summary-v0-source-boundary.md` §0/§2.

### 4.1 Does the live source expose `shotgun`?

**Not verified — live load failed.** Column existence, dtype, unique values, null count, null rate, and whether values are binary/boolean/numeric cannot be reported from this session. This remains exactly as `documented_schema_unverified_live` as it was in #209 §2 — this audit adds **no** new evidence on `shotgun` itself, positive or negative. It does not confirm the field exists; it also does not refute it.

### 4.2 Does the live source expose any pistol/formation-disambiguation field?

**Not verified — live load failed.** No column-name search (`pistol`, `formation`, `shotgun`, `under`, `center`, `align`, `personnel`, `motion`, `shift`) could be run against real data. This audit cannot report a candidate field, and per the issue's own instruction, absence of evidence here is not evidence of absence — it is simply unresolved.

### 4.3 Can `shotgun == 0` honestly be upgraded from `non_shotgun` to `under_center`?

**No — unchanged from #209, not re-derived here.** The issue's own default answer stands: "no" unless the live source clearly proves pistol and other non-under-center looks are absent, separable, or negligible under an explicitly documented rule. No such proof was obtained (§4.1, §4.2 above are both unresolved, not resolved-in-favor). The v0 vocabulary from #209 §3.3 is preserved exactly:

```
shotgun_plays
non_shotgun_plays
unknown_or_unclassified_alignment_plays
```

`under_center_plays` is **not** recommended.

### 4.4 Does the live source expose `defteam`?

**Not verified — live load failed.** Existence, null count/rate, and reconciliation with `posteam` cannot be reported. Remains `documented_schema_unverified_live` per #209 §2, with no change in either direction. `defteam` is not needed for the `formation_summary_v0` denominator or alignment split as currently scoped (§3.1/§3.1a of #209 only need `posteam`), so its continued unavailability does not block anything already decided — it stays deferred.

### 4.5 Confirm the exact scramble indicator column name

**Not verified — live load failed.** The exact live-source column name for a scramble indicator (whether `qb_scramble` or something else) remains **GATED**, exactly as `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Scrambles") already stated it would be "unknown until retrieval." This audit's live retrieval did not occur, so the gate stays open. Per #209 §3.1b (added in PR #209's second review round), this is **non-blocking** for `formation_summary_v0`'s offensive-play denominator (categorical `play_type` inclusion is unaffected) but **is** blocking for the pass/run split fields (`shotgun_pass_rate`/`shotgun_run_rate`/etc.), which must use the verified dropback indicator once its name is confirmed, or fail closed per row.

### 4.6 Confirm denominator-field compatibility with the existing `team_week_raw_v0_2024` precedent

This is the one question this audit **can** partially answer, because it does not require a *new* live pull — it can be answered by re-reading the **already-committed, already-validated** real 2024 candidate artifact and its build script, which is exactly what #209 §2 did. Restated here with the requested three-way split:

| field | status |
|---|---|
| `play_type` | **Already proven by the prior real 2024 candidate path.** Used as the categorical gate in `scripts/build_team_week_raw_v0_2024_candidate.py::is_offensive_play`/`is_competitive_play`; the resulting 544-row candidate passed `allPassed: true` validation. |
| `qb_kneel` | **Already proven** — present as a `play_type` value in the same real build (`OFFENSIVE_PLAY_TYPES`), covered by `tests/test_build_team_week_raw_v0_2024_candidate.py::test_is_offensive_play_includes_kneel_and_spike`. |
| `qb_spike` | **Already proven** — same evidence as `qb_kneel`. |
| `two_point_attempt` | **Already proven** — `row.get("two_point_attempt")` used and tested in the same real build. |
| `sack` | **Already proven** — `row.get("sack")` increments `stats.sacks_allowed` in the real build's `aggregate_game`. |
| `penalty` | **Policy proven, field-level mechanism not directly named in code.** `docs/data/team-week-raw-v0-2024-pr-c-preflight.md` §2 ("Penalties") locks the policy; the real build's categorical `play_type` filter implements the net effect without referencing a literal `penalty` column by name in the script text read for this audit. |
| `aborted_play` | **Policy proven, exact column/detection mechanism still not confirmed.** Same status as in #209 §2 — the real build's `excludedPossessionPlays` diagnostic count implies aborted plays are captured by falling outside `OFFENSIVE_PLAY_TYPES`, but the literal field name was not independently confirmed by this audit (still unable to reach live data). |
| `epa` | **Already proven** — `row.get("epa")` used throughout `aggregate_game` in the real build. |
| `success` | **Already proven** — `row.get("success")` used in `aggregate_game`. Per #209 §3.2, this is nflverse's own native definition and is **distinct** from TIBER `team_state`'s own down/distance success rule; both remain real, but `formation_summary_v0` should not conflate them (unchanged recommendation). |

**None of the above required this audit's live pull to answer** — they were already settled by the prior real 2024 candidate build, and this audit is not claiming new live confirmation for them. This table exists here only because the issue asked for it to be restated with the three-way split; it is not new evidence.

---

## 5. Decisions

| question (from issue's expected-output list) | decision |
|---|---|
| Was a read-only live load attempted and documented, or was an access failure transparently documented? | **Access failure transparently documented** (§3). No live load occurred. |
| Is `shotgun` existence/value-shape/null-count/null-rate reported? | **No — unavailable.** Explicitly `not verified`, not silently omitted. |
| Are candidate pistol/formation-disambiguation fields searched and reported? | **Search could not be run.** No candidate field is reported, positively or negatively. |
| Is `defteam` availability reported? | **No — unavailable.** Unchanged from #209. |
| Is scramble indicator naming checked and reported? | **Not checked — still GATED**, unchanged from the PR C preflight doc. |
| Does the audit state whether `under_center` remains blocked or can be unlocked? | **Remains blocked.** No evidence obtained to unlock it. |
| Does the audit state whether `non_shotgun` remains the v0 vocabulary? | **Yes, unchanged.** |
| Does the audit confirm whether a separate implementation/dry-run issue is authorized? | **Not authorized.** The verification gate has not been passed — this audit failed to pass it, it did not narrow it. |

---

## 6. Recommended next step (separate, not started here)

This audit does not authorize an implementation/dry-run issue, and does not itself re-attempt the live pull further (per the guidance against retry loops on organization policy denials). The concrete blocker is narrower than before this audit (§3.1: specifically `github.com`/`api.github.com`, not GitHub's CDNs generally, and not `nflreadpy`'s data itself), which should make a future retry easier to scope:

**A future verification attempt should run in an environment where `github.com` is reachable** — e.g., this repo's actual CI/development environment. `src/team_state/loader.py` is the accepted production caller of `nflreadpy.load_pbp()`, and `scripts/build_team_week_raw_v0_2024_candidate.py`'s real, committed 2024 candidate is genuine evidence that the same release asset URL was reachable via `httpx` in some prior environment — but neither is direct proof that `nflreadpy.load_pbp()`'s own downloader has successfully executed in this repo (§3.1 correction). A future attempt should treat `nflreadpy.load_pbp()` reachability as still unconfirmed, not as something merely blocked by this sandbox alone. This sandbox has failed to reach `github.com` twice now, across two independent sessions.

Until such an attempt succeeds and answers §4.1–§4.5, `formation_summary_v0`'s `under_center` label stays blocked, `non_shotgun` stays the v0 vocabulary, and no implementation/dry-run issue should be opened.

---

## Appendix — Referenced facts

- `nflreadpy` v0.1.5's `NflverseDownloader.BASE_URLS` (`nflreadpy/downloader.py`) hardcodes four sources, all under `github.com`: `nflverse-data` (releases), `espnscraper` (raw), `dynastyprocess` (raw), `ffopportunity` (releases). No alternate-mirror or direct-CDN-URL option exists in the installed package.
- `exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json` (544 rows, `partial_real_data`, `allPassed: true`) remains real, committed, validated evidence that the `nflverse-data` release asset URL for 2024 pbp was reachable via `httpx` in some prior session/environment. It is **not** direct evidence that `nflreadpy.load_pbp()` itself — which uses its own `requests`-based downloader, a different code path hitting the same URL — has ever successfully executed in this repo (correction, §3.1; the original claim in `docs/specs/formation-summary-v0-source-boundary.md` was overstated and has been corrected there too).
- Diagnostic reachability (this session): `github.com` release path 403; `api.github.com` 403; `objects.githubusercontent.com` reachable (404 on an intentionally invalid root probe, not a policy block); `raw.githubusercontent.com` 200 (full successful fetch of a real file).
- This audit adds no new evidence, positive or negative, about `shotgun`, `defteam`, pistol/formation-disambiguation fields, or the exact scramble-indicator column name. All remain exactly as classified in `docs/specs/formation-summary-v0-source-boundary.md` §2.
