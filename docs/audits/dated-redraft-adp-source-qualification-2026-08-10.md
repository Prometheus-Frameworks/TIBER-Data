# Dated redraft ADP source qualification — 2026-08-10

## Decision

Fantasy Football Calculator (FFC) is the strongest technical candidate for a narrow, source-specific 2026 PPR 12-team mock-draft ADP lane. The endpoint's exclusion of dynasty, rookie, keeper, or other draft populations was not bound, so “redraft” remains the question being qualified rather than an observed source fact. FFC is not yet admissible for a governed TIBER-Data adapter.

The official API page, last updated 2018-07-17, permits personal and commercial API use, requests attribution, and says the data updates daily. The newer Terms of Service, last updated 2025-10-13, restrict systematic retrieval, database compilation, automated extraction, aggregation, republication, public display, distribution, and commercial exploitation outside an applicable exception or express permission. The current `robots.txt` also disallows `/api/` for the general user agent. The API page may be a specific exception for ordinary application use, but it does not clearly authorize TIBER's proposed once-daily immutable archive, normalized historical database, public GitHub artifacts, or downstream redistribution.

This is a source-governance assessment, not legal advice. Observed source statements are separated below from TIBER's conservative admission inference.

**Terminal decision:** `dated_redraft_adp_source_v0_requires_rightsholder_or_definition_followup`

## Authority and boundary

- Authority: operator-approved D1 source qualification in TIBER-Data issue #251.
- Parent readiness work: issue #235 and draft PR #248.
- Evidence cutoff: `2026-08-10T20:12:10Z`.
- Pinned TIBER-Data base: `44296134a178f9d53fd7eda01a94548e76160d29`.
- Candidate source: FFC ADP REST API, `ppr`, 12 teams, 2026, all-player response.
- This packet contains no player ADP rows or values. No market body was persisted, but the exact current endpoint was contacted twice; the second GET exceeded issue #251's one-probe ceiling. The deviation is disclosed below and no further source call is authorized.
- No adapter, snapshot, history, scheduler, source purchase, credential, license acceptance, identity promotion, downstream binding, merge, or deployment is authorized here.
- Issue #251 acceptance is not met and the issue must remain open. The source terminal above remains defensible, but the process nonconformance requires an explicit operator disposition before this audit PR can be considered for merge or any separate outreach can be authorized.

## Exact market definition

The provisional lane name is `ffc_mock_ppr_12_candidate_v0`. It must not be called redraft until FFC confirms which draft populations the `/ppr` endpoint includes. If eventually admitted, it must remain source-specific and must not be described as “the market,” “consensus ADP,” or managed-league ADP.

| Dimension | Contract |
|---|---|
| Provider/product | Fantasy Football Calculator ADP REST API |
| Endpoint configuration | `ppr`, `teams=12`, `year=2026` |
| Draft type | Unknown: the inspected evidence does not prove that `/ppr` excludes dynasty, rookie, keeper, or other mock populations |
| Population | Human selections in FFC-hosted mock drafts |
| Computer selections | Excluded by FFC before averaging |
| Player population | All positions returned by the source; no position query was used |
| Metric | Source-supplied average draft position and supporting source fields |
| Generalizability | FFC mock-draft behavior only; not a universal or managed-league market |
| Team-count confidence | The request specified 12; the exact response metadata value was not retained, and population/filter semantics require confirmation |

The 12-team semantics remain unresolved because TIBER-Fantasy PR #304's same-day 10- and 12-team PPR prototypes reported the same source window and draft count and substantively identical source values apart from formatted pick notation. This is a definition warning, not evidence that the provider ignores team count.

## Official FFC evidence receipts

All hashes below are SHA-256 over decoded response-body bytes after automatic HTTP content decoding. They are not TLS-wire or compressed-transfer digests.

| Evidence | Source state | Retrieval | Decoded bytes | SHA-256 |
|---|---|---:|---:|---|
| [ADP REST API help](https://help.fantasyfootballcalculator.com/article/42-adp-rest-api) | Updated 2018-07-17; API use permission, attribution request, daily cadence | 2026-08-10T19:59:05.805Z–19:59:18.546Z | 15,464 | `4a4bbdc61edba9381fa2e03ae5f41eb319478ca976a0bd69f8ae10b4ffd79014` |
| [ADP methodology](https://help.fantasyfootballcalculator.com/article/34-average-draft-position-adp-data) | Updated 2018-07-17; mock-draft aggregation, computer picks excluded | 2026-08-10T19:59:18.555Z–19:59:19.026Z | 15,300 | `878dfde5d6271a10b20663dbd3c9658782cdf916138b9ffc10aff997d8ccdfa9` |
| [Terms page](https://fantasyfootballcalculator.com/terms-of-service) | Deterministic HTML embeds Termly UUID `2ef2a813-520e-416e-8542-126123f37364` | 2026-08-10T19:59:19.026Z–19:59:24.315Z | 39,610 | `51cd23d7062dee728100a1313002e3b85f6a738e16f57c1bf06be3c9839d6668` |
| Embedded Terms policy content | Policy updated 2025-10-13; Left Brain Sports LLC d/b/a FFC; content digest pinned | 2026-08-10T19:59:24.316Z–19:59:29.084Z | 179,092 JSON bytes | `299f9442dc18ebc6c48090fc7318b51cd410c98c21603ffbc9210992f13e22b9` |
| [Privacy page](https://fantasyfootballcalculator.com/privacy-policy) | Deterministic HTML embeds Termly UUID `9a379394-6a14-42ba-9c4a-8110641bc62c` | 2026-08-10T19:59:29.086Z–19:59:34.936Z | 39,606 | `fa36c70b7517d1abe252db68a9eeb0f437526b27c753e5d6763cfc4278a22d51` |
| Embedded privacy policy content | Policy updated 2025-10-13; no data-license effect | 2026-08-10T19:59:55.646Z–20:00:00.513Z | 224,654 JSON bytes | `eb3267eae283e0665865c2e4deb81708f329c323aa9dc165e36db7414ea2d9d4` |
| [robots.txt](https://fantasyfootballcalculator.com/robots.txt) | General user agent disallows `/api/`; crawler guidance, not a data license | 2026-08-10T20:00:00.522Z–20:00:05.919Z | 245 | `00008501967eca4348089f1f07a013cae145bdd7607a0e3e1d50e25e95fc7393` |

The Terms embedded-content UTF-8 string additionally hashes to `b0e76d59e9cb1aea22acb7124e7044333ac77ee86990d41a92b27ef127d7eaf3`. The privacy embedded-content UTF-8 string hashes to `0c22c86371720024a20c8f90cc39cee852cca299295c672af5dc2d0b83d5ea4b`.

## Rights ledger

| Use | Observed evidence | Admission status |
|---|---|---|
| Occasional API call | Older API page permits personal/commercial use with attribution | Allowed with conditions as an observed API statement; scheduled activation still needs clarification |
| Raw response retention | No express archival grant; newer Terms restrict database compilation | Requires written permission |
| Normalized exact-value storage | No express grant; normalization still creates a compiled database | Requires written permission |
| Ephemeral internal analysis | Consistent with the API page if occasional, attributed, and non-persistent | Allowed with conditions |
| Historical backfill | Annual archives are described, but no dated daily archive or reuse grant was found | Requires written permission and source availability |
| Public repository | No express right to publish raw or normalized snapshots | Requires written permission |
| Public API | No express bulk or sublicensed redistribution right | Requires written permission |
| Public UI | Embedded/derived display appears contemplated by API docs, but TIBER's persistent history dependency is unresolved | Requires written confirmation for governed activation |
| Redistribution | Newer Terms restrict aggregation/republication/distribution outside permission | Requires written permission |

TIBER's inference is deliberately narrower than either source document in isolation. The API page appears to authorize ordinary app use; the newer Terms and robots rule create enough uncertainty that immutable retention and public redistribution cannot be inferred.

## Probe execution and scope deviation

Two separate GET requests were made to the exact 2026 PPR 12-team endpoint. Issue #251 permitted at most one. The second request was therefore outside the execution ceiling even though both calls were bounded and neither body was persisted.

1. From local tool invocation `2026-08-10T19:49:03.035713955Z` through completion `19:49:08.725994295Z`, `curl -D - -o /dev/null` made a full GET. The 49,006-byte representation was transferred, discarded to `/dev/null`, not parsed, not hashed, and not persisted. This was a header-metadata probe, not an HTTP HEAD request.
2. From `2026-08-10T20:00:05.920Z` through `20:00:06.362Z`, a second GET transiently processed the response for byte length, digest, and schema keys. That call produced the receipt below.

An official API-documentation example for the 2018 standard 12-team endpoint was also opened through the web tool while inspecting the documentation. Its player rows appeared only in transient tool output; no row was copied into a file or this packet. It was not the named current 2026 PPR endpoint, but is disclosed to avoid understating source access.

The first request's server `Date` header was later than the locally recorded completion clock. Local invocation/completion bounds are therefore authoritative for the receipt; server `Date` is retained only as a response header and never used as a TIBER retrieval clock.

## Schema-probe receipt

The second GET produced the following schema-only receipt:

- HTTP status: 200.
- Decoded body size: 49,006 bytes.
- Decoded body SHA-256: `75b5784c2af5c2b71176375a1837fb795fedb86800b649459ef719f7fe626af8`.
- The body was held transiently only to compute byte length, digest, and schema keys. No player row or value was printed or persisted.
- The source publishes no formal JSON Schema observed in this audit.
- Observed top-level keys: `status`, `meta`, `players`.
- Observed metadata keys: `type`, `teams`, `rounds`, `total_drafts`, `start_date`, `end_date`.
- The values for those six metadata fields were not retained. Therefore the exact response type, echoed team count, round count, sample size, and calculation-window dates are unavailable and not reproducibly pinned. They must not be reconstructed from PR #304 or obtained through another call in this slice.
- Observed player-field names: `player_id`, `name`, `position`, `team`, `adp`, `adp_formatted`, `times_drafted`, `high`, `low`, `stdev`, `bye`.
- Response `Content-Type` was `text/html; charset=utf-8` even though the body parsed as JSON.
- Cache headers included `max-age=3600`; `Last-Modified` was `2026-08-10T19:47:07Z`.
- No ETag, semantic revision identifier, generated timestamp, rate-limit header, or retry-after header was present.

The `Last-Modified` header is an HTTP representation/cache clock only. It is not documented as an ADP generation, correction, or market-as-of clock.

## Clocks, cadence, and correction behavior

| Clock | State |
|---|---|
| Market sample window | Field names were observed, but values were not retained; exact window, timezone, and inclusion semantics are unavailable |
| Generated at | Unavailable |
| Source as-of | Unavailable beyond the sample-window fields |
| Available at | Unavailable |
| Retrieval | Fully observed and recorded above |
| HTTP representation modified | Observed; not promoted to a semantic clock |
| Semantic revision/correction | Unavailable |
| Downstream claim cutoff | `2026-08-10T20:12:10Z` |

The API page says the data updates once per day and asks clients not to call frequently. No numeric quota, preferred user agent, update hour, correction policy, replay token, or revision clock was found. Even if rights are granted, the first adapter contract should be once daily at most until the provider supplies a more exact envelope.

## History assessment

FFC documents annual historical ADP back to 2007. That is not evidence of original daily point-in-time snapshots or a lawful trailing-12-month export. A value retrieved today must not be backdated.

Current history status is `prospective_only` for a governed watch and only after rights are confirmed. The initial lane would have partial history; it may not claim 12-month movement until 12 months of admitted observations exist or the rightsholder supplies an authorized dated archive with provenance.

## Identity assessment

- The probe exposes a source-local integer `player_id`; its stability and reuse rules are undocumented.
- It must be retained, if permitted, only as `ffc_player_id`.
- No FFC-to-GSIS edge or cross-platform identifier was observed.
- Names, team, position, ADP, and absence from a snapshot are forbidden canonical joins.
- Required player states remain distinct: ranked, explicitly unranked, missing from snapshot, and identity unresolved. Missing or unresolved rows cannot be called unranked.

Pinned adjacent Data evidence at main `44296134a178f9d53fd7eda01a94548e76160d29` is Sleeper-only:

- Candidate crosswalk `exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json`, blob `ed340fc0d55f37b0f2143608d9aa02762e26e301`, SHA-256 `45a69f2176104249d3ea416ccdd71dadd8196c6f5dfe3f1bf4e303580ecf47cd`, 1,106 candidate rows plus 24 review rows in a 1,130-player universe.
- Promoted V2 slice `exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json`, blob `feb570db234a1e47883be80a4e186e61dac2e048`, SHA-256 `e6c6f8720352f1b94bf0a60fc5c6a2af7995b2b86b87ef9170b18ef3fcc96f9c`, 68 records, supported provider `sleeper`.

Neither artifact authorizes an FFC join. Any FFC bridge is a separate candidate/review lane and must fail closed without an exact source-specific mapping.

## Prototype evidence, not source authority

TIBER-Fantasy PR #304 is pinned only as `schema_reference_only`:

- head `39eee962aa754781e4c3f8a9939d96f42a355293`;
- merge commit `93e26825fb4dbafec722083a2704a0cc59f5aac5`;
- fetcher blob `e31234596e951a64f7b22714b158ae3161f09745`;
- README blob `7406c03e730286895bb0833a9f2a74889ddd4d4f`.

It demonstrates useful parameter and wrapper vocabulary, but not an admitted Data source. Same-day runs can overwrite date-grain filenames; `latest` overwrites by design; no raw source digest, immutable event ID, revision contract, rights pin, or governed FFC identity edge exists. Its committed player snapshots must not be copied into this packet or promoted through this decision.

## Alternatives matrix

| Source | Fit | Rights/method state | Decision for this lane |
|---|---|---|---|
| MyFantasyLeague ADP API | Aggregate hosted-draft ADP with useful filters | API docs encourage caching, but newer site terms conflict; PPR and period semantics are not exact enough | Rightsholder and definition follow-up |
| Sleeper public draft API | Rich per-draft metadata | No representative global discovery/aggregate endpoint; July 2026 terms require authorization for systematic extraction | Reject as a representative market source |
| Underdog Fantasy | Strong best-ball market if licensed | No public approved ADP feed found; automated access restricted; wrong market type for managed redraft | Unavailable for this lane |
| SportsDataIO/FantasyData | Potential licensed feed and persistent provider IDs | Contract-dependent rights; public methodology omits population, team count, window, and revision semantics; may syndicate FFC rather than add an independent market | Commercial/rightsholder follow-up |

No alternative clears both the rights and exact-market-definition gate today.

The alternatives were qualified only from their official public surfaces on 2026-08-10; no player payload was retained:

- **MyFantasyLeague / First Pick Labs, Inc.** exposes an ADP export through its developer program. The documented filters include team count, a PPR flag, keeper/redraft/rookie, mock/non-mock, and named periods, and the API returns a last-updated value. However, the PPR flag does not distinguish half from full PPR, exact recent-period dates and broader roster/scoring controls are incomplete, and the API's caching guidance conflicts with newer site terms restricting reproduction, publication, distribution, caching, scraping, or extraction without written permission. Provider identity and any GSIS edge require a separate audit. Original dated daily history and revision behavior are undocumented.
- **Sleeper / Blitz Studios, Inc. and affiliates** exposes read-only drafts, picks, and player data and documents a general request ceiling below 1,000 calls per minute, but there is no market-specific cadence or official representative global draft-discovery/aggregate ADP endpoint. A sample built only from known users, leagues, or draft IDs would be incomplete and selection-biased. The 2026-07-24 Terms require separate authorization for the proposed systematic extraction and redistribution. Per-draft clocks do not cure the population defect.
- **Underdog Sports, LLC d/b/a Underdog Fantasy** has no public approved ADP feed observed in this audit, restricts automated access outside an approved client/API, and represents a best-ball contest market rather than the requested redraft mock population. No source key, dated history, or semantic clocks were available for qualification.
- **SportsDataIO** advertises fantasy ADP fields, persistent provider IDs, and a licensed historical product. Production use and all retention/redistribution rights are contract-dependent. Public documentation does not bind source population, sample size, team count, full-PPR semantics, calculation window, availability, correction, or revision behavior. FFC also states that its ADP is syndicated through FantasyData, so this may be a licensed delivery of the same market rather than an independent comparator.

## Required rightsholder confirmation

No message was sent during this audit. The first required action is operator disposition of the probe-budget nonconformance. Only after a separate outreach authorization should a request ask Left Brain Sports LLC / FFC to confirm in writing:

1. once-daily automated calls for each named market configuration;
2. whether the API page is the intended exception to the 2025 Terms and `/api/` robots rule;
3. immutable raw-response retention;
4. normalized exact-value and historical storage;
5. public GitHub publication, public UI display, public API use, and bulk redistribution boundaries;
6. required attribution wording and placement;
7. numeric request ceiling, preferred user agent/contact, and update hour;
8. `player_id` stability, reuse, and retirement rules;
9. exact 10-/12-team population semantics;
10. whether `/ppr` contains only ordinary redraft, non-keeper, non-dynasty, non-rookie mock drafts;
11. the returned metadata values and their exact source-window semantics;
12. source generation, availability, correction, and revision clocks; and
13. whether an authorized original dated prior-12-month export exists.

Contact observed in the Terms: `support@fantasyfootballcalculator.com`. Sending this request is an external action and needs separate operator authorization.

## Candidate-adapter prerequisites

A later candidate-adapter issue may be proposed only after all blocking items are bound:

1. written rightsholder permission covering the intended retention, storage, display, and redistribution modes;
2. exact source-specific market name and population contract;
3. confirmed request cadence, attribution, and correction/revision behavior;
4. append-only timestamped receipts with source-body digest and immutable observation ID;
5. validator and negative fixtures for schema drift, wrong format/team/season, missing metadata, clock failure, and duplicate observations;
6. source-local `ffc_player_id` preservation plus a separate reviewed FFC-to-GSIS candidate bridge;
7. explicit missing/unranked/unresolved semantics;
8. prospective-only history until admitted dated evidence exists; and
9. no `latest` advancement unless a fully validated immutable candidate is retained.

## Prohibited next steps

Until a later operator activation, do not build an adapter, call the market endpoint again, retain player rows, normalize values, reconstruct or backdate history, schedule retrievals, publish a snapshot, expose values in an API/UI, create an FFC identity crosswalk, accept a license, purchase a source, merge this draft, or bind any downstream model. The extra GET cannot be undone; the control response is disclosure, immediate stop, and no source admission from this slice.
