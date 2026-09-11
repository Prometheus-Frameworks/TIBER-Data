"""Materialize the accepted four-row V2 extension from immutable reviewed bytes.

Offline only. No FORGE cohort expansion, provider fetch or name join.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_COMMIT = "e08e5cb8f8c3c71441e62755fb87c9514ce1b249"
PROPOSAL_PATH = "docs/audits/draft-review-evidence-admission-2026-09-07.json"
RECEIPT_PATH = "exports/promoted/draft_review/evidence_admission_v1.json"
OUTPUT_PATH = "exports/promoted/identity_crosswalk/tiber_identity_crosswalk_v2.json"
ACCEPTANCE = "https://github.com/Prometheus-Frameworks/TIBER-Data/pull/264#issuecomment-5574349251"


def historical(path):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{PROPOSAL_COMMIT}:{path}"])


def build(receipt=None):
    rb = (ROOT / RECEIPT_PATH).read_bytes() if receipt is None else json.dumps(receipt, indent=2).encode() + b"\n"
    receipt = json.loads(rb)
    fixed = {
        "schema_version": "draft_review_evidence_admission_v1",
        "scope": "bounded_historical_descriptive_consumer",
        "proposal_path": PROPOSAL_PATH,
        "review": "https://github.com/Prometheus-Frameworks/TIBER-Data/pull/264#issuecomment-5570922674",
    }
    allowed = set(fixed) | {"status", "proposal_commit", "proposal_sha256", "operator_acceptance",
                            "identity_records", "consumer_scope", "sources", "merge_authorized",
                            "production_deployment_authorized", "artifact_generated_at"}
    if (set(receipt) != allowed or any(receipt.get(k) != v for k, v in fixed.items())
            or receipt.get("merge_authorized") is not False
            or receipt.get("production_deployment_authorized") is not False):
        raise ValueError("Invalid or contradictory admission authority envelope")
    pb = historical(PROPOSAL_PATH)
    p = json.loads(pb)
    if (receipt.get("status") != "accepted" or receipt.get("operator_acceptance") != ACCEPTANCE
            or receipt.get("proposal_commit") != PROPOSAL_COMMIT
            or receipt.get("proposal_sha256") != hashlib.sha256(pb).hexdigest()
            or receipt.get("identity_records") != p["identity"]["proposed_records"]
            or receipt.get("sources") != p["sources"]):
        raise ValueError("Admission does not match the accepted reviewed proposal")
    expected_scope = dict(p["proposed_consumer_scope"])
    expected_scope["public_rights_receipt"] = "Accepted scoped terms/attribution assessment in reviewed proposal and operator acceptance; no blanket provider admission."
    if receipt.get("consumer_scope") != expected_scope:
        raise ValueError("Historical consumer scope changed")
    for source in p["sources"]:
        if hashlib.sha256(historical(source["path"])).hexdigest() != source["sha256"]:
            raise ValueError("Historical source hash mismatch")
    base = json.loads(historical(OUTPUT_PATH))
    old_records = list(base["records"])
    base["records"] += receipt["identity_records"]
    keys = [r["provider_canonical_id"] for r in base["records"]]
    ids = [r["tiber_player_id"] for r in base["records"]]
    if len(keys) != 72 or len(set(keys)) != 72 or len(set(ids)) != 72:
        raise ValueError("Unexpected identity scope/collision")
    base["record_count"] = 72
    base["record_count_by_match_method"]["name_exact"] += 4
    # Artifact construction clock; old source row clocks remain byte-for-byte.
    datetime.strptime(receipt["artifact_generated_at"], "%Y-%m-%dT%H:%M:%SZ")
    base["generated_at"] = receipt["artifact_generated_at"]
    base["coverage_notes"]["slice"] += " Plus four operator-accepted Draft Review identities; see admission receipt."
    base["source_artifacts"].append({"artifact": "DRAFT_REVIEW_EVIDENCE_ADMISSION_V1", "path": RECEIPT_PATH,
                                     "sha256": hashlib.sha256(rb).hexdigest()})
    assert base["records"][:68] == old_records
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if (ROOT / "exports/promoted/draft_review/team_identity_admission_v1.json").exists():
        raise ValueError("The three-row Team extension is prepared; use materialize_team_identity_admission.py. This legacy command would discard accepted rows.")
    output = json.dumps(build(), indent=1) + "\n"
    path = ROOT / OUTPUT_PATH
    if args.check:
        if path.read_text() != output:
            raise ValueError("Committed admitted crosswalk differs from deterministic replay")
        print("Accepted 72-row crosswalk replay matches; original 68 rows preserved.")
    else:
        path.write_text(output)


if __name__ == "__main__":
    main()
