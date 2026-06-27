"""PR D promotion: stamp the explicit governance marker on the 2024 candidate.

This is the deterministic, fail-closed promotion step for TIBER-Data #179. It
does NOT re-run source retrieval, does NOT change any row value, and does NOT
source/estimate/zero-fill pressure. It only re-verifies the data gate and then
stamps the explicit human-review governance marker decided in the #179 PR D
review.

Governance is carried by the explicit marker in artifact/manifest metadata, not
by the file path (the chain's no-path-inference rule), so the artifact is
promoted in place at its existing path.

Re-running is idempotent: an already-promoted, gate-consistent artifact is
re-verified and rewritten identically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CANDIDATE_ARTIFACT_PATH = Path(
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.json"
)
CANDIDATE_VALIDATION_REPORT_PATH = Path(
    "exports/candidates/team_week_raw/team_week_raw_v0_2024_real_source_candidate.validation.json"
)
LINEAGE_MANIFEST_PATH = Path(
    "data/manifests/team_week_raw_v0_2024_real_source_candidate.manifest.json"
)
PROMOTION_REVIEW_DOC_PATH = "docs/reviews/team-week-raw-v0-2024-promotion-review-pr-d.md"

# Fixed so re-running the promotion is byte-deterministic.
REVIEW_DATE = "2026-06-27"
REVIEW_REFS = [PROMOTION_REVIEW_DOC_PATH, "TIBER-Data#179"]
PROMOTION_AUTHORIZED_BY = (
    "explicit operator authorization (Path A) via the TIBER-Data #179 PR D promotion review"
)
GOVERNANCE_MARKER_NOTE = (
    "Promoted to governed_real_data by explicit human promotion review (PR D, "
    "TIBER-Data #179): the candidate satisfied the full #171/#172 promotion gate under "
    "the #173/#174 pressureRateAllowed deferral (Option B) and the #175/#176 contract "
    "revision. governanceSource is explicit_marker set by that review; governed status "
    "holds only because provenanceStatus (governed_real_data) and the explicit marker "
    "agree. pressureRateAllowed remains null/deferred (unknown, never zero)."
)

DEFERRED_READINESS_STATUSES = frozenset({"deferred", "insufficient_data", "unavailable"})
# provenanceNotes lines asserting the pre-promotion non-governed posture; replaced
# by the governance marker note at promotion time.
_STALE_NOTE_MARKERS = ("provenanceStatus is partial_real_data", "No governance marker is set")


def verify_promotable(
    artifact: dict[str, Any], validation_report: dict[str, Any]
) -> list[str]:
    """Re-verify the governance-agnostic data gate. Empty list => promotable."""
    issues: list[str] = []

    for check in validation_report.get("checks", []):
        # non_governed_status is the pre-promotion governance check; governance is
        # decided by this review, not by that check.
        if check["name"] in ("non_governed_status", "governance_marker_consistent"):
            continue
        if not check["passed"]:
            issues.append(f"validation check failed: {check['name']}")

    metadata = artifact["metadata"]
    rows = artifact["rows"]

    if any(row.get("pressureRateAllowed") is not None for row in rows):
        issues.append("pressureRateAllowed is non-null on at least one row")

    deferred = set(metadata.get("deferredFields", []))
    for field, status in metadata.get("fieldReadiness", {}).items():
        if status in DEFERRED_READINESS_STATUSES:
            deferred.add(field)
    for index, row in enumerate(rows):
        for field in deferred:
            if isinstance(row.get(field), (int, float)):
                issues.append(
                    f"deferred field '{field}' has numeric value at row {index} "
                    "(deferred fields must be null, never zero-filled)"
                )

    for source in metadata.get("inputSources", []):
        checksum = source.get("checksum")
        if not (isinstance(checksum, dict) and checksum.get("algorithm") and checksum.get("value")):
            issues.append("an input source is missing a checksum")

    coverage = metadata["coverage"]
    if coverage["missingTeams"] or coverage["unexpectedTeams"]:
        issues.append("coverage is not full-league")
    if coverage["actualTeamGameRows"] != coverage["expectedTeamGameRows"]:
        issues.append("actual team-game row count does not match expected")

    return issues


def promote_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Return a governed copy of the artifact. Rows are untouched."""
    promoted = json.loads(json.dumps(artifact))
    metadata = promoted["metadata"]
    metadata["provenanceStatus"] = "governed_real_data"
    metadata["governance"] = {
        "governanceStatus": "governed",
        "governanceSource": "explicit_marker",
        "notes": GOVERNANCE_MARKER_NOTE,
        "reviewRefs": list(REVIEW_REFS),
    }
    notes = [
        note
        for note in metadata.get("provenanceNotes", [])
        if not any(marker in note for marker in _STALE_NOTE_MARKERS)
        and note != GOVERNANCE_MARKER_NOTE
    ]
    notes.append(GOVERNANCE_MARKER_NOTE)
    metadata["provenanceNotes"] = notes
    return promoted


def promote_validation_report(
    validation_report: dict[str, Any], promoted_artifact: dict[str, Any]
) -> dict[str, Any]:
    """Swap the pre-promotion non_governed_status check for a governed-consistency
    check and record the promotion. Data checks are preserved (rows unchanged)."""
    report = json.loads(json.dumps(validation_report))
    metadata = promoted_artifact["metadata"]
    governance = metadata["governance"]
    consistent = (
        metadata["provenanceStatus"] == "governed_real_data"
        and governance["governanceStatus"] == "governed"
        and governance["governanceSource"] == "explicit_marker"
    )
    checks = [
        check
        for check in report.get("checks", [])
        if check["name"] not in ("non_governed_status", "governance_marker_consistent")
    ]
    checks.append(
        {
            "name": "governance_marker_consistent",
            "passed": consistent,
            "details": {
                "provenanceStatus": metadata["provenanceStatus"],
                "governanceStatus": governance["governanceStatus"],
                "governanceSource": governance["governanceSource"],
            },
        }
    )
    report["checks"] = checks
    report["allPassed"] = all(check["passed"] for check in checks)
    report["promotion"] = {
        "decision": "governed_real_data",
        "reviewedAt": REVIEW_DATE,
        "reviewRefs": list(REVIEW_REFS),
        "authorizedBy": PROMOTION_AUTHORIZED_BY,
    }
    return report


def promote_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Record the governance decision on the lineage manifest. Sources/checksums
    and mutability notes are preserved."""
    promoted = json.loads(json.dumps(manifest))
    promoted["governanceStatus"] = "governed"
    promoted["governanceSource"] = "explicit_marker"
    promoted["promotion"] = {
        "decision": "governed_real_data",
        "reviewedAt": REVIEW_DATE,
        "reviewRefs": list(REVIEW_REFS),
        "authorizedBy": PROMOTION_AUTHORIZED_BY,
    }
    promoted["notes"] = [
        "This manifest documents source retrieval for the 2024 team_week_raw_v0 artifact.",
        "Promoted to governed_real_data by an explicit human promotion review "
        "(PR D, TIBER-Data #179); governanceSource is explicit_marker.",
        "Source URLs remain mutable nflverse rolling assets; the recorded sha256 "
        "checksums pin the exact bytes consumed so drift is detectable.",
    ]
    return promoted


def main() -> int:
    artifact = json.loads(CANDIDATE_ARTIFACT_PATH.read_text(encoding="utf-8"))
    validation_report = json.loads(CANDIDATE_VALIDATION_REPORT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(LINEAGE_MANIFEST_PATH.read_text(encoding="utf-8"))

    issues = verify_promotable(artifact, validation_report)
    if issues:
        print("ERROR: candidate is NOT promotable; refusing to set governance marker:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    promoted_artifact = promote_artifact(artifact)
    promoted_report = promote_validation_report(validation_report, promoted_artifact)
    promoted_manifest = promote_manifest(manifest)

    if not promoted_report["allPassed"]:
        print("ERROR: governed validation report did not pass; refusing to write.", file=sys.stderr)
        return 1

    CANDIDATE_ARTIFACT_PATH.write_text(
        f"{json.dumps(promoted_artifact, indent=2)}\n", encoding="utf-8"
    )
    CANDIDATE_VALIDATION_REPORT_PATH.write_text(
        f"{json.dumps(promoted_report, indent=2)}\n", encoding="utf-8"
    )
    LINEAGE_MANIFEST_PATH.write_text(
        f"{json.dumps(promoted_manifest, indent=2)}\n", encoding="utf-8"
    )

    print("Promoted 2024 team_week_raw_v0 candidate to governed_real_data.")
    print(f"  provenanceStatus: {promoted_artifact['metadata']['provenanceStatus']}")
    print(f"  governanceStatus: {promoted_artifact['metadata']['governance']['governanceStatus']}")
    print(f"  governanceSource: {promoted_artifact['metadata']['governance']['governanceSource']}")
    print(f"  reviewRefs: {promoted_artifact['metadata']['governance']['reviewRefs']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with a clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
