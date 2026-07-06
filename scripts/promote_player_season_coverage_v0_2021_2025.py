"""Promote the merged 2021-2025 candidate to extend the governed player_season_coverage_v0
artifact (TIBER-Data #202, promotion review for #200/#201's 2021 candidate extension).

Deterministic, network-free promotion, mirroring scripts/promote_player_season_coverage_v0.py's
gates exactly (that script is NOT modified -- it remains the reproducible record of the original
#192 promotion event; this is a new, separate promotion event that supersedes its OUTPUT, not its
history):

  1. the merged candidate's sha256 must equal the pin recorded here (protects against silent
     drift of the merge input),
  2. the full candidate validator (schema + business rules) must pass with zero errors,
  3. every record must sit inside the declared envelope scope (REG only, QB/RB/WR/TE only),
  4. the promoted payload must validate against schemas/player_season_coverage_v0_promoted.schema.json
     (unchanged schema -- promotion changes only the envelope, never the per-record contract).

This also records full lineage back to the original #192 promotion (prior_promoted_artifact) and
to both upstream candidates that were merged (source_candidate_lineage), so the promotion history
remains fully reconstructible from committed bytes alone.

Promotion does NOT authorize Forecast production binding, mirror refresh, additional validation,
or threshold acceptance: see consumer_safety / forecast_compatibility_note below.

Usage: python scripts/promote_player_season_coverage_v0_2021_2025.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2021_2025.source_backed.json"
PINNED_CANDIDATE_SHA256 = "c92404a1b519a62ee9f4b75f74662157fc8dd02b883648d4cdae694d0e021424"

PROMOTED_SCHEMA_PATH = REPO_ROOT / "schemas/player_season_coverage_v0_promoted.schema.json"
PROMOTED_PATH = REPO_ROOT / "exports/promoted/nfl/player_season_coverage_v0.json"
MANIFEST_PATH = REPO_ROOT / "exports/promoted/nfl/PLAYER_SEASON_COVERAGE_V0_PROMOTION_MANIFEST.json"

PRIOR_PROMOTED_PATH = PROMOTED_PATH  # same path; read BEFORE overwrite to record lineage
PRIOR_PROMOTION_REVIEW = "TIBER-Data#192"
PRIOR_PROMOTED_SHA256 = "29f8e378127fa5426e5897ac4522b6187941312edabab357d8a427fb20511035"

PROMOTED_STATUS = "promoted_governed_artifact"
PROMOTED_AT = "2026-07-06T00:00:00Z"  # fixed review date: keeps promotion output deterministic
SEASON_TYPE_SCOPE = {"REG"}
POSITION_SCOPE = {"QB", "RB", "WR", "TE"}

PROMOTION_REVIEW = "TIBER-Data#202"
PROMOTION_DECISION = "promote_player_season_coverage_v0_2021_2025"

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
    "until a Forecast production-binding review passes. This promotion changes nothing in Forecast. "
    "TIBER-Data#202 authorizes TIBER-Data promotion review ONLY: it does not authorize a Forecast "
    "mirror refresh, additional validation, or threshold acceptance. The only next authorized step "
    "is a separate TIBER-Forecast issue considering whether to refresh non-production mirrors."
)


class PromotionGateError(SystemExit):
    pass


def _load_validator_module():
    module_path = REPO_ROOT / "scripts/validate_player_season_coverage_v0.py"
    spec = spec_from_file_location("validate_player_season_coverage_v0", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_envelope_scope(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(records):
        if row.get("season_type") not in SEASON_TYPE_SCOPE:
            errors.append(f"record[{idx}]: season_type {row.get('season_type')!r} outside promoted scope {sorted(SEASON_TYPE_SCOPE)}")
        if row.get("position") not in POSITION_SCOPE:
            errors.append(f"record[{idx}]: position {row.get('position')!r} outside promoted scope {sorted(POSITION_SCOPE)}")
    return errors


def build_promoted_payload(
    candidate: dict,
    candidate_sha256: str,
    pinned_candidate_sha256: str,
    validator_module,
    prior_promoted_sha256: str | None,
) -> dict:
    """Pure transformation candidate -> promoted payload. Fails closed on any gate violation."""
    if candidate_sha256 != pinned_candidate_sha256:
        raise PromotionGateError(
            f"FAIL CLOSED: merged candidate sha256 {candidate_sha256} does not match the pin "
            f"{pinned_candidate_sha256}. If the merge was intentionally regenerated, re-run the "
            "full governance review and update the pin first."
        )
    errors = validator_module.validate_payload(candidate)
    if errors:
        raise PromotionGateError(f"FAIL CLOSED: candidate validator reported {len(errors)} error(s); first: {errors[0]}")
    records = candidate["records"]
    scope_errors = check_envelope_scope(records)
    if scope_errors:
        raise PromotionGateError(f"FAIL CLOSED: {len(scope_errors)} record(s) outside promoted scope; first: {scope_errors[0]}")

    if prior_promoted_sha256 is not None and prior_promoted_sha256 != PRIOR_PROMOTED_SHA256:
        raise PromotionGateError(
            f"FAIL CLOSED: the currently-committed promoted artifact's sha256 ({prior_promoted_sha256}) "
            f"does not match the expected prior sha256 ({PRIOR_PROMOTED_SHA256}) recorded for lineage. "
            "The promoted artifact changed out from under this script since it was written; re-verify "
            "lineage before re-running."
        )

    return {
        "artifact_id": "player_season_coverage_v0",
        "spec_version": "player_season_coverage_v0_promoted_v1",
        "status": PROMOTED_STATUS,
        "generated_at": candidate["generated_at"],
        "promoted_at": PROMOTED_AT,
        "promotion_review": PROMOTION_REVIEW,
        "promotion_decision": PROMOTION_DECISION,
        "source_candidate": {
            "path": CANDIDATE_PATH.relative_to(REPO_ROOT).as_posix(),
            "sha256": candidate_sha256,
            "status_at_promotion": candidate["status"],
        },
        "source_candidate_lineage": candidate.get("merged_from", []),
        "prior_promoted_artifact": {
            "path": PROMOTED_PATH.relative_to(REPO_ROOT).as_posix(),
            "sha256": prior_promoted_sha256,
            "promotion_review": PRIOR_PROMOTION_REVIEW,
            "seasons": [2022, 2023, 2024, 2025],
            "note": (
                "This promotion event supersedes the OUTPUT of TIBER-Data#192 (same artifact_id/path), "
                "extending season coverage from 2022-2025 to 2021-2025. It does not retroactively "
                "invalidate #192's review. WARNING: do NOT run scripts/promote_player_season_coverage_v0.py "
                "against this live checkout to reconstruct the prior bytes -- it writes to this same "
                "exports/promoted/nfl/player_season_coverage_v0.json path and would silently overwrite the "
                "current 2021-2025 governed artifact with the stale 2022-2025-only content. The prior bytes "
                "are safely reconstructible either via this repo's git history (the commit immediately before "
                "TIBER-Data#206 landed), or by running scripts/promote_player_season_coverage_v0.py with its "
                "PROMOTED_PATH/MANIFEST_PATH constants redirected to a scratch output location."
            ),
        },
        "approved_source_allowlist": list(validator_module.APPROVED_SOURCE_NAME_PREFIXES),
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
            "promoted_schema": PROMOTED_SCHEMA_PATH.relative_to(REPO_ROOT).as_posix(),
            "status": "passed",
        },
        "consumer_safety": CONSUMER_SAFETY,
        "forecast_compatibility_note": FORECAST_COMPATIBILITY_NOTE,
        "reproducibility": {
            "promotion": (
                "deterministic and network-free: this file is a pure transformation of the "
                "sha256-pinned merged candidate; re-running scripts/promote_player_season_coverage_v0_2021_2025.py "
                "yields byte-identical output"
            ),
            "merged_candidate_rebuild": (
                "python scripts/build_player_season_coverage_2021_2025_merged_candidate.py "
                "(network-free: reads the two already-committed, sha256-pinned upstream candidates). "
                "Content-reproducible against unchanged upstream candidate files."
            ),
            "original_2022_2025_candidate_rebuild": (
                "python scripts/build_player_season_coverage_2022_2025.py (network: nflreadpy). "
                "NOT byte-identical across runs (embedded observed_at/generated_at timestamps); a "
                "rebuilt candidate gets a NEW sha and requires a NEW governance review before re-promotion."
            ),
            "2021_candidate_rebuild": (
                "python scripts/build_player_season_coverage_2021_candidate.py (network: nflreadpy). "
                "Same non-determinism caveat as above."
            ),
        },
        "records": records,
    }


def main() -> int:
    candidate_raw = CANDIDATE_PATH.read_bytes()
    candidate_sha256 = hashlib.sha256(candidate_raw).hexdigest()
    candidate = json.loads(candidate_raw.decode("utf-8"))
    validator_module = _load_validator_module()

    prior_promoted_sha256 = None
    if PRIOR_PROMOTED_PATH.exists():
        prior_promoted_sha256 = hashlib.sha256(PRIOR_PROMOTED_PATH.read_bytes()).hexdigest()

    promoted = build_promoted_payload(
        candidate, candidate_sha256, PINNED_CANDIDATE_SHA256, validator_module, prior_promoted_sha256
    )

    promoted_schema = json.loads(PROMOTED_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_errors = [
        f"{'/'.join(str(p) for p in err.path)}: {err.message}"
        for err in jsonschema.Draft202012Validator(promoted_schema).iter_errors(promoted)
    ]
    if schema_errors:
        raise PromotionGateError(f"FAIL CLOSED: promoted payload fails its schema; first: {schema_errors[0]}")

    PROMOTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    promoted_bytes = (json.dumps(promoted, indent=1) + "\n").encode("utf-8")
    PROMOTED_PATH.write_bytes(promoted_bytes)

    manifest = {k: v for k, v in promoted.items() if k != "records"}
    manifest["promoted_artifact_path"] = PROMOTED_PATH.relative_to(REPO_ROOT).as_posix()
    manifest["promoted_artifact_sha256"] = hashlib.sha256(promoted_bytes).hexdigest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"promoted {len(promoted['records'])} records -> {PROMOTED_PATH}")
    print(f"promoted artifact sha256: {manifest['promoted_artifact_sha256']}")
    print(f"manifest -> {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PromotionGateError:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
