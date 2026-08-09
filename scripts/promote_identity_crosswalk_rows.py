#!/usr/bin/env python3
"""Promote a scoped slice of identity-crosswalk CANDIDATES into the promoted artifact (issue #241).

Operator-gated by repo governance: this script only runs a promotion the
operator has already authorized, and it promotes a bounded slice rather than
the full 1,106-row candidate set. Two slices are promoted:

  1. every candidate row whose tiber_player_id appears in TIBER-FORGE's
     promoted FORGE_PLAYER_STATIC_V1 artifact (the join the consumer needs), and
  2. every provider id already present in the existing promoted crosswalk,
     re-expressed in the GSIS vocabulary so prior operator-verified coverage
     survives the vocabulary change instead of being dropped.

The vocabulary change is the reason this exists. The previous promoted rows
mapped provider ids to `tiber-data-player-2025-*` identifiers; FORGE's promoted
artifact is now keyed by GSIS player_id, so legacy rows would resolve to
nothing while still counting as "crosswalk matched" downstream — a silently
misleading diagnostic. Promoting a single-vocabulary artifact keeps matched
and scored meaning the same thing.

Usage:
  python3 scripts/promote_identity_crosswalk_rows.py \
      --forge-artifact /path/to/forge_player_static_v1.json \
      [--candidates exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json] \
      [--existing exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json] \
      [--out exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json] \
      [--generated-at 2026-08-09T00:00:00Z]
"""
import argparse, json, sys
from datetime import datetime, timezone

CONFIDENCE_BY_TIER = {
    "gsis_direct": "high",      # provider-declared GSIS id agrees with the coverage universe
    "espn_bridge": "high",      # provider-declared ESPN id agrees with coverage provider_ids
    "name_exact": "medium",     # unique normalized-name + position match, no provider id available
}


def build_record(cand: dict, generated_at: str) -> dict:
    tier = cand["match_tier"]
    ev = cand.get("evidence") or {}
    return {
        "provider": "sleeper",
        "provider_player_id": cand["sleeper_id"],
        "provider_canonical_id": f"sleeper:{cand['sleeper_id']}",
        "tiber_player_id": cand["tiber_player_id"],
        "player_name": cand["player_name"],
        "position": cand["position"],
        "team": ev.get("sleeper_team") or None,
        "confidence": CONFIDENCE_BY_TIER[tier],
        "match_method": tier,
        "source": "exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json",
        "source_updated_at": generated_at,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-artifact", required=True,
                    help="TIBER-FORGE promoted forge_player_static_v1.json (defines the required join slice)")
    ap.add_argument("--candidates", default="exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json")
    ap.add_argument("--existing", default="exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json")
    ap.add_argument("--out", default="exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json")
    ap.add_argument("--generated-at", default=None)
    args = ap.parse_args()

    generated_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    candidates = json.load(open(args.candidates))["rows"]
    by_sleeper = {c["sleeper_id"]: c for c in candidates}
    forge_ids = {r["player_id"] for r in json.load(open(args.forge_artifact))["rows"]}
    existing = json.load(open(args.existing))
    existing_records = existing.get("records") or existing.get("rows") or []

    selected: dict[str, dict] = {}
    for cand in candidates:
        if cand["tiber_player_id"] in forge_ids:
            selected[cand["sleeper_id"]] = cand

    # Carry prior operator-verified coverage forward in the new vocabulary.
    carried, dropped = [], []
    for rec in existing_records:
        sid = rec["provider_player_id"]
        cand = by_sleeper.get(sid)
        if cand is None:
            # No GSIS identity exists for this provider id in the promoted
            # coverage universe. Retaining the legacy row would reintroduce a
            # second id vocabulary that resolves to nothing, so it is dropped
            # here and reported for operator visibility.
            dropped.append(rec)
            continue
        if sid not in selected:
            selected[sid] = cand
            carried.append(rec["player_name"])

    records = [build_record(c, generated_at) for c in selected.values()]
    records.sort(key=lambda r: (r["tiber_player_id"], r["provider_canonical_id"]))

    canonical_ids = [r["provider_canonical_id"] for r in records]
    if len(set(canonical_ids)) != len(canonical_ids):
        print("refusing to write: duplicate provider_canonical_id in promoted records", file=sys.stderr)
        return 1

    tiers = {}
    for r in records:
        tiers[r["match_method"]] = tiers.get(r["match_method"], 0) + 1

    artifact = {
        "artifact_id": "TIBER_IDENTITY_CROSSWALK_V1",
        "schema_version": "v1",
        "generated_at": generated_at,
        "supported_providers": ["sleeper"],
        "coverage": "operator_promoted_slice_gsis_vocabulary_not_full_player_universe",
        "coverage_notes": {
            "id_vocabulary": "tiber_player_id is a GSIS player id (00-XXXXXXX), matching "
                             "TIBER-FORGE FORGE_PLAYER_STATIC_V1 promoted rows.",
            "slice": "Rows backing the promoted FORGE cohort, plus prior promoted provider ids "
                     "re-expressed in the GSIS vocabulary.",
            "match_method": "gsis_direct/espn_bridge are provider-declared id agreements; name_exact "
                            "is a unique normalized-name + position match and carries medium confidence.",
        },
        "source_artifacts": [args.candidates, args.forge_artifact],
        "record_count": len(records),
        "record_count_by_match_method": dict(sorted(tiers.items())),
        "records": records,
    }

    json.dump(artifact, open(args.out, "w"), indent=1)
    print(f"promoted {len(records)} records {dict(sorted(tiers.items()))}")
    print(f"  forge-cohort slice: {len(forge_ids & {r['tiber_player_id'] for r in records})}/{len(forge_ids)} FORGE rows joinable")
    print(f"  carried forward from prior promoted artifact: {len(carried)}")
    if dropped:
        print(f"  DROPPED (no GSIS identity available): {[d['player_name'] for d in dropped]}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
