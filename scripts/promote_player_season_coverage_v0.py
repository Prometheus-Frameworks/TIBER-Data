"""Promote player_season_coverage_v0 from candidate evidence to a governed artifact (TIBER-Data #192).

Deterministic, network-free promotion: this script reads the sha256-pinned candidate artifact,
fails closed unless every governance gate passes, and writes the promoted export + manifest.
Running it twice produces byte-identical output.

Fail-closed gates, in order:
  1. candidate artifact sha256 must equal the pin recorded across #100/#104/#108/#110/#112,
  2. the full candidate validator (schema + business rules, incl. the #192 all-source allow-list)
     must pass with zero errors,
  3. every record must sit inside the declared envelope scope (REG only, QB/RB/WR/TE only),
  4. the promoted payload must validate against schemas/player_season_coverage_v0_promoted.schema.json
     (identical per-record contract; promotion changes only the envelope).

Promotion does NOT authorize Forecast production binding: Forecast consumption of the promoted
artifact requires its own downstream gate/review (see the consumer_safety and
forecast_compatibility_note blocks embedded in the promoted envelope).

Usage: python scripts/promote_player_season_coverage_v0.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import jsonschema

CANDIDATE_PATH = Path("data/processed/evidence/player_season_coverage_2022_2025.source_backed.json")
PINNED_CANDIDATE_SHA256 = "39b6e71e36d667509221137f2b712143fe5fdccf5423f50e81b5c7a138c0072b"
PROMOTED_SCHEMA_PATH = Path("schemas/player_season_coverage_v0_promoted.schema.json")
PROMOTED_PATH = Path("exports/promoted/nfl/player_season_coverage_v0.json")
MANIFEST_PATH = Path("exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json")

PROMOTED_STATUS = "promoted_governed_artifact"
PROMOTED_AT = "2026-07-03T00:00:00Z"  # fixed review date: keeps promotion output deterministic
SEASON_TYPE_SCOPE = {"REG"}
POSITION_SCOPE = {"QB", "RB", "WR", "TE"}

# The promotion decision enum for #192. Deliberately NO value authorizes Forecast binding,
# production signal, or product output.
PROMOTION_DECISIONS = (
    "promote_player_season_coverage_v0",
    "do_not_promote_requires_fixes",
    "do_not_promote_requires_new_source_artifact",
    "promotion_review_invalid_must_not_use",
)

CONSUMER_SAFETY = {
    "allowed": [
        "source-backed player-season production/history evidence (REG, QB/RB/WR/TE, approved seasons)",
        "row-level source_refs / identity_confidence / provenance",
        "team-of-record context (teams[], primary_team, primary_team_rule) as production-row context only",
    ],
    "not_allowed": [
        "current active roster status",
        "player availability or injury status",
        "depth chart role",
        "ownership/team membership",
        "product advice or fantasy rankings/start-sit/trade/draft output",
        "Forecast production binding without a separate Forecast issue and gate",
    ],
}

FORECAST_COMPATIBILITY_NOTE = (
    "Forecast may consume this promoted artifact only through a separate Forecast-side gate that "
    "re-verifies sha/provenance, enforces target-season leakage splits structurally, and considers a "
    "production-only feature contract given the Forecast #116 attribution finding (the production "
    "family carries essentially all of the candidate signal). No product-facing claim is authorized "
    "until a Forecast production-binding review passes. This promotion changes nothing in Forecast."
)


def _load_validator_module():
    module_path = Path(__file__).resolve().parent / "validate_player_season_coverage_v0.py"
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_envelope_scope(records: list[dict]) -> list[str]:
    """Records must sit inside the scope the promoted envelope declares (fail closed, no filtering)."""
    errors: list[str] = []
    for idx, row in enumerate(records):
        if row.get("season_type") not in SEASON_TYPE_SCOPE:
            errors.append(f"record[{idx}]: season_type {row.get('season_type')!r} outside promoted scope {sorted(SEASON_TYPE_SCOPE)}")
        if row.get("position") not in POSITION_SCOPE:
            errors.append(f"record[{idx}]: position {row.get('position')!r} outside promoted scope {sorted(POSITION_SCOPE)}")
    return errors


def build_promoted_payload(candidate: dict, candidate_sha256: str, validator_module) -> dict:
    """Pure transformation candidate -> promoted payload. Fails closed on any gate violation."""
    if candidate_sha256 != PINNED_CANDIDATE_SHA256:
        raise SystemExit(
            f"FAIL CLOSED: candidate sha256 {candidate_sha256} does not match the pin {PINNED_CANDIDATE_SHA256}. "
            "If the candidate was intentionally regenerated, re-run the full governance review and update the pin first."
        )
    errors = validator_module.validate_payload(candidate)
    if errors:
        raise SystemExit(f"FAIL CLOSED: candidate validator reported {len(errors)} error(s); first: {errors[0]}")
    records = candidate["records"]
    scope_errors = check_envelope_scope(records)
    if scope_errors:
        raise SystemExit(f"FAIL CLOSED: {len(scope_errors)} record(s) outside promoted scope; first: {scope_errors[0]}")

    return {
        "artifact_id": "player_season_coverage_v0",
        "spec_version": "player_season_coverage_v0_promoted_v1",
        "status": PROMOTED_STATUS,
        "generated_at": candidate["generated_at"],
        "promoted_at": PROMOTED_AT,
        "promotion_review": "TIBER-Data#192",
        "promotion_decision": PROMOTION_DECISIONS[0],
        "source_candidate": {
            "path": str(CANDIDATE_PATH),
            "sha256": candidate_sha256,
            "status_at_promotion": candidate["status"],
        },
        "approved_source_allowlist": list(validator_module.APPROVED_SOURCE_NAME_SUBSTRINGS),
        "seasons": candidate["seasons"],
        "season_type_scope": candidate["season_type_scope"],
        "included_positions": sorted(POSITION_SCOPE),
        "row_grain": candidate["row_grain"],
        "counts": {
            "records": len(records),
            "by_season": dict(sorted(Counter(r["season"] for r in records).items())),
            "by_position": dict(sorted(Counter(r["position"] for r in records).items())),
        },
        "no_fixture_or_scaffold_markers_confirmed": True,
        "validation": {
            "candidate_schema": "schemas/player_season_coverage_v0.schema.json",
            "candidate_validator": "scripts/validate_player_season_coverage_v0.py (incl. #192 all-source allow-list)",
            "promoted_schema": str(PROMOTED_SCHEMA_PATH),
            "status": "passed",
        },
        "consumer_safety": CONSUMER_SAFETY,
        "forecast_compatibility_note": FORECAST_COMPATIBILITY_NOTE,
        "reproducibility": {
            "promotion": "deterministic and network-free: this file is a pure transformation of the sha256-pinned candidate; re-running scripts/promote_player_season_coverage_v0.py yields byte-identical output",
            "candidate_rebuild": "python scripts/build_player_season_coverage_2022_2025.py (network: nflreadpy). Content-reproducible against unchanged upstream data, but NOT byte-identical across runs (embedded observed_at/generated_at timestamps) and upstream nflreadpy data is mutable; a rebuilt candidate gets a NEW sha and requires a NEW governance review before re-promotion",
        },
        "records": records,
    }


def main() -> int:
    raw = CANDIDATE_PATH.read_bytes()
    candidate_sha256 = hashlib.sha256(raw).hexdigest()
    candidate = json.loads(raw.decode("utf-8"))
    validator_module = _load_validator_module()

    promoted = build_promoted_payload(candidate, candidate_sha256, validator_module)

    promoted_schema = json.loads(PROMOTED_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_errors = [
        f"{'/'.join(str(p) for p in err.path)}: {err.message}"
        for err in jsonschema.Draft202012Validator(promoted_schema).iter_errors(promoted)
    ]
    if schema_errors:
        raise SystemExit(f"FAIL CLOSED: promoted payload fails its schema; first: {schema_errors[0]}")

    PROMOTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    promoted_bytes = (json.dumps(promoted, indent=1) + "\n").encode("utf-8")
    PROMOTED_PATH.write_bytes(promoted_bytes)

    manifest = {k: v for k, v in promoted.items() if k != "records"}
    manifest["promoted_artifact_path"] = str(PROMOTED_PATH)
    manifest["promoted_artifact_sha256"] = hashlib.sha256(promoted_bytes).hexdigest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"promoted {len(promoted['records'])} records -> {PROMOTED_PATH}")
    print(f"promoted artifact sha256: {manifest['promoted_artifact_sha256']}")
    print(f"manifest -> {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
