# FFC ADP permission addendum — 2026-08-19

## Status

**RIGHTSHOLDER RESPONSE RECEIVED — SOURCE QUALIFICATION EVIDENCE UPDATED; NO ADAPTER OR INGESTION ACTIVATED BY THIS DOCUMENT.**

This addendum updates the source-qualification record for TIBER-Data issue #251 and the audit merged through PR #252. It records a direct email response from Fantasy Football Calculator (FFC) received on 2026-08-19 after the operator's August 17 follow-up.

## Request scope sent to FFC

The follow-up asked FFC to confirm whether the free, open-source TIBER Fantasy project may:

- make low-frequency automated requests to the FFC ADP API;
- store ADP observations;
- display attributed historical ADP observations; and
- identify any applicable rate limits, attribution requirements, retention restrictions, or redistribution restrictions.

## Rightsholder response

Sender: Brooke Mennella, `support@fantasyfootballcalculator.com`  
Received: 2026-08-19  
Subject: `Re: Permission request: FFC ADP API use in open-source TIBER Fantasy`

FFC's response states that TIBER may store and display ADP observations from Fantasy Football Calculator. FFC stated that it has no specific conditions around that permission and asked only that usage be respectful. The response also notes that FFC uses IP bans in cases of egregious use.

The email did not separately and affirmatively address automated access, provide a numeric request-rate limit, provide a retention limit, grant public-repository/redistribution rights, or specify a mandatory attribution format.

## Governance interpretation

This is first-party permission evidence and materially changes the rights posture recorded in #251 / PR #252.

The prior terminal posture — `dated_redraft_adp_source_v0_requires_rightsholder_or_definition_followup` — was driven in part by unresolved permission for retained and displayed FFC observations. The storage/display portion of that blocker is now resolved. Automated access and public redistribution remain separate unresolved rights questions because the reply did not explicitly grant them.

For TIBER governance, the evidence supports the following bounded interpretation:

```text
source: Fantasy Football Calculator ADP API
permission_evidence: direct_rightsholder_email
permission_received_at: 2026-08-19
storage_of_adp_observations: permitted
display_of_adp_observations: permitted
low_frequency_automated_use: unresolved_not_separately_granted
numeric_rate_limit: not_specified
retention_limit: not_specified
public_repository_or_redistribution_rights: unresolved_not_separately_granted
required_attribution_format: not_specified
operational_constraint_if_access_is_later_authorized: respectful_usage; avoid egregious request volume / IP-ban risk
```

### Important precision

The reply was responsive to a message that explicitly asked about low-frequency automated requests plus storage and display of attributed historical observations. The response affirmatively permits storage/display, but it does not separately enumerate automation or redistribution rights. TIBER therefore records those two dimensions as unresolved rather than converting silence into a grant.

## What is now true

- TIBER has direct written permission from FFC to store FFC ADP observations.
- TIBER has direct written permission from FFC to display FFC ADP observations.
- No specific retention condition was stated.
- No numeric rate limit was stated.
- FFC explicitly expects respectful usage and may IP-ban egregious use.
- Automated API access remains unresolved under the prior Terms/robots conflict until separately and affirmatively granted or otherwise resolved.
- Public GitHub/API redistribution remains unresolved; permission to display is not recorded as permission to redistribute source values through a public repository or API.

## What remains missing

This permission evidence does **not** by itself settle the remaining source-definition, rights, and implementation questions from #251, including:

- affirmative automation/API-access permission under the current Terms/robots posture;
- affirmative public-repository/API redistribution permission if a future candidate or promoted artifact would publish exact source values;
- exact population semantics of the FFC `ppr` endpoint (for example, whether all observations are strictly managed-redraft versus a broader mock population);
- exact source-native clocks and calculation-window semantics;
- identity coverage and a governed FFC-provider-ID → GSIS path;
- exact cadence policy for TIBER collection;
- a versioned ADP snapshot contract/schema/validator — `dated_redraft_adp_snapshot_v0` is currently a proposed contract sketch, not an implemented contract;
- adapter, immutable snapshot, candidate-artifact, promotion, scheduler, or downstream-consumer implementation.

## Operational policy recommendation

If automated access is separately authorized later, any FFC intake should remain conservative:

- low frequency;
- cached where practical;
- no burst polling;
- explicit attribution to Fantasy Football Calculator;
- append-only immutable TIBER snapshots rather than repeated raw mirroring;
- stop/review on HTTP 429, blocking, material terms change, or any request from FFC to change usage.

No numeric rate threshold is invented here because FFC did not provide one.

## Authority boundary

This document records evidence only. It does **not** authorize:

- an FFC adapter;
- automated or live market retrieval;
- public-repository/API redistribution of exact FFC observations;
- historical backfill;
- recurring scheduling;
- source promotion;
- TIBER-Fantasy consumption;
- rankings, advice, or market consensus;
- merge of any future implementation PR.

A later operator activation must bind the exact FFC market lane, resolved access/redistribution rights posture, cadence, request budget, identity path, implemented versioned snapshot contract/schema/validator, validation plan, and mandatory stop.

## Recommended next decision

Issue #251 can now be updated from a fully rights-blocked posture to a **storage/display-permitted but automation/redistribution-and-definition-gated** posture. The next bounded slice should resolve automated API access and public redistribution separately, and implement/review the proposed ADP snapshot contract before any publishing candidate adapter is activated. MFL remains an independent source witness rather than a substitute or consensus component.
