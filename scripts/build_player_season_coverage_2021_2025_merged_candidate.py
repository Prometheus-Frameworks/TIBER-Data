"""Merge the 2021 candidate extension with the promoted 2022-2025 candidate into one
combined candidate, as the required input to a 2021-2025 promotion review (TIBER-Data #202).

This is a deterministic, network-free structural transformation: it reads the two
ALREADY committed, already-validated, sha256-pinned candidate files below, fails closed
unless each still matches its known-good pin (protects against silent drift of either
upstream file), concatenates their records, and re-sorts by (season, player_id) --
exactly the ordering convention both source builders already use. It does not call
nflreadpy, does not fabricate any row, and does not touch exports/promoted/**.

Inputs (both already candidate_evidence_artifact_not_promoted, already validator-clean):
  - data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json
    (TIBER-Data #200 / PR #201)
  - data/processed/evidence/player_season_coverage_2022_2025.source_backed.json
    (TIBER-Data #190-#192; this is the exact file pinned by the CURRENT promoted
    artifact's manifest -- if its sha has drifted since promotion, that is a governance
    problem this script must refuse to paper over.)

Output: data/processed/evidence/player_season_coverage_2021_2025.source_backed.json --
still a candidate/evidence artifact, NOT promoted. Promotion is a separate, explicit step
(scripts/promote_player_season_coverage_v0_2021_2025.py).

Usage: python scripts/build_player_season_coverage_2021_2025_merged_candidate.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_2021_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json"
PINNED_CANDIDATE_2021_SHA256 = "55618590d4a1f6affa8228d32d61b9baa0d66552448811c06136ca6139a7eef4"

CANDIDATE_2022_2025_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2022_2025.source_backed.json"
PINNED_CANDIDATE_2022_2025_SHA256 = "39b6e71e36d667509221137f2b712143fe5fdccf5423f50e81b5c7a138c0072b"

OUTPUT_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2021_2025.source_backed.json"
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_player_season_coverage_v0.py"
PROMOTED_DIR = REPO_ROOT / "exports/promoted"

# Fixed, deterministic merge timestamp (this is a structural transformation of already
# source-backed data, not a new source pull, so a wall-clock "now" would make the output
# non-reproducible for no reason -- see scripts/promote_player_season_coverage_v0.py's
# PROMOTED_AT for the same convention).
MERGE_GENERATED_AT = "2026-07-06T00:00:00Z"


class MergeFeasibilityError(ValueError):
    pass


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_player_season_coverage_v0", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_pinned(path: Path, pinned_sha256: str, label: str) -> tuple[dict, str]:
    if not path.exists():
        raise MergeFeasibilityError(f"{label}: source candidate not found at {path}")
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    if sha256 != pinned_sha256:
        raise MergeFeasibilityError(
            f"{label}: sha256 {sha256} does not match the pinned value {pinned_sha256}. "
            f"{path.name} has drifted since it was last validated/promoted; refusing to merge "
            "an unverified input. Re-validate and re-pin before merging."
        )
    return json.loads(raw.decode("utf-8")), sha256


def build_merged_candidate(candidate_2021: dict, candidate_2022_2025: dict, validator_module) -> dict:
    """Pure assembly: merges two already-validated candidate payloads.

    Fails closed if either input isn't itself validator-clean, if the merge produces a
    duplicate (player_id, season, season_type) grain, or if the row_grain/season_type
    conventions of the two inputs disagree.
    """
    for label, candidate in (("2021", candidate_2021), ("2022-2025", candidate_2022_2025)):
        errors = validator_module.validate_payload(candidate)
        if errors:
            raise MergeFeasibilityError(
                f"{label} candidate is not validator-clean ({len(errors)} error(s)); "
                f"first: {errors[0]}. Refusing to merge an invalid input."
            )

    if candidate_2021["row_grain"] != candidate_2022_2025["row_grain"]:
        raise MergeFeasibilityError(
            "row_grain mismatch between inputs: "
            f"{candidate_2021['row_grain']!r} vs {candidate_2022_2025['row_grain']!r}"
        )
    if set(candidate_2021["season_type_scope"]) != set(candidate_2022_2025["season_type_scope"]):
        raise MergeFeasibilityError(
            "season_type_scope mismatch between inputs: "
            f"{candidate_2021['season_type_scope']!r} vs {candidate_2022_2025['season_type_scope']!r}"
        )

    overlapping_seasons = set(candidate_2021["seasons"]) & set(candidate_2022_2025["seasons"])
    if overlapping_seasons:
        raise MergeFeasibilityError(
            f"Inputs claim overlapping season(s) {sorted(overlapping_seasons)}; a merge must be "
            "over disjoint season windows, not a season-level overwrite."
        )

    records = list(candidate_2021["records"]) + list(candidate_2022_2025["records"])

    seen_grain: set[tuple] = set()
    for r in records:
        key = (r["player_id"], r["season"], r["season_type"])
        if key in seen_grain:
            raise MergeFeasibilityError(f"Duplicate grain {key} produced by merge. Fails closed.")
        seen_grain.add(key)

    records.sort(key=lambda r: (r["season"], r["player_id"]))

    seasons = sorted({r["season"] for r in records})
    included_positions = sorted({r["position"] for r in records})

    return {
        "artifact_id": "player_season_coverage_2021_2025.source_backed",
        "spec_version": "player_season_coverage_v0_candidate",
        "status": "candidate_evidence_artifact_not_promoted",
        "generated_at": MERGE_GENERATED_AT,
        "seasons": seasons,
        "season_type_scope": candidate_2022_2025["season_type_scope"],
        "included_positions": included_positions,
        "row_grain": candidate_2022_2025["row_grain"],
        "provenance": "nflreadpy.load_player_stats + nflreadpy.load_players",
        "tracking_issue": "TIBER-Data#202 (promotion review; merges #200/#201's 2021 candidate with the #190-#192 2022-2025 candidate)",
        "merged_from": [
            {
                "path": CANDIDATE_2021_PATH.relative_to(REPO_ROOT).as_posix(),
                "sha256": None,  # filled in by main() from the actual read bytes
                "seasons_contributed": candidate_2021["seasons"],
                "record_count": len(candidate_2021["records"]),
            },
            {
                "path": CANDIDATE_2022_2025_PATH.relative_to(REPO_ROOT).as_posix(),
                "sha256": None,  # filled in by main() from the actual read bytes
                "seasons_contributed": candidate_2022_2025["seasons"],
                "record_count": len(candidate_2022_2025["records"]),
            },
        ],
        "non_goals": [
            "not promoted/governed Forecast-ready data",
            "not a Forecast input today",
            "no active/inactive/IR/practice-squad availability status is asserted",
            "POST season_type out of scope",
            "this file is a pure structural merge; no row was recomputed, filtered, or fabricated",
        ],
        "records": records,
    }


def main() -> int:
    resolved_output = OUTPUT_PATH.resolve()
    resolved_promoted_dir = PROMOTED_DIR.resolve()
    if resolved_output == resolved_promoted_dir or resolved_promoted_dir in resolved_output.parents:
        raise MergeFeasibilityError(f"Refusing to write merged candidate under a promoted path: {resolved_output}")

    candidate_2021, sha_2021 = _load_pinned(CANDIDATE_2021_PATH, PINNED_CANDIDATE_2021_SHA256, "2021 candidate")
    candidate_2022_2025, sha_2022_2025 = _load_pinned(
        CANDIDATE_2022_2025_PATH, PINNED_CANDIDATE_2022_2025_SHA256, "2022-2025 candidate"
    )

    validator_module = _load_validator_module()
    merged = build_merged_candidate(candidate_2021, candidate_2022_2025, validator_module)
    merged["merged_from"][0]["sha256"] = sha_2021
    merged["merged_from"][1]["sha256"] = sha_2022_2025

    errors = validator_module.validate_payload(merged)
    if errors:
        raise MergeFeasibilityError(f"Merged candidate failed validation ({len(errors)} error(s)); first: {errors[0]}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(f"{json.dumps(merged, indent=2, allow_nan=False)}\n", encoding="utf-8")
    print(f"Wrote merged 2021-2025 candidate: {OUTPUT_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Record count: {len(merged['records'])}")
    print(f"Seasons: {merged['seasons']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
