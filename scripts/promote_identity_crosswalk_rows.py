#!/usr/bin/env python3
"""Build TIBER_IDENTITY_CROSSWALK_V2 from operator-authorized candidate rows (issue #241).

V2 exists because of one semantic change: `tiber_player_id` is a GSIS player id
rather than a `tiber-data-player-2025-*` slug. FORGE_PLAYER_STATIC_V1 is now
GSIS-keyed, so a V1-vocabulary crosswalk resolves to zero FORGE rows while still
reporting players as crosswalk-matched downstream. Per AGENTS.md rule 6 the
contract is versioned rather than mutated: V1's schema, builder, validator, and
promoted artifact are left untouched and still pass their own checks.

Two slices are promoted, both in the GSIS vocabulary:

  1. every candidate row whose tiber_player_id appears in the pinned
     FORGE_PLAYER_STATIC_V1 artifact (the join the consumer needs), and
  2. every provider id already present in the promoted V1 crosswalk, so prior
     operator-verified coverage is carried forward rather than dropped.

Both source artifacts are pinned by sha256, so the promoted slice is
reproducible and auditable from the artifact alone.

Usage:
  python3 scripts/promote_identity_crosswalk_rows.py \
      --forge-artifact /path/to/forge_player_static_v1.json \
      [--forge-artifact-ref TIBER-FORGE:exports/promoted/forge_player_static/forge_player_static_v1.json] \
      [--forge-sha256 <expected sha256>] \
      [--candidates exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json] \
      [--existing exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json] \
      [--out exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json] \
      [--generated-at 2026-08-09T00:00:00Z] [--check]

--forge-artifact may be a local copy of the upstream file; --forge-artifact-ref
is the durable identity recorded as provenance, and --forge-sha256 pins the
exact bytes so a different file at the same path cannot silently promote a
different slice.
"""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ARTIFACT_ID = "TIBER_IDENTITY_CROSSWALK_V2"
SCHEMA_VERSION = "v2"
COVERAGE = "operator_promoted_slice_gsis_vocabulary_not_full_player_universe"
DEFAULT_FORGE_REF = "TIBER-FORGE:exports/promoted/forge_player_static/forge_player_static_v1.json"
DEFAULT_OUT = "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json"
SCHEMA_PATH = "schemas/tiber_identity_crosswalk_v2.schema.json"

CONFIDENCE_BY_TIER = {
    "gsis_direct": "high",      # provider-declared GSIS id agrees with the coverage universe
    "espn_bridge": "high",      # provider-declared ESPN id agrees with coverage provider_ids
    "name_exact": "medium",     # unique normalized-name + position match, no provider id available
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def validate_artifact(payload: dict) -> None:
    """Validate against the committed V2 schema. Fail closed."""
    from jsonschema import Draft202012Validator, FormatChecker

    schema = json.loads(Path(SCHEMA_PATH).read_text(encoding="utf-8"))
    checker = FormatChecker()
    checker.checks("date-time")(
        lambda v: not isinstance(v, str) or bool(
            datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
        )
    )
    Draft202012Validator(schema, format_checker=checker).validate(payload)


def build(args) -> dict:
    generated_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    forge_sha = sha256_file(args.forge_artifact)
    if args.forge_sha256 and args.forge_sha256 != forge_sha:
        raise SystemExit(
            f"refusing to promote: --forge-artifact sha256 {forge_sha} does not match "
            f"the pinned --forge-sha256 {args.forge_sha256}"
        )

    candidates = json.load(open(args.candidates))["rows"]
    by_sleeper = {c["sleeper_id"]: c for c in candidates}
    forge_ids = {r["player_id"] for r in json.load(open(args.forge_artifact))["rows"]}
    existing = json.load(open(args.existing))
    existing_records = existing.get("records") or existing.get("rows") or []

    selected: dict[str, dict] = {}
    for cand in candidates:
        if cand["tiber_player_id"] in forge_ids:
            selected[cand["sleeper_id"]] = cand

    carried, dropped = [], []
    for rec in existing_records:
        sid = rec["provider_player_id"]
        cand = by_sleeper.get(sid)
        if cand is None:
            # No GSIS identity exists for this provider id in the promoted coverage
            # universe. Retaining the V1 row would reintroduce a second vocabulary
            # that resolves to nothing, so it is dropped and reported by name.
            dropped.append(rec)
            continue
        if sid not in selected:
            selected[sid] = cand
            carried.append(rec["player_name"])

    records = [build_record(c, generated_at) for c in selected.values()]
    records.sort(key=lambda r: (r["tiber_player_id"], r["provider_canonical_id"]))

    canonical_ids = [r["provider_canonical_id"] for r in records]
    if len(set(canonical_ids)) != len(canonical_ids):
        raise SystemExit("refusing to write: duplicate provider_canonical_id in promoted records")

    tiers: dict[str, int] = {}
    for r in records:
        tiers[r["match_method"]] = tiers.get(r["match_method"], 0) + 1

    artifact = {
        "artifact_id": ARTIFACT_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "supported_providers": ["sleeper"],
        "coverage": COVERAGE,
        "id_vocabulary": "gsis",
        "coverage_notes": {
            "id_vocabulary": "tiber_player_id is a GSIS player id (00-XXXXXXX), matching "
                             "TIBER-FORGE FORGE_PLAYER_STATIC_V1 promoted rows.",
            "slice": "Rows backing the pinned FORGE cohort, plus prior promoted provider ids "
                     "re-expressed in the GSIS vocabulary.",
            "match_method": "gsis_direct/espn_bridge are provider-declared id agreements; name_exact "
                            "is a unique normalized-name + position match and carries medium confidence.",
        },
        "source_artifacts": [
            {
                "artifact": "IDENTITY_CROSSWALK_CANDIDATES_V0",
                "path": args.candidates,
                "sha256": sha256_file(args.candidates),
            },
            {
                "artifact": "FORGE_PLAYER_STATIC_V1",
                "path": args.forge_artifact_ref,
                "sha256": forge_sha,
            },
        ],
        "record_count": len(records),
        "record_count_by_match_method": dict(sorted(tiers.items())),
        "records": records,
    }
    validate_artifact(artifact)
    artifact["_report"] = {"tiers": tiers, "carried": carried, "dropped": dropped, "forge_ids": forge_ids}
    return artifact


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-artifact",
                    help="FORGE_PLAYER_STATIC_V1 artifact (may be a local copy of the upstream file); "
                         "required unless --check")
    ap.add_argument("--forge-artifact-ref", default=DEFAULT_FORGE_REF,
                    help="durable identity recorded as provenance for --forge-artifact")
    ap.add_argument("--forge-sha256", default=None,
                    help="expected sha256 of --forge-artifact; refuses to promote on mismatch")
    ap.add_argument("--candidates", default="exports/candidates/identity_crosswalk/identity_crosswalk_candidates_v0.json")
    ap.add_argument("--existing", default="exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v1.json")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--generated-at", default=None)
    ap.add_argument("--check", action="store_true",
                    help="validate the committed artifact instead of writing a new one")
    args = ap.parse_args()

    if args.check:
        payload = json.loads(Path(args.out).read_text(encoding="utf-8"))
        validate_artifact(payload)
        print(f"Validated {args.out}")
        return 0

    if not args.forge_artifact:
        ap.error("--forge-artifact is required unless --check")

    artifact = build(args)
    report = artifact.pop("_report")
    json.dump(artifact, open(args.out, "w"), indent=1)

    promoted_ids = {r["tiber_player_id"] for r in artifact["records"]}
    print(f"promoted {artifact['record_count']} records {dict(sorted(report['tiers'].items()))}")
    print(f"  forge-cohort slice: {len(report['forge_ids'] & promoted_ids)}/{len(report['forge_ids'])} FORGE rows joinable")
    print(f"  carried forward from promoted V1: {len(report['carried'])}")
    if report["dropped"]:
        print(f"  DROPPED (no GSIS identity available): {[d['player_name'] for d in report['dropped']]}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
