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

## Producing it

```bash
python3 scripts/promote_identity_crosswalk_rows.py \
    --forge-artifact /path/to/forge_player_static_v1.json \
    --forge-sha256 <sha256 of that file>
python3 scripts/promote_identity_crosswalk_rows.py --check   # validate the committed artifact
```

The promoter validates against `schemas/tiber_identity_crosswalk_v2.schema.json` **before** writing, refuses to write on a duplicate `provider_canonical_id`, and refuses to promote when the supplied FORGE artifact's bytes do not match `--forge-sha256`. That last guard is what keeps the authorization scoped: re-running against a different file at the same path cannot silently promote a different or larger slice.

## Current scope

68 records: 49 backing the promoted FORGE cohort, plus 19 provider ids carried forward from V1 and re-expressed as GSIS. The remaining candidate rows in `exports/candidates/identity_crosswalk/` stay candidate-tier; widening the slice is a separate operator decision.

`match_method` is the evidence tier and should be treated as such by consumers:

- `gsis_direct` / `espn_bridge` — provider-declared identifier agreement (`high`)
- `name_exact` — unique normalized-name + position match, no provider id available (`medium`)
- `verified_manual_seed` — operator-verified V1 seed (`high`)

Known gaps are recorded in `docs/audits/identity-crosswalk-v2-gsis-vocabulary-2026-08-09.md`: `Frank Gore Jr.` has no GSIS identity in the coverage universe and is not carried into V2; `Kenneth Gainwell` has no crosswalk row, so FORGE-cohort coverage is 49/50.
