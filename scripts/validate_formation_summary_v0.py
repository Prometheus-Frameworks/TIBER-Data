"""Validator for a formation_summary_v0 candidate artifact (TIBER-Data #214).

Combines JSON Schema structural validation (schemas/formation_summary_v0.schema.json)
with the fail-closed business rules from docs/specs/formation-summary-v0-source-boundary.md
sections 3.1-3.3, 6.1, and 7:

- exact three-bucket reconciliation per row:
  shotgun + non_shotgun + unknown == offensive_plays,
- alignment vocabulary is exactly shotgun / non_shotgun /
  unknown_or_unclassified_alignment; the string "under_center" anywhere in the
  serialized artifact is a hard failure, not a style note,
- rates match their counts and stay inside [0, 1] or are null,
- the unknown bucket is explicit (count and rate present) even when zero,
- null-blocked pass/run split fields carry a machine-readable dropback note,
- efficiency fields below the declared bucket sample threshold are null with a
  typed sample note (never a manufactured zero),
- every emitted row satisfies the declared minimum offensive-play threshold,
- full-league coverage: all 32 canonical teams present, no unexpected teams, and
  metadata.coverage consistent with the actual row set (incomplete coverage is a
  hard failure, not a warning),
- the unknown-share high-uncertainty flag matches the declared threshold,
- retrieval metadata and sha256 checksums exist for every input source,
- governance/provenance markers are explicit and never governed/promoted.

Usage: python scripts/validate_formation_summary_v0.py <path-to-artifact.json>
Exits non-zero (fail closed) on any violation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_PATH = Path("schemas/formation_summary_v0.schema.json")

ALIGNMENT_VOCABULARY = ["shotgun", "non_shotgun", "unknown_or_unclassified_alignment"]
CANONICAL_TEAMS = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
        "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
        "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
        "TEN", "WAS",
    }
)
FORBIDDEN_ALIGNMENT_LABEL = "under_" + "center"  # never emitted; see spec section 3.3
SPLIT_RATE_FIELDS = (
    "shotgun_pass_rate", "shotgun_run_rate", "non_shotgun_pass_rate", "non_shotgun_run_rate",
)
RATE_FIELDS = (
    "shotgun_rate", "non_shotgun_rate", "unknown_alignment_rate",
    *SPLIT_RATE_FIELDS, "shotgun_success_rate", "non_shotgun_success_rate",
)
EFFICIENCY_FIELDS_BY_BUCKET = {
    "shotgun": ("shotgun_epa_per_play", "shotgun_success_rate"),
    "non_shotgun": ("non_shotgun_epa_per_play", "non_shotgun_success_rate"),
}
REQUIRED_RETRIEVAL_KEYS = (
    "sourceName", "sourceType", "retrievalMethod", "retrievalTimestamp",
    "packageVersion", "sourceUrlOrDatasetId", "transformCodePath", "sourceRefs",
)
RATE_TOLERANCE = 1e-6


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def validate_schema(artifact: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"schema: {'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(artifact)
    ]


def validate_business_rules(artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metadata = artifact.get("metadata", {})
    rows = artifact.get("rows", [])

    if FORBIDDEN_ALIGNMENT_LABEL in json.dumps(artifact):
        errors.append(
            f"forbidden alignment label '{FORBIDDEN_ALIGNMENT_LABEL}' appears in the "
            "artifact; spec section 3.3 hard-blocks it in any field name or prose"
        )

    if metadata.get("alignmentVocabulary") != ALIGNMENT_VOCABULARY:
        errors.append(
            "metadata.alignmentVocabulary must be exactly "
            f"{ALIGNMENT_VOCABULARY}, got {metadata.get('alignmentVocabulary')!r}"
        )

    thresholds = metadata.get("sampleThresholds", {})
    min_row_plays = thresholds.get("minOffensivePlaysPerRow")
    min_bucket_plays = thresholds.get("minBucketPlaysForEfficiency")
    unknown_threshold = thresholds.get("unknownShareUncertaintyThreshold")

    teams_seen: set[str] = set()
    for row in rows:
        team = row.get("team", "<missing>")
        prefix = f"row[{team}]"
        if team in teams_seen:
            errors.append(f"{prefix}: duplicate team row (grain is team_season)")
        teams_seen.add(team)

        offensive = row.get("offensive_plays", 0)
        bucket_sum = (
            row.get("shotgun_plays", 0)
            + row.get("non_shotgun_plays", 0)
            + row.get("unknown_or_unclassified_alignment_plays", 0)
        )
        if bucket_sum != offensive:
            errors.append(
                f"{prefix}: three-bucket reconciliation failed exactly "
                f"({bucket_sum} != {offensive})"
            )

        if isinstance(min_row_plays, int) and offensive < min_row_plays:
            errors.append(
                f"{prefix}: emitted with {offensive} offensive plays, below the "
                f"declared minimum of {min_row_plays} (must be suppressed instead)"
            )

        for field in RATE_FIELDS:
            value = row.get(field)
            if value is not None and not (0.0 <= value <= 1.0):
                errors.append(f"{prefix}: {field}={value} outside [0, 1]")

        for field, numerator in (
            ("shotgun_rate", row.get("shotgun_plays", 0)),
            ("non_shotgun_rate", row.get("non_shotgun_plays", 0)),
            ("unknown_alignment_rate", row.get("unknown_or_unclassified_alignment_plays", 0)),
        ):
            expected = _safe_ratio(numerator, offensive)
            actual = row.get(field)
            if expected is None or actual is None:
                if expected != actual:
                    errors.append(f"{prefix}: {field} null/denominator mismatch")
            elif abs(actual - expected) > RATE_TOLERANCE:
                errors.append(
                    f"{prefix}: {field}={actual} does not reconcile with counts "
                    f"(expected {expected:.6f})"
                )

        if row.get("unknown_or_unclassified_alignment_plays") is None or (
            offensive and row.get("unknown_alignment_rate") is None
        ):
            errors.append(
                f"{prefix}: unknown bucket must be explicit (count and rate) even when zero"
            )

        notes = row.get("sample_notes", [])
        note_codes = {note.get("code") for note in notes}
        split_nulls = [field for field in SPLIT_RATE_FIELDS if row.get(field) is None]
        if split_nulls and not (
            {"dropback_split_blocked", "empty_alignment_bucket"} & note_codes
        ):
            errors.append(
                f"{prefix}: null split field(s) {split_nulls} without a machine-readable "
                "dropback_split_blocked/empty_alignment_bucket note (fail-closed rule, "
                "spec section 3.1b)"
            )

        if isinstance(min_bucket_plays, int):
            for bucket, fields in EFFICIENCY_FIELDS_BY_BUCKET.items():
                bucket_plays = row.get(f"{bucket}_plays", 0)
                if bucket_plays >= min_bucket_plays:
                    continue
                emitted = [field for field in fields if row.get(field) is not None]
                if emitted:
                    errors.append(
                        f"{prefix}: efficiency field(s) {emitted} emitted with only "
                        f"{bucket_plays} {bucket} plays (threshold {min_bucket_plays})"
                    )
                if "sample_threshold_not_met" not in note_codes:
                    errors.append(
                        f"{prefix}: {bucket} bucket below efficiency threshold without a "
                        "sample_threshold_not_met note"
                    )

        if isinstance(unknown_threshold, (int, float)) and offensive:
            share = row.get("unknown_or_unclassified_alignment_plays", 0) / offensive
            should_flag = share > unknown_threshold
            if bool(row.get("unknown_alignment_uncertainty_flag")) != should_flag:
                errors.append(
                    f"{prefix}: unknown_alignment_uncertainty_flag="
                    f"{row.get('unknown_alignment_uncertainty_flag')} inconsistent with "
                    f"unknown share {share:.4f} vs threshold {unknown_threshold}"
                )

        if not row.get("sourceRefs"):
            errors.append(f"{prefix}: sourceRefs missing/empty")

    # Full-league coverage is a hard validation failure when incomplete (spec
    # section 7; #214 acceptance criteria), and the coverage metadata must
    # describe the actual row set, not a stale build state.
    missing_teams = sorted(CANONICAL_TEAMS - teams_seen)
    unexpected_teams = sorted(teams_seen - CANONICAL_TEAMS)
    if missing_teams:
        errors.append(f"coverage: missing canonical team row(s) {missing_teams}")
    if unexpected_teams:
        errors.append(f"coverage: unexpected non-canonical team row(s) {unexpected_teams}")
    coverage = metadata.get("coverage", {})
    if sorted(coverage.get("presentTeams", [])) != sorted(teams_seen):
        errors.append(
            "coverage: metadata.coverage.presentTeams does not match the actual row team set"
        )
    if coverage.get("missingTeams"):
        errors.append(
            f"coverage: metadata.coverage.missingTeams is non-empty "
            f"({coverage.get('missingTeams')})"
        )
    if coverage.get("unexpectedTeams"):
        errors.append(
            f"coverage: metadata.coverage.unexpectedTeams is non-empty "
            f"({coverage.get('unexpectedTeams')})"
        )
    if coverage.get("isFullLeague") is not True:
        errors.append(
            f"coverage: isFullLeague must be true, got {coverage.get('isFullLeague')!r}"
        )

    for source in metadata.get("inputSources", []):
        name = source.get("sourceName", "<unnamed>")
        missing = sorted(key for key in REQUIRED_RETRIEVAL_KEYS if not source.get(key))
        if missing:
            errors.append(f"inputSources[{name}]: missing retrieval keys {missing}")
        checksum = source.get("checksum")
        if not (
            isinstance(checksum, dict) and checksum.get("algorithm") and checksum.get("value")
        ):
            errors.append(f"inputSources[{name}]: checksum missing/incomplete")

    governance = metadata.get("governance", {})
    if governance.get("governanceStatus") != "ungoverned":
        errors.append(
            f"governanceStatus must be 'ungoverned', got {governance.get('governanceStatus')!r}"
        )
    if metadata.get("provenanceStatus") in ("governed_real_data", "promoted"):
        errors.append(
            f"provenanceStatus {metadata.get('provenanceStatus')!r} claims governed/promoted "
            "status; this schema only covers candidates"
        )

    return errors


def validate_artifact(artifact: dict[str, Any]) -> list[str]:
    errors = validate_schema(artifact)
    errors.extend(validate_business_rules(artifact))
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: python scripts/validate_formation_summary_v0.py <artifact.json>",
            file=sys.stderr,
        )
        return 2
    artifact = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    errors = validate_artifact(artifact)
    if errors:
        print(f"FAIL: {len(errors)} violation(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    rows = artifact.get("rows", [])
    print(f"PASS: {len(rows)} row(s) validated against schema and business rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
