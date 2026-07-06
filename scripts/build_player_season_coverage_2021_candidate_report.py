"""Build the candidate-build report/manifest for the 2021 player_season_coverage_v0 extension.

TIBER-Data #200. This is a read-only, dependency-free report builder: it does NOT call
nflreadpy and does NOT build the candidate artifact. It reads the already-generated
candidate file written by scripts/build_player_season_coverage_2021_candidate.py,
runs the existing candidate validator/schema against it, reconciles row/position
counts against the #198 source-availability finding, and emits exactly one decision
from the enum required by #200.

Reproduce (after running the builder):
    python3 scripts/build_player_season_coverage_2021_candidate_report.py

Exit code is 0 whenever a report was written, regardless of which decision was
emitted (a blocking/inconclusive decision is a valid, successful report -- this
script only exits non-zero if it cannot write a report at all).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = REPO_ROOT / "data/processed/evidence/player_season_coverage_2021_candidate.source_backed.json"
SOURCE_AVAILABILITY_REPORT_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2021-source-availability.json"
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_player_season_coverage_v0.py"
REPORT_MD_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2021-candidate-build.md"
REPORT_JSON_PATH = REPO_ROOT / "docs/reports/player-season-coverage-v0-2021-candidate-build.json"
PROMOTED_DIR = REPO_ROOT / "exports/promoted"

ALLOWED_DECISIONS = (
    "may_open_player_season_coverage_2021_promotion_review_issue",
    "player_season_coverage_2021_candidate_build_failed_source_or_schema_check",
    "player_season_coverage_2021_candidate_build_requires_source_boundary_redesign",
    "player_season_coverage_2021_candidate_build_inconclusive_requires_followup",
)

INCLUDED_POSITIONS = ("QB", "RB", "WR", "TE")


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_player_season_coverage_v0", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_source_availability_counts() -> dict[str, int] | None:
    if not SOURCE_AVAILABILITY_REPORT_PATH.exists():
        return None
    payload = json.loads(SOURCE_AVAILABILITY_REPORT_PATH.read_text(encoding="utf-8"))
    return payload.get("availability", {}).get("row_counts_by_position_reg_level")


def build_report(
    candidate_payload: dict | None,
    candidate_sha256: str | None,
    validation_errors: list[str],
    source_availability_counts: dict[str, int] | None,
) -> dict:
    """Pure assembly: given an already-loaded (or absent) candidate payload plus
    validator results and the #198 comparison counts, returns the report payload
    and emits exactly one decision from ALLOWED_DECISIONS.
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    if candidate_payload is None:
        decision = "player_season_coverage_2021_candidate_build_inconclusive_requires_followup"
        basis = (
            f"Candidate artifact not found at {CANDIDATE_PATH.relative_to(REPO_ROOT).as_posix()}. "
            "The build script (scripts/build_player_season_coverage_2021_candidate.py) has not been "
            "run against real nflreadpy source data yet in this environment."
        )
        return {
            "report_id": "player_season_coverage_v0_2021_candidate_build",
            "status": "candidate_build_evidence_report_not_an_artifact",
            "tracking_issue": "TIBER-Data#200",
            "generated_at": generated_at,
            "candidate_path": CANDIDATE_PATH.relative_to(REPO_ROOT).as_posix(),
            "candidate_exists": False,
            "candidate_sha256": None,
            "validation_errors": [],
            "reconciliation": None,
            "decision": decision,
            "decision_basis": basis,
            "decisions_not_emitted_and_not_authorized": [d for d in ALLOWED_DECISIONS if d != decision]
            + [
                "promotion of any artifact",
                "Forecast mirror refresh",
                "Forecast controlled rerun",
                "player-history threshold acceptance",
                "leakage audit",
                "model wiring / seasonalPprModel.ts changes",
            ],
        }

    records = candidate_payload.get("records", [])
    total = len(records)
    row_counts_by_position: dict[str, int] = {p: 0 for p in INCLUDED_POSITIONS}
    coverage_status_counts: Counter = Counter()
    identity_confidence_counts: Counter = Counter()
    for r in records:
        pos = r.get("position")
        if pos in row_counts_by_position:
            row_counts_by_position[pos] += 1
        coverage_status_counts[r.get("coverage_status")] += 1
        identity_confidence_counts[r.get("identity_confidence")] += 1

    identity_verified = identity_confidence_counts.get("source_verified", 0)
    identity_join_rate = round(identity_verified / total, 4) if total else None

    reconciliation = None
    counts_match = None
    if source_availability_counts is not None:
        counts_match = row_counts_by_position == {
            p: source_availability_counts.get(p, 0) for p in INCLUDED_POSITIONS
        }
        reconciliation = {
            "source_availability_row_counts": {
                p: source_availability_counts.get(p, 0) for p in INCLUDED_POSITIONS
            },
            "candidate_row_counts": row_counts_by_position,
            "counts_match": counts_match,
        }

    if validation_errors:
        decision = "player_season_coverage_2021_candidate_build_failed_source_or_schema_check"
        basis = f"{len(validation_errors)} validator error(s); see validation_errors."
    elif reconciliation is not None and not counts_match:
        decision = "player_season_coverage_2021_candidate_build_requires_source_boundary_redesign"
        basis = (
            "Candidate row counts by position do not exactly reconcile with the #198 source-availability "
            "finding, with no filtering difference documented in this report; see reconciliation."
        )
    elif reconciliation is None:
        decision = "player_season_coverage_2021_candidate_build_inconclusive_requires_followup"
        basis = (
            f"Cannot reconcile against #198: {SOURCE_AVAILABILITY_REPORT_PATH.relative_to(REPO_ROOT).as_posix()} "
            "is missing or has no availability.row_counts_by_position_reg_level field."
        )
    else:
        decision = "may_open_player_season_coverage_2021_promotion_review_issue"
        basis = (
            "Candidate passed schema/business-rule validation and row counts reconcile exactly with the "
            "#198 source-availability finding for all four positions."
        )

    assert decision in ALLOWED_DECISIONS

    return {
        "report_id": "player_season_coverage_v0_2021_candidate_build",
        "status": "candidate_build_evidence_report_not_an_artifact",
        "tracking_issue": "TIBER-Data#200",
        "generated_at": generated_at,
        "candidate_path": CANDIDATE_PATH.relative_to(REPO_ROOT).as_posix(),
        "candidate_exists": True,
        "candidate_sha256": candidate_sha256,
        "candidate_artifact_id": candidate_payload.get("artifact_id"),
        "candidate_status_field": candidate_payload.get("status"),
        "seasons": candidate_payload.get("seasons"),
        "season_type_scope": candidate_payload.get("season_type_scope"),
        "included_positions": candidate_payload.get("included_positions"),
        "total_records": total,
        "row_counts_by_position": row_counts_by_position,
        "coverage_status_distribution": dict(coverage_status_counts),
        "identity_confidence_distribution": dict(identity_confidence_counts),
        "identity_join_rate": identity_join_rate,
        "validation_errors": validation_errors,
        "reconciliation": reconciliation,
        "no_promoted_path_written": not (
            (REPO_ROOT / CANDIDATE_PATH).resolve() == PROMOTED_DIR.resolve()
            or PROMOTED_DIR.resolve() in (REPO_ROOT / CANDIDATE_PATH).resolve().parents
        ),
        "decision": decision,
        "decision_basis": basis,
        "decisions_not_emitted_and_not_authorized": [d for d in ALLOWED_DECISIONS if d != decision]
        + [
            "promotion of any artifact",
            "Forecast mirror refresh",
            "Forecast controlled rerun",
            "player-history threshold acceptance",
            "leakage audit",
            "model wiring / seasonalPprModel.ts changes",
        ],
    }


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Candidate-Build Report: `player_season_coverage_v0` — 2021 Extension")
    lines.append("")
    lines.append(f"- **Generated at:** {report['generated_at']}")
    lines.append(f"- **Tracking issue:** {report['tracking_issue']}")
    lines.append(f"- **Status:** `{report['status']}`")
    lines.append(f"- **Candidate path:** `{report['candidate_path']}`")
    lines.append(
        "- **Scope:** this report is evidence only. It is not a promoted artifact and authorizes "
        "no Forecast behavior; the only positive outcome it can authorize is a follow-up "
        "promotion-review issue."
    )
    lines.append("")

    if not report["candidate_exists"]:
        lines.append("## Candidate artifact not found")
        lines.append("")
        lines.append(report["decision_basis"])
        lines.append("")
        lines.append("## Decision")
        lines.append("")
        lines.append("```text")
        lines.append(report["decision"])
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Candidate summary")
    lines.append("")
    lines.append(f"- sha256: `{report['candidate_sha256']}`")
    lines.append(f"- artifact_id: `{report['candidate_artifact_id']}`")
    lines.append(f"- status field: `{report['candidate_status_field']}`")
    lines.append(f"- seasons: {report['seasons']}")
    lines.append(f"- season_type_scope: {report['season_type_scope']}")
    lines.append(f"- included_positions: {report['included_positions']}")
    lines.append(f"- total records: {report['total_records']}")
    lines.append(f"- identity join rate: {report['identity_join_rate']}")
    lines.append("")
    lines.append("### Row counts by position")
    lines.append("")
    lines.append("| position | count |")
    lines.append("|---|---|")
    for pos, count in report["row_counts_by_position"].items():
        lines.append(f"| {pos} | {count} |")
    lines.append("")
    lines.append("### Coverage status distribution")
    lines.append("")
    for status, count in report["coverage_status_distribution"].items():
        lines.append(f"- `{status}`: {count}")
    lines.append("")

    if report["reconciliation"] is not None:
        lines.append("## Reconciliation against #198 source-availability finding")
        lines.append("")
        lines.append("| position | #198 source-availability count | candidate count | match |")
        lines.append("|---|---|---|---|")
        recon = report["reconciliation"]
        for pos in INCLUDED_POSITIONS:
            src_count = recon["source_availability_row_counts"].get(pos)
            cand_count = recon["candidate_row_counts"].get(pos)
            lines.append(f"| {pos} | {src_count} | {cand_count} | {'yes' if src_count == cand_count else 'NO'} |")
        lines.append("")
        lines.append(f"- Overall match: **{recon['counts_match']}**")
        lines.append("")
    else:
        lines.append("## Reconciliation against #198 source-availability finding")
        lines.append("")
        lines.append("Not available (see decision_basis).")
        lines.append("")

    lines.append("## Validation")
    lines.append("")
    if report["validation_errors"]:
        lines.append(f"FAILED: {len(report['validation_errors'])} error(s):")
        lines.append("")
        for err in report["validation_errors"][:200]:
            lines.append(f"- {err}")
    else:
        lines.append("PASSED: schema + business-rule validation (`scripts/validate_player_season_coverage_v0.py`).")
    lines.append("")
    lines.append(f"- No promoted path written: **{report['no_promoted_path_written']}**")
    lines.append("")

    lines.append("## Decision")
    lines.append("")
    lines.append("```text")
    lines.append(report["decision"])
    lines.append("```")
    lines.append("")
    lines.append(f"- Basis: {report['decision_basis']}")
    lines.append("")
    lines.append("### Explicitly NOT emitted / NOT authorized by this report")
    lines.append("")
    for item in report["decisions_not_emitted_and_not_authorized"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(
        "This report is evidence under `docs/reports/`. It does not modify or promote any artifact "
        "and does not authorize Forecast behavior; a follow-up TIBER-Data promotion-review issue must "
        "explicitly authorize promotion."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    validator_module = _load_validator_module()
    source_availability_counts = _load_source_availability_counts()

    candidate_payload = None
    candidate_sha256 = None
    validation_errors: list[str] = []

    if CANDIDATE_PATH.exists():
        raw_bytes = CANDIDATE_PATH.read_bytes()
        candidate_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        candidate_payload = json.loads(raw_bytes.decode("utf-8"))
        validation_errors = validator_module.validate_payload(candidate_payload)

    report = build_report(candidate_payload, candidate_sha256, validation_errors, source_availability_counts)

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(f"{json.dumps(report, indent=2, allow_nan=False)}\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote {REPORT_JSON_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Wrote {REPORT_MD_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Decision: {report['decision']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed with clear reason
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
