# Audit: Hugging Face NFL Datasets — Governed Experimental Eligibility

- **Date:** 2026-07-05
- **Scope:** Hugging Face NFL / American-football dataset candidates, metadata-only review.
- **Tracking issue:** [TIBER-Data #194](https://github.com/Prometheus-Frameworks/TIBER-Data/issues/194)
- **Type:** Audit-only. No downloads, no mirrors, no ingestion, no model runs, no metrics, no production binding, no Fantasy/Forecast/Teamstate/Rookies/FORGE/consumer change.
- **Machine-readable companion:** `docs/audits/huggingface-nfl-dataset-eligibility-2026-07-05.json`

> **Method note.** Every finding below comes from Hugging Face dataset cards, Hub API metadata, and publicly published previews/README content. No dataset file was downloaded, opened, or committed. Per the issue guardrail, Hugging Face metadata is **not** treated as sufficient provenance — which is itself a load-bearing reason nothing passes below.

---

## 1. Executive verdict

**No dataset reviewed here is approved for production use or governed experimental use. Zero datasets classify as `external_candidate`.**

Three structural findings drive every classification:

1. **Four of the six candidate lanes are nflverse repackagings.** The 4th-downs dataset, the WR 2025 dataset, and both Karmane datasets are (stated or evident) downstream transforms of nflverse data — the same upstream TIBER-Data already integrates first-hand via `nflreadpy` (`data/processed/evidence/*.source_backed.json`). Mirroring a third party's repackaging would insert an unverifiable middleman between TIBER and a source it already holds under known terms. The correct acquisition pattern for every tabular capability represented here is **in-house derivation**, not external mirroring.
2. **License metadata conflicts are endemic.** The 4th-downs dataset declares **no license at all**; both Karmane datasets carry an MIT tag that contradicts their paid Gumroad manual gate; the object-detection dataset has no Hub license tag while its card boilerplate claims Public Domain over what appears to be copyrighted NFL broadcast footage; the QASports family relabels wiki-scraped (typically CC-BY-SA) text as MIT. In every conflicting case this audit fails closed.
3. **No as-of discipline is verifiable anywhere.** Every tabular candidate mixes pregame features and postgame outcomes in one row (some claim separation; none can be verified without the data). None is safe near Forecast, player-history, or validation lanes without a full leakage audit that this issue does not authorize.

| # | Dataset | License / access | Classification |
|---|---|---|---|
| 1 | `afzalmengal/nfl-4th-downs-dataset` | **none declared**, public | **`rejected`** |
| 2 | `SebastianAndreu/24679_NFL_WR_Dataset_2025` | MIT, public | **`schema_reference_only`** |
| 3 | `Karmane/nfl-rest-advantage-travel-spot-research` | MIT tag ⚡ **paid manual gate** | **`schema_reference_only`** (card/preview only; no purchase, no data use) |
| 4 | `Karmane/nfl-anytime-touchdown-parlay-usage-trends` | MIT tag ⚡ **paid manual gate** | **`schema_reference_only`** (card/preview only; no purchase, no data use) |
| 5 | `keremberke/nfl-object-detection` | no Hub tag; card claims Public Domain (not credible) | **`rejected`** |
| 6 | `leomaurodesenv/QASports2` | MIT tag over wiki-scraped text | **`benchmark_reference_only`** |
| 7 | `PedroCJardim/QASports` (v1) | MIT tag over wiki-scraped text | **`benchmark_reference_only`** |

---

## 2. Per-dataset findings

Each section answers the eleven required audit questions from issue #194.

### 2.1 `afzalmengal/nfl-4th-downs-dataset` — `rejected`

- **URL:** https://huggingface.co/datasets/afzalmengal/nfl-4th-downs-dataset
- **License / access / redistribution:** Public, ungated — but **no license anywhere** (no Hub tag, nothing in the README). Without a license there is no legal basis to mirror, redistribute, or build derivative artifacts. Fail closed.
- **Shape:** 113,156 rows × 79 features, Parquet, single `train` split, 10.6 MB download (76.2 MB in memory), seasons 1999–2025.
- **Source lineage:** Unstated by the author. The README says only "filtered from full NFL play-by-play data (1999–2025)", and the column vocabulary (`game_id`, `posteam`/`defteam`, `yardline_100`, `epa`, `wp`, `def_wp`, `spread_line`, `total_line`) is the exact nflfastR/nflverse play-by-play vocabulary — almost certainly an unattributed nflverse derivative. Unverified.
- **Public/synthetic/scraped/transformed/paid:** Transformed from a public source, unattributed. Created **2026-07-03 — two days before this audit** — by an uploader with no track record (269 downloads, 1 like).
- **Schema summary:** Play-level 4th-down situations: game context, field position, score state, win probability, EPA, betting lines, coaching names, team weekly/yearly performance features, and a `label` target (go / punt / fg).
- **TIBER overlap:** High at the *source* level — TIBER already pulls nflverse via `nflreadpy`. No committed artifact covers play-level 4th-down decisions, but every column here is derivable in-house from the same upstream.
- **Leakage risk:** `epa`/`wp`/`def_wp` are model-derived values and `label` is the realized decision; the card draws no pregame/post-snap boundary, and the team-performance features have unverified as-of semantics (possible future-week contamination within a season). Unsafe near Forecast or validation without a full as-of audit.
- **Identity risk:** Team-code and `game_id` keyed, no player grain. `game_id` convention presumed nflverse-style but unverified; coach names are free text.
- **Classification:** **`rejected`** — no license, unattributed and unverifiable lineage, brand-new anonymous upload, and fully derivable in-house from an already-integrated upstream.
- **Next action:** None for this dataset. If 4th-down decision analytics are ever wanted, open a separate issue to derive an in-house play-level artifact from `nflreadpy` play-by-play with explicit as-of semantics.

### 2.2 `SebastianAndreu/24679_NFL_WR_Dataset_2025` — `schema_reference_only`

- **URL:** https://huggingface.co/datasets/SebastianAndreu/24679_NFL_WR_Dataset_2025
- **License / access / redistribution:** MIT, public, ungated. Redistribution technically permitted; card excludes real-money gambling and player-contract use.
- **Shape:** 1,918 WR player-game rows × 100+ columns, Parquet, single `full` split. Season 2025 only — and an **in-season snapshot** (created 2025-10-03, last modified 2025-10-30), not full-season.
- **Source lineage:** Card cites `nflverse/nflverse-data` play-by-play, processed by two pipelines (defense-adjusted metrics; quarter/WP-bucketed breakdowns). It is a **CMU course project** (24-679: Designing and Deploying AI/ML Systems). Derivation choices undocumented; 6 total downloads.
- **Public/synthetic/scraped/transformed/paid:** Transformed from a public source, attributed, course-project provenance.
- **Schema summary:** Targets, receptions, yards, air yards, YAC, TDs, EPA/WPA, target share, air-yards share, WOPR, aDOT, catch rate, explosive-play rates, red-zone/end-zone/third-down splits, quarter and WP-bucket breakdowns, defense-adjusted deltas, QB context (CPOE), weather/venue/surface, betting lines.
- **TIBER overlap:** **Direct.** TIBER's source-backed 2025 evidence (`player_weekly_usage_2025` 6,326 rows; `player_weekly_ppr_outcomes_2025` 6,394 rows; weeks 1–22, all positions) already covers this grain from the same upstream, with broader position and week coverage than this WR-only snapshot.
- **Leakage risk:** High for any 2025 Forecast/validation use — rows are postgame outcomes, and the defense-adjusted / league-average features are computed over an unspecified window that may fold later weeks into earlier rows.
- **Identity risk:** Player-ID scheme unverified (names vs GSIS IDs); no demonstrated join path to `tiber_identity_crosswalk_v1` (25 sleeper-only records); WR-only filter creates silent-population duplicate-semantics risk against TIBER's all-position artifacts.
- **Classification:** **`schema_reference_only`** — the license is clean, but the rows are redundant with TIBER's own governed source path. The value is the **feature vocabulary** (WOPR, aDOT, WP-bucketed splits, defense-adjusted deltas) for future role/usage contract design.
- **Next action:** May be cited as a public schema/feature-vocabulary reference. No mirror, no ingestion.

### 2.3 `Karmane/nfl-rest-advantage-travel-spot-research` — `schema_reference_only`

- **URL:** https://huggingface.co/datasets/Karmane/nfl-rest-advantage-travel-spot-research
- **License / access / redistribution:** **Contradictory.** Hub tag says MIT, but access is manually gated behind a **paid Gumroad purchase** with username/email verification. The effective terms are the unpublished purchase terms, not MIT. Per the issue guardrail on paid/gated datasets: fail closed — no purchase, no data use, redistribution rights unknown.
- **Shape:** 14,552 rows × 87 columns (727-row public preview), Parquet, single `data` split, 1.11 MB. 27 seasons of completed games; latest source game 2026-02-08. Created/modified 2026-06-11.
- **Source lineage:** Card cites nflverse game schedules and completed game records; team-side observations (one row per team per game).
- **Public/synthetic/scraped/transformed/paid:** Transformed from a public source, **paid/gated**.
- **Schema summary:** Schedule context (rest days, short-week flags, travel distance), market data (spread, moneyline, totals), environment, rolling team-trend metrics, and postgame outcomes (scores, ATS, over/under), with *claimed* pregame/postgame separation. 618 playoff games, 2,418 rest-advantage games, 581 short-week scenarios.
- **TIBER overlap:** Partial conceptual overlap with the team-week lanes (`team_week_raw_v0` contract, team pace/pass environment). No committed artifact covers rest/travel/schedule-spot context; the underlying schedule data is derivable in-house from nflverse.
- **Leakage risk:** Pregame/postgame separation is claimed but unverifiable without the paid data; rolling windows have unverified as-of semantics.
- **Identity risk:** Team-game grain; team-code and game-key conventions unverified against TIBER identity; no player surface.
- **Classification:** **`schema_reference_only`** — the paid gate plus contradictory license metadata fails the guardrail outright, but the public card is legitimately useful vocabulary for a future Teamstate schedule-context contract.
- **Next action:** May be cited (card/preview only) when scoping a future schedule/rest/travel context contract, sourced in-house from nflverse schedules.

### 2.4 `Karmane/nfl-anytime-touchdown-parlay-usage-trends` — `schema_reference_only`

- **URL:** https://huggingface.co/datasets/Karmane/nfl-anytime-touchdown-parlay-usage-trends
- **License / access / redistribution:** Same publisher, same pattern: MIT tag behind a **paid Gumroad manual gate**. Effective terms unpublished. Fail closed — no purchase, no data use.
- **Shape:** 78,641 rows × 126 columns (3,932-row public preview), Parquet, single `data` split, 9.01 MB. Seasons 2013–2024 (regular season + playoffs). One row per offensive skill player per completed game with logged snaps. Created/modified 2026-06-11.
- **Source lineage:** Card cites public nflverse sources — snap counts, player identifiers, weekly player stats, schedules — and states no proprietary touchdown-prop feeds were used.
- **Public/synthetic/scraped/transformed/paid:** Transformed from public sources, **paid/gated**, betting/parlay framing.
- **Schema summary:** ~50 pregame columns (snaps, snap%, rest context, moneyline/spread, implied team totals, rolling last-3/last-5 usage, opponent allowance rates), ~40 postgame outcome columns (TDs, yardage, shares, threshold flags such as `cleared_anytime_td`), ~36 metadata columns (player IDs/names, position, team, game IDs, weather, venue, timestamps).
- **TIBER overlap:** Direct grain overlap with the player-weekly usage lane (`player_weekly_usage_2025.source_backed.json`) and FORGE weekly inputs — though TIBER currently holds 2025 only versus this dataset's 2013–2024. All cited inputs are nflverse surfaces TIBER can pull first-hand.
- **Leakage risk:** Pregame/postgame mixing with unverifiable separation; rolling and opponent-allowance features have unverified as-of discipline; the betting framing bakes in target definitions (threshold flags) TIBER does not govern.
- **Identity risk:** Player IDs/names present but scheme unverified; join to `tiber_identity_crosswalk_v1` unproven; multi-season player-team movement semantics unverified.
- **Classification:** **`schema_reference_only`** — data use fails the paid/gated guardrail; the public card's pregame/postgame column discipline and rolling-usage feature shapes are legitimate design reference only.
- **Next action:** Citation-only feature-shape reference. Multi-season usage needs belong to the existing in-house multi-season coverage lane (`nflreadpy` ingestion), not to this dataset.

### 2.5 `keremberke/nfl-object-detection` — `rejected`

- **URL:** https://huggingface.co/datasets/keremberke/nfl-object-detection
- **License / access / redistribution:** Public, ungated — but **no Hub license tag** in API metadata, while the card body (Roboflow export boilerplate) claims Public Domain. The content is 9,947 frames of NFL game footage; broadcast/endzone imagery is copyrighted, so an unqualified Public Domain claim by a re-exporter is not credible without verification. Fail closed.
- **Shape:** 9,947 images (train 6,963 / valid 1,989 / test 995), COCO annotations, zipped images, 1.23 GB, 1280×720 stretched.
- **Source lineage:** Exported from Roboflow 2022-12-29 via `roboflow2huggingface`; original imagery source unstated. The helmet-label taxonomy (`helmet`, `helmet-blurred`, `helmet-difficult`, `helmet-partial`, `helmet-sideline`) matches the NFL Health & Safety Kaggle helmet-detection competition family, whose data carries its own competition terms. Chain of custody unverifiable.
- **Public/synthetic/scraped/transformed/paid:** Re-exported, provenance unclear. Stale (created 2022-12-30, last modified 2023-01-29).
- **Schema summary:** Bounding-box object detection with five helmet labels; no tabular schema, no player/team/game identity fields.
- **TIBER overlap:** None. TIBER-Data has no image/vision surface and no consumer for visual football-state data.
- **Leakage risk:** Not applicable to Forecast/player-history lanes.
- **Identity risk:** None at the schema level; the residual risk is depicting identifiable players in copyrighted footage — a rights question, not a join-key question.
- **Classification:** **`rejected`** — unverifiable provenance chain, non-credible license claim over probably-copyrighted footage, stale, and zero pipeline overlap. The *topic* (visual football-state / player-safety) could someday be a research lane, but this artifact must not be the vehicle; any future effort should re-source imagery under verified terms.
- **Next action:** None.

### 2.6 `leomaurodesenv/QASports2` and `PedroCJardim/QASports` — `benchmark_reference_only`

- **URLs:** https://huggingface.co/datasets/leomaurodesenv/QASports2 · https://huggingface.co/datasets/PedroCJardim/QASports
- **License / access / redistribution:** MIT Hub tags, public, ungated. **Caveat:** contexts are scraped from sports Fandom wikis, whose text is typically CC-BY-SA; an MIT relabel cannot strip the source text's attribution/share-alike obligations. Redistribution of the text is encumbered regardless of the tag.
- **Shape:** QASports2 — ~1.09M unique rows in the primary `all` configuration (train ~873k / validation ~109k / test ~109k), Parquet, 310 MB, plus 21 per-sport subsets (incl. American Football) that overlap the `all` configuration. The Hub-aggregate figure of 2,183,926 rows double-counts the overlapping configurations (~2x) and must not be used to size benchmark-reference work. QASports v1 — ~1.55M rows, 2.23 GB, CSV+Parquet, three sports (american football 704k, soccer 614k, basketball 232k); paper at Brazilian Symposium on Databases 2023; full data also on OSF.
- **Source lineage:** Extractive QA built over sports wiki pages (~54k documents for v1); processing scripts published at `github.com/leomaurodesenv/qasports-dataset-scripts`.
- **Public/synthetic/scraped/transformed/paid:** Scraped and transformed from public wikis; documented pipeline and paper trail.
- **Schema summary:** `qa_id`/`id_qa`, `context_id`, `context_title`, `context_url`, `context` (passage), `question`, `answer{text, offset}` — extractive QA grain.
- **TIBER overlap:** None. TIBER-Data has no QA/eval artifact surface.
- **Leakage risk:** Not applicable to Forecast/player-history lanes. For any future eval: wiki text embeds realized outcomes of historical events, and a benchmark built from it must treat contexts accordingly.
- **Identity risk:** Player/team references are free wiki text with no controlled IDs — unusable as an identity source; low practical risk since no join is proposed.
- **Classification:** **`benchmark_reference_only`** (both) — relevant solely to future TIBER-Bench / football-domain QA eval **design** (schema shape, split design, per-sport subsets). Prefer QASports2 as the current version; cite the paper. Do not mirror wiki text.
- **Next action:** Citation-only in future eval design work.

---

## 3. Guardrail compliance statement

This audit:

- downloaded **no** dataset contents and committed **no** dataset rows;
- created **no** governed mirrors and added **no** data to production artifacts;
- trained/reran **no** models and computed **no** acceptance metrics;
- changed **no** Fantasy, Forecast, Teamstate, Rookies, FORGE, or downstream consumer behavior;
- treated Hugging Face metadata as **descriptive, not sufficient, provenance** — every lineage claim above is marked verified/unverified accordingly;
- treated both paid/gated datasets as **unusable** absent explicit license/access review, which their contradictory metadata does not permit.

**No dataset reviewed in this audit is approved for production use or governed experimental use. There is currently no candidate for a governed experimental mirror.**

---

## 4. Allowed narrow follow-ups (each requires its own issue; none authorized here)

1. **In-house 4th-down decision artifact** — derive from `nflreadpy` play-by-play with explicit as-of semantics, if decision analytics are wanted. Not a mirror of `afzalmengal/nfl-4th-downs-dataset`.
2. **Schedule/rest/travel context spec for Teamstate** — a contract-only spec issue using the Karmane rest-advantage public card as vocabulary reference, sourced in-house from nflverse schedules.
3. **TIBER-Bench football QA eval design** — a design issue citing QASports2; no wiki-text mirroring.

## Appendix — Evidence consulted

Hugging Face dataset cards and Hub API metadata for the seven datasets above (cards, `api/datasets/*` JSON, published README/preview content), retrieved 2026-07-05. In-repo baseline for the overlap assessment: `TRUTH_SOURCES.md`, `AGENTS.md`, `docs/audits/player-availability-season-coverage-forecast-readiness-2026-06-30.{md,json}`, `docs/data/*` source-backed artifact docs, `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json` (via prior audit), `docs/contracts/team-week-raw-v0.md`.
