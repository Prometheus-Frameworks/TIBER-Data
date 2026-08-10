"""Fail-closed validation helpers for the TIBER-Data #231 D0 pilot.

This module validates contracts, hash-pinned observation metadata, source
allowlisting, freshness advancement, and deterministic diffs. It deliberately
does not fetch, mirror, parse, transcribe, promote, or publish team content.
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_SCHEMA = ROOT / "schemas/team_published_depth_chart_snapshot_v0.schema.json"
REGISTRY_SCHEMA = ROOT / "schemas/team_published_depth_chart_source_registry_v0.schema.json"
REGISTRY = ROOT / "data/candidate/depth_charts/official_source_registry_v0.json"
RECEIPTS = ROOT / "data/candidate/depth_charts/source_observation_receipts_2026-08-10.json"
AUDIT = ROOT / "docs/audits/official-depth-chart-pilot-readiness-2026-08-10.json"

OFFICIAL_HOSTS = frozenset(
    {
        "49ers.com",
        "azcardinals.com",
        "atlantafalcons.com",
        "baltimoreravens.com",
        "bengals.com",
        "buffalobills.com",
        "buccaneers.com",
        "chargers.com",
        "chicagobears.com",
        "chiefs.com",
        "clevelandbrowns.com",
        "colts.com",
        "commanders.com",
        "dallascowboys.com",
        "denverbroncos.com",
        "detroitlions.com",
        "giants.com",
        "houstontexans.com",
        "jaguars.com",
        "miamidolphins.com",
        "neworleanssaints.com",
        "newyorkjets.com",
        "packers.com",
        "panthers.com",
        "patriots.com",
        "philadelphiaeagles.com",
        "raiders.com",
        "seahawks.com",
        "static.clubs.nfl.com",
        "steelers.com",
        "tennesseetitans.com",
        "therams.com",
        "vikings.com",
    }
)
CANONICAL_TEAM_ORDER = (
    "ARI",
    "ATL",
    "BAL",
    "BUF",
    "CAR",
    "CHI",
    "CIN",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GB",
    "HOU",
    "IND",
    "JAX",
    "KC",
    "LAC",
    "LAR",
    "LV",
    "MIA",
    "MIN",
    "NE",
    "NO",
    "NYG",
    "NYJ",
    "PHI",
    "PIT",
    "SF",
    "SEA",
    "TB",
    "TEN",
    "WAS",
)


class PilotValidationError(RuntimeError):
    """Raised when a pilot invariant fails closed."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(payload: Any) -> bytes:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def canonical_sha256(payload: Any) -> str:
    return sha256(canonical_json_bytes(payload)).hexdigest()


def schema_validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(load_json(path), format_checker=FormatChecker())


def normalized_hostname(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise PilotValidationError(f"Official source URL must use https: {url}")
    host = parsed.hostname.lower()
    return host.removeprefix("www.")


def official_source_allowed(url: str) -> bool:
    try:
        return normalized_hostname(url) in OFFICIAL_HOSTS
    except PilotValidationError:
        return False


def validate_registry(payload: dict[str, Any]) -> None:
    schema_validator(REGISTRY_SCHEMA).validate(payload)
    teams = payload["teams"]
    ids = [team["team_id"] for team in teams]
    if len(ids) != 32 or len(set(ids)) != 32:
        raise PilotValidationError("Registry must contain exactly 32 unique team IDs")
    if tuple(ids) != CANONICAL_TEAM_ORDER:
        raise PilotValidationError(
            "Registry team rows drifted from the canonical deterministic order"
        )

    for team in teams:
        if team["team_id"] != team["team_abbr"]:
            raise PilotValidationError(f"Team ID/abbreviation drift: {team['team_id']}")
        for key in ("official_team_home_url", "official_depth_chart_page_candidate"):
            url = team[key]
            if url is not None and not official_source_allowed(url):
                raise PilotValidationError(f"Non-official source in registry: {url}")
        if team["coverage_state"] == "not_yet_published" and team["last_checked_at"] is None:
            raise PilotValidationError("not_yet_published requires an observation clock")
        if team["latest_verified_snapshot_id"] is not None:
            required = (
                team["last_qualifying_effective_date"],
                team["latest_verified_snapshot_sha256"],
            )
            if any(value is None for value in required):
                raise PilotValidationError(
                    "Verified latest requires an effective date and content hash"
                )


def validate_receipts(payload: dict[str, Any]) -> None:
    receipts = payload.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        raise PilotValidationError("Observation ledger must contain receipts")
    seen: set[str] = set()
    for receipt in receipts:
        receipt_id = receipt["receipt_id"]
        if receipt_id in seen:
            raise PilotValidationError(f"Duplicate receipt ID: {receipt_id}")
        seen.add(receipt_id)
        if not official_source_allowed(receipt["source_url"]):
            raise PilotValidationError(f"Non-official receipt URL: {receipt['source_url']}")
        if receipt["external_source_classification"] != "external_candidate":
            raise PilotValidationError(f"Unexpected source classification: {receipt_id}")
        invalid_sha = len(receipt["sha256"]) != 64 or any(
            char not in "0123456789abcdef" for char in receipt["sha256"]
        )
        if invalid_sha:
            raise PilotValidationError(f"Malformed source SHA-256: {receipt_id}")
        if not receipt["refetch_byte_identical"] or receipt["sha256"] != receipt["refetch_sha256"]:
            raise PilotValidationError(f"Refetch drifted: {receipt_id}")
        if receipt["byte_length"] <= 0:
            raise PilotValidationError(f"Empty source receipt: {receipt_id}")
        if receipt["archive_status"] == "blocked_rights_unresolved":
            if receipt["repository_receipt_path"] is not None:
                raise PilotValidationError(f"Rights-blocked receipt was mirrored: {receipt_id}")
            if receipt["license_observed"] is not None:
                raise PilotValidationError(
                    f"Rights blocker conflicts with a declared license: {receipt_id}"
                )


def validate_snapshot(payload: dict[str, Any]) -> None:
    schema_validator(SNAPSHOT_SCHEMA).validate(payload)
    receipt_ids = [receipt["receipt_id"] for receipt in payload["source_receipts"]]
    if len(receipt_ids) != len(set(receipt_ids)):
        raise PilotValidationError("Snapshot receipt IDs must be unique")
    row_ids = [row["row_instance_id"] for row in payload["rows"]]
    if len(row_ids) != len(set(row_ids)):
        raise PilotValidationError("Snapshot row IDs must be unique")
    if payload["transcription"]["normalized_row_count"] != len(payload["rows"]):
        raise PilotValidationError("Normalized row count does not match rows")
    entry_count = sum(len(row["entries"]) for row in payload["rows"])
    if payload["transcription"]["normalized_entry_count"] != entry_count:
        raise PilotValidationError("Normalized entry count does not match entries")
    for row in payload["rows"]:
        for entry in row["entries"]:
            if entry["identity_status"].startswith("unresolved") and entry["player_id"] is not None:
                raise PilotValidationError("Unresolved identity must retain player_id=null")
            if entry["identity_status"] == "resolved_exact" and not entry["player_id"]:
                raise PilotValidationError("Resolved identity requires a canonical player ID")


def snapshot_evidence_date(snapshot: dict[str, Any]) -> str | None:
    if snapshot.get("chart_as_of"):
        return snapshot["chart_as_of"]
    if snapshot.get("published_at"):
        return snapshot["published_at"][:10]
    return None


def candidate_can_advance(snapshot: dict[str, Any]) -> bool:
    if snapshot.get("normalization_status") != "complete":
        return False
    if snapshot.get("verification_status") != "candidate_structurally_validated":
        return False
    if snapshot_evidence_date(snapshot) is None:
        return False
    receipts = snapshot.get("source_receipts", [])
    return bool(receipts) and all(
        receipt.get("archive_status") == "stored_immutable" for receipt in receipts
    )


def advance_latest(
    prior_verified: dict[str, Any] | None,
    changed_candidate: dict[str, Any],
) -> dict[str, Any] | None:
    """Advance only on a newer, complete, rights-cleared, structurally validated candidate."""
    if not candidate_can_advance(changed_candidate):
        return deepcopy(prior_verified)
    if prior_verified is None:
        return deepcopy(changed_candidate)
    prior_date = snapshot_evidence_date(prior_verified)
    candidate_date = snapshot_evidence_date(changed_candidate)
    if prior_date is None or candidate_date is None or candidate_date <= prior_date:
        return deepcopy(prior_verified)
    return deepcopy(changed_candidate)


def _entry_index(snapshot: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    index: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in snapshot.get("rows", []):
        for entry in row.get("entries", []):
            key = (
                row["unit"],
                row["row_instance_id"],
                entry["display_column"],
                entry["display_order_within_column"],
                entry["raw_source_text"],
            )
            if key in index:
                raise PilotValidationError(f"Duplicate semantic entry key: {key}")
            index[key] = {"row": row["source_position_label_raw"], "entry": deepcopy(entry)}
    return index


def deterministic_snapshot_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    left = _entry_index(before)
    right = _entry_index(after)
    left_keys = set(left)
    right_keys = set(right)
    added = [{"key": list(key), "after": right[key]} for key in sorted(right_keys - left_keys)]
    removed = [{"key": list(key), "before": left[key]} for key in sorted(left_keys - right_keys)]
    changed = [
        {"key": list(key), "before": left[key], "after": right[key]}
        for key in sorted(left_keys & right_keys)
        if canonical_sha256(left[key]) != canonical_sha256(right[key])
    ]
    return {"added": added, "removed": removed, "changed": changed}


def validate_pilot_files() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    receipts = load_json(RECEIPTS)
    audit = load_json(AUDIT)
    validate_registry(registry)
    validate_receipts(receipts)

    if audit["source_registry_path"] != str(REGISTRY.relative_to(ROOT)):
        raise PilotValidationError("Audit/registry path drift")
    if audit["source_observation_receipts_path"] != str(RECEIPTS.relative_to(ROOT)):
        raise PilotValidationError("Audit/receipt path drift")
    if any(result["normalization_output_committed"] for result in audit["format_probe_results"]):
        raise PilotValidationError(
            "Audit claims a normalized candidate despite the receipt blocker"
        )
    decision = audit.get("terminal_decision")
    if not isinstance(decision, str) or not decision.startswith("official_depth_chart_pilot_"):
        raise PilotValidationError("Missing or malformed terminal decision")

    return {
        "registry_team_count": len(registry["teams"]),
        "observation_receipt_count": len(receipts["receipts"]),
        "format_probe_count": len(audit["format_probe_results"]),
        "normalized_candidate_count": 0,
        "terminal_decision": decision,
    }


def main() -> int:
    print(json.dumps(validate_pilot_files(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
