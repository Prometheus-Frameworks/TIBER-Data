# TIBER Identity Crosswalk V2

`TIBER_IDENTITY_CROSSWALK_V2` is the TIBER-Data-owned identity bridge from external provider player identifiers to TIBER canonical player identifiers, **in the GSIS vocabulary**.

The promoted artifact lives at:

```text
exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json
```

## What changed from V1, and why

V1 maps provider ids to `tiber-data-player-2025-*` slugs. `FORGE_PLAYER_STATIC_V1` is keyed by **GSIS player id**, so a V1-vocabulary crosswalk resolves to zero FORGE rows while still reporting players as crosswalk-matched downstream. V2 changes exactly one semantic — the identifier vocabulary — plus the fields that follow from it:

| | V1 | V2 |
| --- | --- | --- |
| `tiber_player_id` | `^tiber-data-player-2025-*` | `^00-\d{7}$` (GSIS) |
| `match_method` | `verified_manual_seed` | + `gsis_direct`, `espn_bridge`, `name_exact` |
| `confidence` | `exact\|high\|provisional` | + `medium` (for `name_exact`) |
| `team` | required string | nullable (providers omit it for unsigned players) |
| `source_artifacts` | — | required, each pinned by sha256 |
| `id_vocabulary` | — | required, `gsis` |

**V1 is frozen, not replaced.** Its schema, builder, validator, artifact, and tests are untouched and still pass; it remains the contract of record for any consumer not yet migrated. The two artifacts must not be merged or consumed interchangeably.

## Original cohort producer (historical; regeneration now guarded)

```bash
python3 scripts/promote_identity_crosswalk_rows.py \
    --forge-artifact /path/to/forge_player_static_v1.json \
    --forge-sha256 <sha256 of that file>
python3 scripts/promote_identity_crosswalk_rows.py --check   # validate the committed artifact
```

The promoter validates against `schemas/tiber_identity_crosswalk_v2.schema.json` **before** writing, refuses to write on a duplicate `provider_canonical_id`, and refuses to promote when the supplied FORGE artifact's bytes do not match `--forge-sha256`. That last guard is what keeps the authorization scoped: re-running against a different file at the same path cannot silently promote a different or larger slice.

## Original scope

68 records: 49 backing the promoted FORGE cohort, plus 19 provider ids carried forward from V1 and re-expressed as GSIS. The remaining candidate rows in `exports/candidates/identity_crosswalk/` stay candidate-tier; widening the slice is a separate operator decision.

`match_method` is the evidence tier and should be treated as such by consumers:

- `gsis_direct` / `espn_bridge` — provider-declared identifier agreement (`high`)
- `name_exact` — unique normalized-name + position match, no provider id available (`medium`)
- `verified_manual_seed` — operator-verified V1 seed (`high`)

Known gaps are recorded in `docs/audits/identity-crosswalk-v2-gsis-vocabulary-2026-08-09.md`: `Frank Gore Jr.` has no GSIS identity in the coverage universe and is not carried into V2; `Kenneth Gainwell` has no crosswalk row, so FORGE-cohort coverage is 49/50.

## Accepted Draft Review extension — Data #263 / Fantasy #360

The operator accepted the four reviewed name_exact/medium edges in
[the exact proposal acceptance](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/264#issuecomment-5574349251).
`exports/promoted/draft_review/evidence_admission_v1.json` is the separate
acceptance receipt. The original proposal remains unchanged as historical
preparation evidence. Its audit now replays its immutable base commit rather
than validating subsequent files in the working tree.

The four-row admission stage produced 72 rows (the current review branch adds three more below). Its original 68 records are byte-for-byte
preserved; the four additional rows retain the reviewed candidate-generation
clocks and medium confidence. Artifact generation time is a separate receipt
clock, not a provider update time. The source_artifacts list pins the receipt.

Historical replay command at the four-row stage (now refuses to overwrite or check the newer Team extension; use the current command below):

```sh
python scripts/materialize_draft_review_identity_admission.py
python scripts/materialize_draft_review_identity_admission.py --check
python scripts/promote_identity_crosswalk_rows.py --check
```

The materializer requires git objects for the exact reviewed proposal commit;
missing objects fail rather than falling back to mutable source data. It rejects
changed edges, tiers, source pins, consumer windows or acceptance reference.
The old FORGE/V1-cohort CLI now refuses regeneration while this receipt exists,
because it would drop accepted rows. Its schema-only --check remains available.
No schema, V1 artifact, source statistics or candidate evidence is changed.
The accepted historical-use receipt does not assert deployed consumer readiness.

## Current branch preparation — Data #267 / #268

The review branch contains **75 records**: all original 72 unchanged plus Parker
Washington/9487, Drake London/8112 and Chris Rodriguez/10219. Match-method counts
are 23 `gsis_direct`, 6 `espn_bridge`, and 46 `name_exact`. The three new records
remain `name_exact` / `medium`; no provider-ID agreement is newly claimed.

The separate `exports/promoted/draft_review/team_identity_admission_v1.json`
receipt binds proposal commit `22e9843df74ced8f2856c6463c86b626a79683d1`, its
review and [operator preparation authorization](https://github.com/Prometheus-Frameworks/TIBER-Data/pull/268#issuecomment-5627117154).
Its status is `accepted_for_branch_preparation`. It preserves the prior bounded
2025 weeks 1–18 descriptive scope verbatim and grants no consumer regeneration,
merge, deployment or release. This describes prepared branch bytes, not active
production availability. The old four-row receipt stays byte-identical.

```sh
python scripts/materialize_team_identity_admission.py --check
python scripts/promote_identity_crosswalk_rows.py --check
python scripts/audit_team_identity_proposal.py --check
```

The materializer can also reproduce the prepared artifact without `--check`,
but refuses to overwrite anything other than the exact archived 72-row base or
its own exact 75-row result. Missing historical git objects fail closed. The
original four-row materializer refuses both CLI modes while the Team receipt
exists, preventing a 75→72 rollback. Its importable `build()` remains an archived
four-row-stage replay for tests.

The original #267 proposal MD/JSON remain archived and inactive. Its earlier
current-checkout-only replay description is superseded by this implementation:
only its superseded crosswalk input replays immutable base `b0c79de`; all other
inputs still check current bytes against their original pins. No weekly source,
candidate, schema or original receipt has been regenerated.

Historical recorded-week denominators are 16/12/12, not certified games played.
Parker's week 19 stays excluded; Rodriguez's dated candidate JAX context and
historical WAS observations stay distinct. Unknown source clocks and original
acquisition/terms limitations remain; no forecast, current role, roster or
transaction authority is introduced. See the paired
[mechanical preparation audit](../audits/team-identity-admission-2026-09-10.md).
