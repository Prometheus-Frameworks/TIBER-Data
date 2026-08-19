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

The email did not provide a numeric request-rate limit, retention limit, separate redistribution prohibition, or mandatory attribution format.

## Governance interpretation

This is first-party permission evidence and materially changes the rights posture recorded in #251 / PR #252.

The prior terminal posture — `dated_redraft_adp_source_v0_requires_rightsholder_or_definition_followup` — was driven in part by unresolved permission for retained and displayed FFC observations. That rights blocker is now substantially resolved for the scope requested in the August 17 email.

For TIBER governance, the evidence supports the following bounded interpretation:

```text
source: Fantasy Football Calculator ADP API
permission_evidence: direct_rightsholder_email
permission_received_at: 2026-08-19
storage_of_adp_observations: permitted
public_display_of_adp_observations: permitted
low_frequency_automated_use: permitted_under_respectful_usage_constraint
numeric_rate_limit: not_specified
retention_limit: not_specified
redistribution_prohibition: not_specified
required_attribution_format: not_specified
operational_constraint: respectful_usage; avoid egregious request volume / IP-ban risk
```

### Important precision

The reply was responsive to a message that explicitly asked about low-frequency automated requests plus storage and display of attributed historical observations. The response affirmatively permits storage/display and imposes only a general respectful-usage constraint. However, because the reply did not separately enumerate every requested sub-right, this addendum records the automation permission as a bounded interpretation of the responsive exchange rather than inventing a numeric or unlimited access grant.

## What is now true

- TIBER has direct written permission from FFC to store and display FFC ADP observations.
- No specific retention condition was stated.
- No numeric rate limit was stated.
- No separate redistribution prohibition was stated in the response.
- FFC explicitly expects respectful usage and may IP-ban egregious use.
- The earlier rights uncertainty in #251 / PR #252 should no longer be represented as unresolved in the same form.

## What remains missing

This permission evidence does **not** by itself settle the remaining source-definition and implementation questions from #251, including:

- exact population semantics of the FFC `ppr` endpoint (for example, whether all observations are strictly managed-redraft versus a broader mock population);
- exact source-native clocks and calculation-window semantics;
- identity coverage and a governed FFC-provider-ID → GSIS path;
- exact cadence policy for TIBER collection;
- adapter, validator, immutable snapshot, candidate-artifact, promotion, scheduler, or downstream-consumer implementation.

## Operational policy recommendation

Until a separate adapter activation is approved, any future FFC intake should remain conservative:

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
- live market retrieval beyond separately approved bounds;
- historical backfill;
- recurring scheduling;
- source promotion;
- TIBER-Fantasy consumption;
- rankings, advice, or market consensus;
- merge of any future implementation PR.

A separate operator activation should bind the exact FFC market lane, cadence, request budget, identity path, snapshot contract, validation plan, and mandatory stop.

## Recommended next decision

Issue #251 can now be updated from a rights-blocked posture to a source-qualified-but-definition/implementation-gated posture. A reasonable next operator decision is to open a bounded FFC candidate-adapter activation under the existing `dated_redraft_adp_snapshot_v0` contract, while keeping MFL as an independent source witness rather than substituting or averaging the two.
