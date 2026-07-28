"""Validate the bounded 2026 population census v0 candidate.

Validation is fail-closed and includes:

* JSON Schema validation;
* exact source-pin and source-governance hash checks;
* deterministic reconstruction from the two immutable git blobs;
* population-row uniqueness and status-count invariants;
* reconciliation-ledger consistency; and
* a recursive ban on forecast, ranking, advice, and activity assertion fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema

try:
    from scripts.build_bounded_2026_population_census_v0 import (
        ARTIFACT_ID,
        DATA_SOURCE_PIN,
        ROOKIE_SOURCE_PIN,
        SCHEMA_VERSION,
        SCOPE_ID,
        STATUS,
        build_from_git,
        serialize_artifact,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_....py
    from build_bounded_2026_population_census_v0 import (  # type: ignore[no-redef]
        ARTIFACT_ID,
        DATA_SOURCE_PIN,
        ROOKIE_SOURCE_PIN,
        SCHEMA_VERSION,
        SCOPE_ID,
        STATUS,
        build_from_git,
        serialize_artifact,
    )

SCHEMA_PATH = Path("schemas/bounded_2026_population_census_v0.schema.json")
DEFAULT_ARTIFACT_PATH = Path(
    "exports/candidates/population_census/bounded_2026_population_census_v0.json"
)

FORBIDDEN_ROW_KEYS = {
    "active",
    "active_status",
    "advice",
    "fantasy_points",
    "forecast",
    "forecast_value",
    "is_active",
    "model_score",
    "ownership_status",
    "projected_points",
    "projection",
    "rank",
    "ranking",
    "recommendation",
    "roster_status",
}


def _schema_errors(payload: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    return [
        f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    ]


def _walk_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_ROW_KEYS:
                errors.append(f"{child_path}: forbidden output field")
            errors.extend(_walk_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return errors


def _expected_count_map(rows: list[dict[str, Any]], getter) -> dict[str, int]:
    return dict(sorted(Counter(str(getter(row)) for row in rows).items()))


def _check_count_maps(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = payload.get("population_rows")
    if not isinstance(rows, list):
        return ["population_rows: must be an array before count checks can run"]
    coverage = payload.get("coverage_summary")
    if not isinstance(coverage, dict):
        return ["coverage_summary: must be an object before count checks can run"]
    expected_maps = {
        "by_source": _expected_count_map(
            rows, lambda row: row["source_identity_ref"]["source_artifact_key"]
        ),
        "by_population_kind": _expected_count_map(rows, lambda row: row["population_kind"]),
        "by_identity_status": _expected_count_map(rows, lambda row: row["identity_status"]),
        "by_position_status": _expected_count_map(rows, lambda row: row["position_status"]),
        "by_team_status": _expected_count_map(
            rows, lambda row: row["team_assignment"]["team_status"]
        ),
        "by_history_status": _expected_count_map(rows, lambda row: row["history_status"]),
    }
    for name, expected in expected_maps.items():
        actual = coverage.get(name)
        if actual != expected:
            errors.append(f"coverage_summary.{name}: expected {expected}, got {actual}")
        if isinstance(actual, dict) and sum(actual.values()) != len(rows):
            errors.append(
                f"coverage_summary.{name}: counts sum to {sum(actual.values())}, "
                f"expected {len(rows)}"
            )
    return errors


def _check_source_descriptors(payload: dict[str, Any]) -> list[str]:
    expected = {
        DATA_SOURCE_PIN.source_artifact_key: DATA_SOURCE_PIN,
        ROOKIE_SOURCE_PIN.source_artifact_key: ROOKIE_SOURCE_PIN,
    }
    errors: list[str] = []
    sources = payload.get("source_artifacts")
    if not isinstance(sources, list):
        return ["source_artifacts: must be an array"]
    if len(sources) != len(expected):
        errors.append(f"source_artifacts: expected exactly 2 entries, got {len(sources)}")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"source_artifacts[{index}]: must be an object")
            continue
        key = source.get("source_artifact_key")
        if key not in expected:
            errors.append(f"source_artifacts[{index}]: unapproved source_artifact_key {key!r}")
            continue
        if key in seen:
            errors.append(f"source_artifacts[{index}]: duplicate source_artifact_key {key!r}")
        seen.add(key)
        pin = expected[key]
        checks = {
            "repository": pin.repository,
            "commit": pin.commit,
            "path": pin.path,
            "sha256": pin.sha256,
            "included_row_count": pin.expected_included_rows,
        }
        for field, expected_value in checks.items():
            if source.get(field) != expected_value:
                errors.append(
                    f"source_artifacts[{index}].{field}: expected "
                    f"{expected_value!r}, got {source.get(field)!r}"
                )
        governance = source.get("governance_evidence")
        if not isinstance(governance, dict):
            errors.append(f"source_artifacts[{index}].governance_evidence: missing")
        else:
            if governance.get("path") != pin.governance_path:
                errors.append(f"source_artifacts[{index}].governance_evidence.path: pin mismatch")
            if governance.get("sha256") != pin.governance_sha256:
                errors.append(f"source_artifacts[{index}].governance_evidence.sha256: pin mismatch")
    if seen != set(expected):
        errors.append(
            f"source_artifacts: expected source keys {sorted(expected)}, got {sorted(seen)}"
        )
    return errors


def _check_row_invariants(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = payload.get("population_rows")
    if not isinstance(rows, list):
        return ["population_rows: must be an array"]
    if payload.get("population_row_count") != len(rows):
        errors.append(
            f"population_row_count: declared {payload.get('population_row_count')}, "
            f"found {len(rows)} rows"
        )
    expected_total = (
        DATA_SOURCE_PIN.expected_included_rows + ROOKIE_SOURCE_PIN.expected_included_rows
    )
    if len(rows) != expected_total:
        errors.append(f"population_rows: expected {expected_total} rows, found {len(rows)}")

    row_ids = [row.get("population_row_id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != len(set(row_ids)):
        errors.append("population_rows: duplicate population_row_id")
    if row_ids != sorted(row_ids):
        errors.append(
            "population_rows: rows are not deterministically ordered by population_row_id"
        )

    source_descriptors = {
        source.get("source_artifact_key"): source
        for source in payload.get("source_artifacts", [])
        if isinstance(source, dict)
    }
    source_pairs: list[tuple[str, int]] = []
    source_index_counts: Counter[str] = Counter()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        ref = row.get("source_identity_ref")
        if not isinstance(ref, dict):
            continue
        source_key = ref.get("source_artifact_key")
        source_index = ref.get("source_row_index")
        if isinstance(source_key, str) and isinstance(source_index, int):
            source_pairs.append((source_key, source_index))
            source_index_counts[source_key] += 1
            descriptor = source_descriptors.get(source_key)
            source_row_count = (
                descriptor.get("source_row_count") if isinstance(descriptor, dict) else None
            )
            if (
                not isinstance(source_row_count, int)
                or source_index < 0
                or source_index >= source_row_count
            ):
                errors.append(
                    f"population_rows[{index}].source_identity_ref.source_row_index: "
                    f"{source_index} is outside source artifact row range "
                    f"0..{source_row_count - 1 if isinstance(source_row_count, int) else 'unknown'}"
                )
        if (
            row.get("canonical_player_id") is not None
            and ref.get("source_identity_confidence") != "source_verified"
        ):
            errors.append(
                f"population_rows[{index}]: canonical_player_id requires "
                "source_identity_confidence == 'source_verified'"
            )
        if row.get("population_kind") == "rookie_transition_2026":
            if row.get("canonical_player_id") is not None:
                errors.append(
                    f"population_rows[{index}]: rookie canonical_player_id must remain null "
                    "without an exact governed cross-namespace contract"
                )
            if row.get("history_status") != "history_unresolved_no_exact_crosswalk":
                errors.append(
                    f"population_rows[{index}]: rookie history status overclaims identity history"
                )
        availability = row.get("availability_evidence")
        records = availability.get("provenance_records") if isinstance(availability, dict) else None
        if not isinstance(records, list):
            errors.append(
                f"population_rows[{index}].availability_evidence.provenance_records: "
                "must be an array"
            )
            continue
        evidence_fields = [
            record.get("evidence_field") for record in records if isinstance(record, dict)
        ]
        if len(evidence_fields) != len(set(evidence_fields)):
            errors.append(
                f"population_rows[{index}].availability_evidence: duplicate evidence_field"
            )
        if row.get("population_kind") == "rookie_transition_2026":
            expected_fields = {
                "draft_capital",
                "age_at_entry",
                "athletic_testing",
                "college_production",
                "official_postdraft_outcome",
            }
            if set(evidence_fields) != expected_fields:
                errors.append(
                    f"population_rows[{index}].availability_evidence: expected rookie "
                    f"provenance fields {sorted(expected_fields)}, got "
                    f"{sorted(str(field) for field in evidence_fields)}"
                )
        elif "record_envelope" not in evidence_fields:
            errors.append(
                f"population_rows[{index}].availability_evidence: "
                "historical record_envelope evidence missing"
            )
    if len(source_pairs) != len(set(source_pairs)):
        errors.append("population_rows: one or more source rows appear more than once")
    for source_key, descriptor in source_descriptors.items():
        included_row_count = descriptor.get("included_row_count")
        if source_index_counts[source_key] != included_row_count:
            errors.append(
                f"source_artifacts[{source_key!r}].included_row_count: declared "
                f"{included_row_count}, found {source_index_counts[source_key]} row indices"
            )
    return errors


def _expected_reconciliation(rows: list[dict[str, Any]]) -> dict[str, int]:
    unresolved = [row for row in rows if "unresolved" in row["identity_status"]]
    missing = [row for row in unresolved if row["source_identity_ref"]["source_player_id"] is None]
    return {
        "unresolved_identity_rows": len(unresolved),
        "missing_identity_rows": len(missing),
    }


def _check_reconciliation(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = payload.get("population_rows")
    reconciliation = payload.get("reconciliation")
    if not isinstance(rows, list) or not isinstance(reconciliation, dict):
        return ["reconciliation: cannot check without population_rows and reconciliation object"]
    expected_counts = _expected_reconciliation(rows)
    counts = reconciliation.get("counts")
    if not isinstance(counts, dict):
        return ["reconciliation.counts: must be an object"]
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(
                f"reconciliation.counts.{key}: expected {expected}, got {counts.get(key)}"
            )
        ledger = reconciliation.get(key)
        if not isinstance(ledger, list) or len(ledger) != expected:
            errors.append(
                f"reconciliation.{key}: expected {expected} itemized rows, "
                f"got {len(ledger) if isinstance(ledger, list) else 'non-array'}"
            )
    canonical = reconciliation.get("cross_source_canonical_identity_reconciliation")
    if not isinstance(canonical, dict):
        errors.append(
            "reconciliation.cross_source_canonical_identity_reconciliation: must be an object"
        )
    else:
        if canonical.get("status") != "unevaluable_no_exact_cross_namespace_contract":
            errors.append(
                "reconciliation.cross_source_canonical_identity_reconciliation.status: "
                "must remain unevaluable without an exact cross-namespace contract"
            )
        if canonical.get("collision_groups") is not None:
            errors.append(
                "reconciliation.cross_source_canonical_identity_reconciliation."
                "collision_groups: must be null, not a numeric zero"
            )
    if counts.get("cross_source_canonical_identity_collision_groups") is not None:
        errors.append(
            "reconciliation.counts.cross_source_canonical_identity_collision_groups: "
            "must be null while canonical identity is unevaluable"
        )
    reuse = reconciliation.get("cross_source_source_id_reuse")
    if not isinstance(reuse, list):
        errors.append("reconciliation.cross_source_source_id_reuse: must be an array")
    elif counts.get("cross_source_source_id_reuse_groups") != len(reuse):
        errors.append(
            "reconciliation.counts.cross_source_source_id_reuse_groups: "
            f"expected {len(reuse)}, got "
            f"{counts.get('cross_source_source_id_reuse_groups')}"
        )
    return errors


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = _schema_errors(payload)
    if payload.get("artifact_id") != ARTIFACT_ID:
        errors.append(f"artifact_id must equal {ARTIFACT_ID}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    if payload.get("status") != STATUS:
        errors.append(f"status must equal {STATUS}")
    if payload.get("scope_id") != SCOPE_ID:
        errors.append(f"scope_id must equal {SCOPE_ID}")
    scope = payload.get("scope_definition")
    if isinstance(scope, dict):
        if scope.get("full_universe_claim") is not False:
            errors.append("scope_definition.full_universe_claim must be false")
        if scope.get("idp_full_universe_available") is not False:
            errors.append("scope_definition.idp_full_universe_available must be false")
        if scope.get("activity_inference_performed") is not False:
            errors.append("scope_definition.activity_inference_performed must be false")
        if (
            scope.get("identity_join_policy")
            != "exact_source_identity_only_no_cross_namespace_join"
        ):
            errors.append("scope_definition.identity_join_policy drifted")
    errors.extend(_check_source_descriptors(payload))
    errors.extend(_check_row_invariants(payload))
    errors.extend(_check_count_maps(payload))
    errors.extend(_check_reconciliation(payload))
    errors.extend(_walk_forbidden_keys(payload.get("population_rows", []), "$.population_rows"))
    return errors


def validate_against_sources(
    payload: dict[str, Any],
    *,
    data_repo_root: Path,
    rookie_repo_root: Path,
) -> list[str]:
    expected = build_from_git(
        data_repo_root=data_repo_root,
        rookie_repo_root=rookie_repo_root,
        generated_at=str(payload.get("generated_at")),
    )
    if payload != expected:
        return [
            "artifact differs from deterministic reconstruction of the exact pinned source blobs"
        ]
    return []


def _report_payload(
    artifact_path: Path,
    raw: bytes,
    payload: dict[str, Any],
) -> dict[str, Any]:
    source_indices: dict[str, list[int]] = {}
    for row in payload["population_rows"]:
        ref = row["source_identity_ref"]
        source_indices.setdefault(ref["source_artifact_key"], []).append(ref["source_row_index"])
    return {
        "artifact_id": ARTIFACT_ID,
        "schema_version": SCHEMA_VERSION,
        "validation_status": "passed",
        "artifact_path": artifact_path.as_posix(),
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "population_row_count": payload["population_row_count"],
        "source_row_counts": payload["coverage_summary"]["by_source"],
        "source_row_index_ranges": {
            source_key: {
                "count": len(indices),
                "minimum": min(indices),
                "maximum": max(indices),
            }
            for source_key, indices in sorted(source_indices.items())
        },
        "identity_status_counts": payload["coverage_summary"]["by_identity_status"],
        "team_status_counts": payload["coverage_summary"]["by_team_status"],
        "reconciliation_counts": payload["reconciliation"]["counts"],
        "source_pins_verified": True,
        "deterministic_source_rebuild_equal": True,
        "forecast_run_authorized": False,
        "promotion_authorized": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact",
        nargs="?",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
    )
    parser.add_argument("--data-repo-root", type=Path, default=Path("."))
    parser.add_argument("--rookie-repo-root", type=Path, required=True)
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional deterministic JSON validation report output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = args.artifact.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"FAILED: {args.artifact} is not valid JSON: {exc}")
        return 1
    if not isinstance(payload, dict):
        print(f"FAILED: {args.artifact} must contain a JSON object")
        return 1

    errors = validate_payload(payload)
    try:
        errors.extend(
            validate_against_sources(
                payload,
                data_repo_root=args.data_repo_root.resolve(),
                rookie_repo_root=args.rookie_repo_root.resolve(),
            )
        )
    except Exception as exc:  # Convert source access/build failures into validator failures.
        errors.append(f"source verification failed: {exc}")
    if raw != serialize_artifact(payload):
        errors.append("artifact bytes do not match canonical deterministic serialization")

    if errors:
        print(f"FAILED: {len(errors)} validation error(s) in {args.artifact}")
        for error in errors[:200]:
            print(f"  - {error}")
        return 1

    if args.report:
        report = _report_payload(args.artifact, raw, payload)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        f"OK: {args.artifact} passed schema, source-pin, row-preservation, "
        f"and deterministic rebuild checks ({payload['population_row_count']} rows, "
        f"sha256={hashlib.sha256(raw).hexdigest()})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
